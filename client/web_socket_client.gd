class_name WebSocketClient extends Node


signal on_server_packet(event: String, data: Dictionary)
signal data_sent()

var send_buffer_size: int:
	get:
		return _conn.get_current_outbound_buffered_amount()

@onready var _conn := WebSocketPeer.new()


func get_websocket_server_address() -> String:
	return "ws://frp-fly.top:59657"

func send(event: String, data: Dictionary):
	var text_data := JSON.stringify({
		"event": event,
		"data": data
	})
	var err := _conn.send_text(text_data)
	if err != OK:
		Utils.push_notification(Notification.ERROR, "Failed to send packet: " + error_string(err))
	data_sent.emit()

func _ready():
	_conn.outbound_buffer_size = 1024*1024*10
	
	var err := _conn.connect_to_url(get_websocket_server_address())
	if err != OK:
		Utils.push_notification(Notification.ERROR, "Failed to connect to server: " + error_string(err))

var _last_state := WebSocketPeer.STATE_CLOSED

func _process(_delta):
	var state := _conn.get_ready_state()
	if state == WebSocketPeer.STATE_OPEN:
		if _last_state != WebSocketPeer.STATE_OPEN:
			Utils.push_notification(Notification.SUCCESS, "Connected to server!")
		
		_conn.poll()
		for i in range(_conn.get_available_packet_count()):
			var raw_data := _conn.get_packet().get_string_from_utf8()
			var pkt = JSON.parse_string(raw_data)
			if pkt == null or not pkt is Dictionary:
				Utils.push_notification(Notification.ERROR, "Failed to parse packet")
				printerr("Failed to parse server packet: " + raw_data)
				continue
			pkt = pkt as Dictionary
			
			var event = pkt.get("event", null)
			var data = pkt.get("data", {})
			if (not event is String) or (not data is Dictionary):
				Utils.push_notification(Notification.ERROR, "Invalid packet")
				printerr("Invalid server packet: " + raw_data)
			
			on_server_packet.emit(event, data)
	
	_last_state = state
