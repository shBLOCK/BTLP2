class_name Prompt extends PanelContainer


signal changed()

@export var editable := false:
	set(value):
		editable = value
		if is_node_ready():
			_editable_changed()


func serialize() -> Dictionary:
	return {}

func deserialize(data: Dictionary):
	pass

func construct_prompt() -> String:
	assert(false, "Subclasses of prompt should override construct_prompt(), and return the complete prompt they represents.")
	return "NOT IMPLEMENTED"

func get_image() -> Image:
	assert(false, "Subclasses of prompt should override construct_prompt(), and return the its image.")
	return null

func _editable_changed() -> void:
	pass
