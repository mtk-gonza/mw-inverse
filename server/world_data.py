REGIONS = {
    "training_meadow": {
        "name": "Pradera de entrenamiento",
        "level_min": 1,
        "level_max": 5,
        "npcs": ["mentor_arin"],
        "enemies": ["training_dummy_1", "training_dummy_2", "training_dummy_3"],
        "shrines": ["frost_lantern"],
    },
    "quiet_harbor": {
        "name": "Puerto tranquilo",
        "level_min": 1,
        "level_max": 10,
        "npcs": ["quartermaster_lynn"],
        "enemies": [],
        "shrines": ["harbor_beacon"],
    },
    "frostwood": {
        "name": "Bosque escarchado",
        "level_min": 3,
        "level_max": 20,
        "npcs": ["warden_sela"],
        "enemies": ["frost_wisp_1", "frost_wisp_2", "frost_guardian"],
        "shrines": ["frostwood_root"],
    },
}

NPCS = {
    "mentor_arin": {
        "name": "Arin",
        "region_id": "training_meadow",
        "dialogue": "Bienvenido a la pradera. Practica con los tres muñecos de entrenamiento.",
    },
    "quartermaster_lynn": {
        "name": "Lynn",
        "region_id": "quiet_harbor",
        "dialogue": "El puerto es seguro. Regresa cuando tengas algo que comerciar.",
    },
    "warden_sela": {
        "name": "Sela",
        "region_id": "frostwood",
        "dialogue": "El bosque cambia con el hielo. Sigue las luces y no pierdas de vista tu grupo.",
    },
}


def region_snapshot(region_id: str) -> dict:
    region = REGIONS.get(region_id, REGIONS["training_meadow"])
    return {"region_id": region_id if region_id in REGIONS else "training_meadow", **region}
