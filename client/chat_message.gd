extends PanelContainer


func setup(prompt: Prompt, image: Image):
	var my_prompt := prompt.duplicate()
	my_prompt.deserialize(prompt.serialize())
	my_prompt.size_flags_horizontal = SIZE_EXPAND_FILL
	my_prompt.size_flags_stretch_ratio = 1.0
	%PromptContainer.add_child(my_prompt)
	%Image.texture = ImageTexture.create_from_image(image)
	%PromptContainer.custom_minimum_size.y = prompt.size.y
	%PromptContainer.queue_sort()

func set_progress(progress: String, bar: float):
	var fill: StyleBoxFlat = %ProgressBar.get_theme_stylebox("fill")
	fill.bg_color = Color.LIME_GREEN
	%ProgressBar.add_theme_stylebox_override("fill", fill)
	%ProgressBar.value = bar
	%ProgressLabel.text = progress
	%PromptContainer.queue_sort()

func set_result(result: PackedStringArray):
	%Progress.hide()
	if not result.is_empty():
		%Response.text = "\n".join(result)
	else:
		%Response.text = "NO_RESPONSE"
	%PromptContainer.queue_sort()

func set_fail(reason: String):
	%ProgressBar.value = 1.0
	var fill: StyleBoxFlat = %ProgressBar.get_theme_stylebox("fill")
	fill.bg_color = Color.INDIAN_RED
	%ProgressBar.add_theme_stylebox_override("fill", fill)
	%ProgressLabel.text = reason
	%PromptContainer.queue_sort()
