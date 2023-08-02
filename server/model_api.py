import enum

import torch
from lavis.models import load_model_and_preprocess

import config


class Model:
    def __init__(self, main, vis_proc, txt_proc):
        self.main = main
        self.vis_proc = vis_proc
        self.txt_proc = txt_proc

    def generate(
            self,
            prompt: str,
            image: torch.Tensor,
            use_nucleus_sampling=False,
            num_beams=5,
            max_length=30,
            min_length=1,
            top_p=0.9,
            repetition_penalty=1.0,
            length_penalty=1.0,
            num_captions=1,
            temperature=1,
    ):
        """
        Args:
            prompt (str): The prompt text
            image (torch.Tensor): A tensor of shape (batch_size, 3, H, W)
            use_nucleus_sampling (bool): Whether to use nucleus sampling. If False, use top-k sampling.
            num_beams (int): Number of beams for beam search. 1 means no beam search.
            max_length (int): The maximum length of the sequence to be generated.
            min_length (int): The minimum length of the sequence to be generated.
            top_p (float): The cumulative probability for nucleus sampling.
            repetition_penalty (float): The parameter for repetition penalty. 1.0 means no penalty.
            num_captions (int): Number of captions to be generated for each image.
        Returns:
            captions (list): A list of strings of length batch_size * num_captions.
        """
        with self.main.maybe_autocast(), torch.no_grad():
            image_embeds = self.main.ln_vision(self.main.visual_encoder(image))
            image_atts = torch.ones(image_embeds.size()[:-1], dtype=torch.long).to(
                image.device
            )

            query_tokens = self.main.query_tokens.expand(image_embeds.shape[0], -1, -1)
            query_output = self.main.Qformer.bert(
                query_embeds=query_tokens,
                encoder_hidden_states=image_embeds,
                encoder_attention_mask=image_atts,
                return_dict=True,
            )

            inputs_opt = self.main.opt_proj(query_output.last_hidden_state)
            atts_opt = torch.ones(inputs_opt.size()[:-1], dtype=torch.long).to(
                image.device
            )

            opt_tokens = self.main.opt_tokenizer(
                [prompt] * image.size(0),
                return_tensors="pt",
                padding="longest",
                truncation=True,
                max_length=self.main.max_txt_len,
            ).to(image.device)
            attention_mask = torch.cat([atts_opt, opt_tokens.attention_mask], dim=1)

            # new version for transformers>=4.27
            inputs_embeds = self.main.opt_model.get_input_embeddings()(opt_tokens.input_ids)
            inputs_embeds = torch.cat([inputs_opt, inputs_embeds], dim=1)

            yield "opt_model.generate"
            outputs = self.main.opt_model.generate(
                inputs_embeds=inputs_embeds,
                attention_mask=attention_mask,
                do_sample=use_nucleus_sampling,
                top_p=top_p,
                temperature=temperature,
                num_beams=num_beams,
                max_length=max_length,
                min_length=min_length,
                eos_token_id=self.main.eos_token_id,
                repetition_penalty=repetition_penalty,
                length_penalty=length_penalty,
                num_return_sequences=num_captions,
            )

            yield "opt_tokenizer.batch_decode"
            output_text = self.main.opt_tokenizer.batch_decode(
                outputs, skip_special_tokens=True
            )

            output_text = [text.strip() for text in output_text]
            return output_text


def load_model(device) -> Model:
    model, _vis_processors, _txt_processors = load_model_and_preprocess(
        name=config.MODEL_NAME,
        model_type=config.MODEL_TYPE,
        is_eval=True,
        device=device
    )
    vis_processor = _vis_processors["eval"]
    txt_processor = _txt_processors["eval"]
    return Model(model, vis_processor, txt_processor)
