class_name TargetingCandidate
extends RefCounted

## Client-side representation of a possible target.
## The server remains authoritative for the final decision.

var entity_id: int
var distance_squared: float
var is_party_member: bool
var is_foreign_attacker: bool
var is_excluded: bool
var score: int = 0

func _init(id: int, distance_sq: float) -> void:
	entity_id = id
	distance_squared = distance_sq


class TargetingService:
	var search_radius_squared: float = 25.0

	func rank(candidates: Array[TargetingCandidate]) -> Array[TargetingCandidate]:
		var usable: Array[TargetingCandidate] = []
		for candidate in candidates:
			if candidate.is_excluded:
				continue
			if candidate.distance_squared > search_radius_squared:
				continue
			candidate.score = _score(candidate)
			usable.append(candidate)
		usable.sort_custom(func(a: TargetingCandidate, b: TargetingCandidate) -> bool:
			return a.score > b.score
		)
		return usable

	func _score(candidate: TargetingCandidate) -> int:
		var value := 0
		if candidate.is_foreign_attacker:
			value += 1000
		if not candidate.is_party_member:
			value += 100
		value -= int(candidate.distance_squared)
		return value
