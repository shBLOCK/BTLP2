extends Node


@onready var _notifications_node = get_node("/root/Main/Notifications")


func push_notification(type: int, msg: String):
	var noti: Notification = preload("res://notification.tscn").instantiate()
	noti.type = type
	noti.message = msg
	_notifications_node.add_child(noti)
