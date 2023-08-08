extends PanelContainer


var _PROGRESS_BAR_MAP = {}

const ChatMessage_Scene := preload("res://chat_message.tscn")
@onready var WSClient: WebSocketClient = $WebSocketClient

var _submission_id := 0
var _id_msg_map := {}
var _queue_pos_map := {}
var _queue_len := -1


func _ready():
	for i in range(12):
		_PROGRESS_BAR_MAP[str(i)] = float(i) / 11.0

func _on_server_packet(event: String, data: Dictionary):
	print(event, data)
	match event:
		"progress":
			var progress = data["progress"]
			_set_progress(data["id"], progress, _PROGRESS_BAR_MAP.get(progress, 0))
		"result":
			_id_msg_map[int(data["id"])].set_result(data["result"])
		"queue_len":
			_queue_len = data["len"]
			_update_queue_info()
		"queue_pos":
			var id = data["id"]
			_queue_pos_map[id] = data["pos"]
			_update_queue_info(id)
		"submit_fail":
			Utils.push_notification(Notification.ERROR, "Submission failed!")
			var id = data.get("id")
			if id is int and _id_msg_map.has(id):
				_id_msg_map[id].set_fail(data.get("cause", "Unknown error"))
		_:
			Utils.push_notification(Notification.ERROR, "Unknown event type: " + event)
			printerr("Unknown event type: " + event)

func _on_send_panel_submit(prompt: Prompt, image: Image, image_size: Vector2i, args: Dictionary):
	WSClient.send("submit", {
		"id": self._submission_id,
		"prompt": prompt.construct_prompt(),
		"image": Marshalls.raw_to_base64(image.get_data()),
		"image_width": image_size.x,
		"image_height": image_size.y,
		"args": args
	})
	
	var msg := ChatMessage_Scene.instantiate()
	msg.setup(prompt, image)
	%ChatMessageContainer.add_child(msg)
	msg.set_progress("WAITING_FOR_SERVER_RESPONSE", 0.0)
	self._id_msg_map[self._submission_id] = msg
	self._queue_pos_map[self._submission_id] = _queue_len
	
	self._submission_id += 1

func _set_progress(id: int, progress: String, bar: float):
	_id_msg_map[id].set_progress(progress, bar)

func _update_queue_info(msg_id: int = -1):
	for id in [msg_id] if msg_id >= 0 else _id_msg_map:
		var this_pos = _queue_pos_map.get(id, _queue_len - 1)
		_set_progress(id, "Queue: %d/%d" % [this_pos + 1, _queue_len], float(this_pos) / (_queue_len - 1))

func _on_data_sent():
	var buf_size := WSClient.send_buffer_size
	if buf_size == 0:
		return
	else:
		%NetworkProgressBar.show()
		%NetworkProgressBar.max_value = buf_size
		%NetworkProgressBar.value = 0

func _process(_delta):
	var buf_size := WSClient.send_buffer_size
	if buf_size == 0:
		%NetworkProgressBar.hide()
		return
	%NetworkProgressBar.value = %NetworkProgressBar.max_value - buf_size
