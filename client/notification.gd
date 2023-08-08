class_name Notification extends PanelContainer


@export var _BASE_STYLE_BOX: StyleBoxFlat
var _panel: StyleBoxFlat

enum {
	SUCCESS,
	INFO,
	ERROR
}

var type:int = INFO:
	set(value):
		type = value
		self._update_style()

var message: String:
	set(value):
		message = value
		$Label.text = value


func _ready():
	$Label.text = message
	self._update_style()
	$AnimationPlayer.play("fade")

const _BG_COLOR_MAP := {
	SUCCESS: Color.LIME_GREEN,
	INFO: Color.SLATE_GRAY,
	ERROR: Color.INDIAN_RED,
}

func _update_style():
	if self.has_theme_stylebox_override("panel"):
		self.remove_theme_stylebox_override("panel")
	
	self._panel = self._BASE_STYLE_BOX
	self._panel.bg_color = _BG_COLOR_MAP[self.type]
	
	self.add_theme_stylebox_override("panel", self._panel)
