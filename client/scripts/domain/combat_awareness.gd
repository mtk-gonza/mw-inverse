class_name CombatAwareness
extends RefCounted

## Minimal local awareness buffer. It is a hint for the client UI; authoritative
## combat decisions belong to the server.

var _last_hits: Dictionary = {}
const MAX_HITS_PER_TARGET := 128

func record_hit(target_id: int, attacker_id: int, timestamp_ms: int) -> void:
\tif not _last_hits.has(target_id):
\t\t_last_hits[target_id] = []
\t_last_hits[target_id].append({"attacker_id": attacker_id, "timestamp_ms": timestamp_ms})
\tif _last_hits[target_id].size() > MAX_HITS_PER_TARGET:
\t\t_last_hits[target_id].pop_front()

func forget(target_id: int) -> void:
	_last_hits.erase(target_id)

func was_hit_by(target_id: int, attacker_id: int, since_ms: int) -> bool:
	if not _last_hits.has(target_id):
		return false
	for hit in _last_hits[target_id]:
		if hit.attacker_id == attacker_id and hit.timestamp_ms >= since_ms:
			return true
	return false
