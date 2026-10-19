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


class TargetingProfile:
	## Own, serializable targeting preferences. The server still validates the result.
	var search_radius_squared: float = 25.0
	var prefer_foreign_attackers := true
	var prefer_non_party := true
	var excluded_ids: Array[int] = []
	var switch_mode := "nearest"

	func to_dict() -> Dictionary:
		return {
			"search_radius_squared": search_radius_squared,
			"prefer_foreign_attackers": prefer_foreign_attackers,
			"prefer_non_party": prefer_non_party,
			"excluded_ids": excluded_ids.duplicate(),
			"switch_mode": switch_mode,
		}

	func from_dict(data: Dictionary) -> void:
		search_radius_squared = maxf(1.0, float(data.get("search_radius_squared", search_radius_squared)))
		prefer_foreign_attackers = bool(data.get("prefer_foreign_attackers", prefer_foreign_attackers))
		prefer_non_party = bool(data.get("prefer_non_party", prefer_non_party))
		excluded_ids = []
		for value in data.get("excluded_ids", []):
			if excluded_ids.size() >= 128:
				break
			excluded_ids.append(int(value))
		var requested_mode := str(data.get("switch_mode", switch_mode))
		switch_mode = requested_mode if requested_mode in ["nearest", "attacker", "cycle"] else "nearest"

func _init(id: int, distance_sq: float) -> void:
	entity_id = id
	distance_squared = distance_sq


class TargetingService:
	var profile := TargetingProfile.new()

	func set_profile(value: TargetingProfile) -> void:
		profile = value

	func rank(candidates: Array[TargetingCandidate]) -> Array[TargetingCandidate]:
		var usable: Array[TargetingCandidate] = []
		for candidate in candidates:
			if candidate.entity_id in profile.excluded_ids:
				continue
			if candidate.is_excluded:
				continue
			if candidate.distance_squared > profile.search_radius_squared:
				continue
			candidate.score = _score(candidate)
			usable.append(candidate)
		usable.sort_custom(func(a: TargetingCandidate, b: TargetingCandidate) -> bool:
			if a.score == b.score:
				return a.distance_squared < b.distance_squared
			return a.score > b.score
		)
		return usable

	func _score(candidate: TargetingCandidate) -> int:
		var value := 0
		if profile.prefer_foreign_attackers and candidate.is_foreign_attacker:
			value += 1000
		if profile.prefer_non_party and not candidate.is_party_member:
			value += 100
		value -= int(candidate.distance_squared)
		return value
