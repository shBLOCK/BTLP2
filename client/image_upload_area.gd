extends TextureButton


const MAX_IMAGE_SIZE = 128

var _image: Image
var image: Image:
	get:
		return _image

var _image_size: Vector2i
var image_size: Vector2i:
	get:
		return _image_size


const _IMAGE_LOADERS := {
	"jpeg": "load_jpg_from_buffer",
	"jpg": "load_jpg_from_buffer",
	"png": "load_png_from_buffer",
	"tga": "load_tga_from_buffer",
	"webp": "load_webp_from_buffer",
}

func _load_image_data(raw_data: String) -> void:
	if not raw_data.begins_with("data:image"):
		printerr("Raw data invalid")
		return
	raw_data = raw_data.substr(11)
	var type_other := raw_data.split(";")
	var type := type_other[0]
	var loader_method: String = _IMAGE_LOADERS.get(type, "")
	if loader_method == "":
		printerr("Unsupported format: " + type)
		return
	var data_b64 := type_other[1].substr(7)
	var data := Marshalls.base64_to_raw(data_b64)
	
	var image := Image.new()
	var err: Error = image.call(loader_method, data)
	if err != OK:
		printerr("Failed to load image: " + error_string(err))
		return
	image.convert(Image.FORMAT_RGBA8)
	
	var img_size := image.get_size()
	if img_size.x > MAX_IMAGE_SIZE:
		img_size.y = int(img_size.y * (float(MAX_IMAGE_SIZE) / img_size.x))
		img_size.x = MAX_IMAGE_SIZE
	if img_size.y > MAX_IMAGE_SIZE:
		img_size.x = int(img_size.x * (float(MAX_IMAGE_SIZE) / img_size.y))
		image_size.y = MAX_IMAGE_SIZE
	print(img_size)
	image.resize(img_size.x, img_size.y, Image.INTERPOLATE_BILINEAR)
	
	self.texture_normal = ImageTexture.create_from_image(image)
	self._image = image
	self._image_size = image.get_size()

func _ready():
	JavaScriptBridge.eval("""
		img_selector = document.createElement("input");
		img_selector.type = "file";
		img_selector.id = "image_uploads";
		img_selector.className = "inputFile";
		img_selector.accept = "image/png,image/jpeg,image/bmp";
		img_selector.style.width = "1%";
		img_selector.style.height = "1%";
		img_selector.style.position = "absolute";
		img_selector.style.opacity = 0;
		img_selector.addEventListener("change", read_selected_image);
		
		selected_img_data = undefined;
		
		function read_selected_image() {
			let files = img_selector.files;
			if (files.length > 0) {
				const reader = new FileReader();
				reader.addEventListener('load', (event) => {
					selected_img_data = event.target.result;
				});
				reader.readAsDataURL(files[0]);
			} else {
				alert("Didn't select anything?");
			}
		}
		
		function get_selected_image_data() {
			return selected_img_data;
		}
	""", true)
	set_process(false)

func _on_pressed():
	JavaScriptBridge.eval("""
		selected_img_data = undefined;
		img_selector.click();
	""", true)
	set_process(true)

func _process(_delta):
	var data = JavaScriptBridge.eval("get_selected_image_data();", true)
	if data != null:
		_load_image_data(data)
		set_process(false)
