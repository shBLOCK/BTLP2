extends HBoxContainer


signal submit(prompt: String, image: PackedByteArray, image_size: Vector2i, args: Dictionary)


func _on_button_pressed():
	if %ImageUploadArea.image == null:
		Utils.push_notification(Notification.ERROR, "You must select a image!")
		return
	
	submit.emit(
		%Prompts.get_current_tab_control(),
		%ImageUploadArea.image,
		%ImageUploadArea.image_size,
		{
			"temperature": 1.5,
			"top_p": 0.95,
			"min_length":10,
			#"max_length": 100
		}
	)
