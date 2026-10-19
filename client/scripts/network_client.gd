class_name NetworkClient
extends RefCounted

signal connected
signal disconnected
signal message_received(message: Dictionary)
signal connection_error(message: String)

const HOST := "127.0.0.1"
const PORT := 24500
const PROTOCOL_VERSION := 1

var peer := StreamPeerTCP.new()
var _buffer := ""
var _was_connected := false
var session_token := ""
var reconnect_timer := 0.0
var reconnect_delay := 1.0

func connect_to_server() -> void:
	var result := peer.connect_to_host(HOST, PORT)
	if result != OK:
		connection_error.emit("No se pudo iniciar la conexión")
		reconnect_timer = reconnect_delay

func poll(delta: float = 0.0) -> void:
	peer.poll()
	var status := peer.get_status()
	if status == StreamPeerTCP.STATUS_CONNECTED:
		if not _was_connected:
			_was_connected = true
			connected.emit()
		_read_messages()
	elif _was_connected and status in [StreamPeerTCP.STATUS_ERROR, StreamPeerTCP.STATUS_NONE]:
		_was_connected = false
		disconnected.emit()
		reconnect_timer = reconnect_delay
		reconnect_delay = minf(reconnect_delay * 2.0, 15.0)
	elif status == StreamPeerTCP.STATUS_NONE and reconnect_timer > 0.0:
		reconnect_timer -= delta
		if reconnect_timer <= 0.0:
			peer = StreamPeerTCP.new()
			connect_to_server()
	else:
		reconnect_delay = 1.0

func send_message(message: Dictionary) -> bool:
	if peer.get_status() != StreamPeerTCP.STATUS_CONNECTED:
		return false
	var outgoing := message.duplicate()
	outgoing["protocol_version"] = PROTOCOL_VERSION
	if not session_token.is_empty() and outgoing.get("type", "") != "login_request":
		outgoing["session_token"] = session_token
	var line := JSON.stringify(outgoing) + "\n"
	return peer.put_data(line.to_utf8_buffer()) == OK

func _read_messages() -> void:
	while peer.get_available_bytes() > 0:
		var result := peer.get_data(peer.get_available_bytes())
		if result[0] != OK:
			return
		_buffer += result[1].get_string_from_utf8()
	while "\n" in _buffer:
		var newline := _buffer.find("\n")
		var line := _buffer.substr(0, newline)
		_buffer = _buffer.substr(newline + 1)
		var message = JSON.parse_string(line)
		if message is Dictionary:
			message_received.emit(message)
