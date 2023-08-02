class_name Prompt extends PanelContainer


signal changed()


func construct_prompt() -> String:
	assert(false, "Subclasses of prompt should override construct_prompt(), and return the complete prompt they represents.")
	return "NOT IMPLEMENTED"

func get_image() -> Image:
	assert(false, "Subclasses of prompt should override construct_prompt(), and return the its image.")
	return null
