class_name ExplorationSession
extends RefCounted

## Independent model inspired by the observed session/version pattern.
## It intentionally does not copy the original data formats.

enum LoadState { IDLE, LOADING, READY, ERROR }

var generation: int = 0
var state: LoadState = LoadState.IDLE
var error_message: String = ""
var regions: Dictionary = {}

func start() -> void:
	generation += 1
	state = LoadState.LOADING
	error_message = ""

func complete(loaded_regions: Dictionary) -> void:
	if state != LoadState.LOADING:
		return
	regions = loaded_regions.duplicate(true)
	state = LoadState.READY

func fail(message: String) -> void:
	if state != LoadState.LOADING:
		return
	error_message = message
	state = LoadState.ERROR

func has_region(region_id: String) -> bool:
	return regions.has(region_id)
