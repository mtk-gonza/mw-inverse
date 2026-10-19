QUESTS = {
    "training_hunt": {
        "title": "Práctica de combate",
        "target": "training_dummy",
        "goal": 3,
        "experience_reward": 50,
    }
    ,"frostwood_expedition": {
        "title": "Expedición escarchada",
        "target": "frost_wisp",
        "goal": 2,
        "experience_reward": 100,
    }
}


def initial_quests() -> dict:
    return {quest_id: {"progress": 0, "completed": False} for quest_id in QUESTS}
