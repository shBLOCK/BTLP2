extends Prompt


func serialize() -> Dictionary:
	var data := super.serialize()
	data["text"] = %TextEdit.text
	return data

func deserialize(data: Dictionary):
	super.deserialize(data)
	%TextEdit.text = data["text"]

func _on_text_changed():
	changed.emit()

func construct_prompt() -> String:
	var text: String = %TextEdit.text
	if text == "":
		return ""
	return "if you can't answer, just say sorry.Question: " + text + " Answer: "

func _editable_changed() -> void:
	%TextEdit.editable = editable
