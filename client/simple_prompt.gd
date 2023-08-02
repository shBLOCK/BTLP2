extends Prompt


func _on_text_changed():
	changed.emit()

func construct_prompt() -> String:
	return %TextEdit.text
