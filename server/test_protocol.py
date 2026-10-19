import tempfile
import unittest
from pathlib import Path

import main
from storage import PlayerStorage


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        main.PLAYERS.clear()
        main.ONLINE_PLAYER_IDS.clear()
        main.CLANS.clear()
        main.TRADE_REQUESTS.clear()
        main.TRADE_OFFERS.clear()
        main.MATCHMAKING_QUEUE.clear()
        main.MATCHES.clear()
        for enemy_id in ("training_dummy_1", "training_dummy_2", "training_dummy_3"):
            main.ENEMY_HEALTH[enemy_id] = 30
        main.ENEMY_HEALTH.update({"frost_wisp_1": 45, "frost_wisp_2": 45, "frost_guardian": 120})
        main.ENEMY_POSITIONS.update({
            "training_dummy_1": {"x": 0.0, "y": 0.8, "z": -4.0},
            "training_dummy_2": {"x": 4.0, "y": 0.8, "z": -5.0},
            "training_dummy_3": {"x": -4.0, "y": 0.8, "z": -5.0},
            "frost_wisp_1": {"x": 8.0, "y": 0.8, "z": -6.0},
            "frost_wisp_2": {"x": -8.0, "y": 0.8, "z": -6.0},
            "frost_guardian": {"x": 0.0, "y": 0.8, "z": -10.0},
        })
        self.directory = tempfile.TemporaryDirectory()
        main.STORAGE = PlayerStorage(str(Path(self.directory.name) / "players.sqlite3"))

    async def asyncTearDown(self) -> None:
        self.directory.cleanup()

    async def test_login_move_attack_and_reward(self) -> None:
        player, login = await main.handle_message(None, {"type": "login_request", "player_id": "test"})
        self.assertIsNotNone(player)
        self.assertTrue(login["ok"])

        player, movement = await main.handle_message(player, {"type": "move_intent", "dx": 2, "dz": -1})
        self.assertEqual(movement["state"]["position"]["x"], 2)

        for enemy_number in range(1, 4):
            target_id = f"training_dummy_{enemy_number}"
            for _ in range(3):
                player, combat = await main.handle_message(player, {"type": "attack_request", "target_id": target_id})
        self.assertTrue(combat["defeated"])
        self.assertEqual(combat["inventory"]["monster_core"], 3)
        self.assertEqual(combat["quests"]["training_hunt"]["progress"], 3)
        self.assertTrue(combat["quests"]["training_hunt"]["completed"])

        saved = main.STORAGE.load("test")
        self.assertIsNotNone(saved)
        self.assertEqual(saved["inventory"]["monster_core"], 3)
        self.assertEqual(saved["state_version"], 1)

    async def test_invalid_target_is_rejected(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "test"})
        _, result = await main.handle_message(player, {"type": "attack_request", "target_id": "unknown"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "invalid_target")

    async def test_protocol_version_is_negotiated_and_rejected_when_unknown(self) -> None:
        _, accepted = await main.handle_message(None, {"type": "login_request", "player_id": "versioned", "protocol_version": main.PROTOCOL_VERSION})
        self.assertEqual(accepted["protocol_version"], main.PROTOCOL_VERSION)
        _, rejected = await main.handle_message(None, {"type": "login_request", "player_id": "bad-version", "protocol_version": 999})
        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["code"], "unsupported_protocol")

    async def test_health_request_is_available_before_login(self) -> None:
        _, result = await main.handle_message(None, {"type": "health_request"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "ready")

    async def test_health_request_reports_protocol_and_metrics(self) -> None:
        _, result = await main.handle_message(None, {"type": "health_request"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["protocol_version"], main.PROTOCOL_VERSION)
        self.assertIn("messages", result["metrics"])
        self.assertIn("metrics", result)

    async def test_shrine_discovery_is_region_bound_and_persistent(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "shrine"})
        _, result = await main.handle_message(player, {"type": "discover_shrine", "shrine_id": "frost_lantern"})
        self.assertTrue(result["ok"])
        self.assertIn("frost_lantern", result["discovered"])
        _, rejected = await main.handle_message(player, {"type": "discover_shrine", "shrine_id": "harbor_beacon"})
        self.assertFalse(rejected["ok"])

    async def test_frost_loot_and_crafting_are_authoritative(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "crafter"})
        player.level = 3
        player.inventory = {"monster_core": 2, "ice_shard": 3}
        player.currency = 100
        main.ENEMY_HEALTH["frost_wisp_1"] = 1
        _, combat = await main.handle_message(player, {"type": "attack_request", "target_id": "frost_wisp_1"})
        self.assertTrue(combat["defeated"])
        self.assertGreaterEqual(combat["inventory"].get("ice_shard", 0), 5)
        _, crafted = await main.handle_message(player, {"type": "craft_request", "item_id": "frost_blade"})
        self.assertTrue(crafted["ok"])
        self.assertEqual(crafted["inventory"].get("frost_blade"), 1)

    async def test_selling_material_is_atomic_and_persistent(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "seller"})
        player.inventory["ice_shard"] = 2
        starting_currency = player.currency
        _, result = await main.handle_message(player, {"type": "sell_request", "item_id": "ice_shard", "amount": 2})
        self.assertTrue(result["ok"])
        self.assertEqual(result["currency"], starting_currency + 16)
        self.assertNotIn("ice_shard", result["inventory"])

    async def test_shop_request_id_is_idempotent(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "idempotent-shop"})
        starting_currency = player.currency
        request = {"type": "buy_request", "item_id": "health_potion", "request_id": "buy-1"}
        _, first = await main.handle_message(player, request)
        _, second = await main.handle_message(player, request)
        self.assertEqual(first, second)
        self.assertEqual(player.currency, starting_currency - 25)
        self.assertEqual(player.inventory.get("health_potion"), 1)

    async def test_enemy_ai_attacks_when_in_range_and_guard_reduces_damage(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "combatant"})
        player.x, player.z = 0.0, -4.0
        main.ENEMY_POSITIONS["training_dummy_1"] = {"x": 0.0, "y": 0.8, "z": -4.0}
        before = player.health
        _, tick = await main.handle_message(player, {"type": "world_tick"})
        self.assertTrue(tick["enemy_attacks"])
        self.assertLess(player.health, before)

    async def test_movement_is_clamped_to_world_and_attack_requires_range(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "bounds"})
        _, movement = await main.handle_message(player, {"type": "move_intent", "dx": 999, "dz": 999})
        self.assertLessEqual(abs(movement["state"]["position"]["x"]), main.WORLD_LIMIT)
        _, combat = await main.handle_message(player, {"type": "attack_request", "target_id": "training_dummy_1"})
        self.assertFalse(combat["ok"])
        self.assertEqual(combat["reason"], "target_out_of_range")

    async def test_attack_request_id_is_idempotent(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "idempotent-attack"})
        player.x, player.z = 0.0, -4.0
        main.ENEMY_HEALTH["training_dummy_1"] = 100
        request = {"type": "attack_request", "target_id": "training_dummy_1", "request_id": "attack-1"}
        _, first = await main.handle_message(player, request)
        health_after_first = main.ENEMY_HEALTH["training_dummy_1"]
        _, second = await main.handle_message(player, request)
        self.assertEqual(first, second)
        self.assertEqual(main.ENEMY_HEALTH["training_dummy_1"], health_after_first)

    async def test_frost_nova_applies_authoritative_slow_state(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "slower"})
        player.x, player.z = 0.0, -4.0
        main.ENEMY_HEALTH["training_dummy_1"] = 30
        _, result = await main.handle_message(player, {"type": "skill_request", "skill_id": "frost_nova", "target_id": "training_dummy_1"})
        self.assertTrue(result["ok"])
        self.assertGreater(main.ENEMY_SLOWED_UNTIL["training_dummy_1"], 0.0)

    async def test_skill_and_consume_request_ids_are_idempotent(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "idempotent-skill"})
        player.x, player.z = 0.0, -4.0
        player.inventory["health_potion"] = 1
        player.health = 50
        first_health = player.health
        consume = {"type": "consume_request", "item_id": "health_potion", "request_id": "consume-1"}
        _, first = await main.handle_message(player, consume)
        _, duplicate = await main.handle_message(player, consume)
        self.assertEqual(first, duplicate)
        self.assertGreater(player.health, first_health)
        main.ENEMY_HEALTH["training_dummy_1"] = 100
        skill = {"type": "skill_request", "skill_id": "arcane_bolt", "target_id": "training_dummy_1", "request_id": "skill-1"}
        _, cast = await main.handle_message(player, skill)
        energy_after_cast = player.energy
        _, cast_duplicate = await main.handle_message(player, skill)
        self.assertEqual(cast, cast_duplicate)
        self.assertEqual(player.energy, energy_after_cast)

    async def test_skill_casting_locks_movement_authoritatively(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "casting-lock"})
        player.x, player.z = 0.0, -4.0
        main.ENEMY_HEALTH["training_dummy_1"] = 100
        _, cast = await main.handle_message(player, {"type": "skill_request", "skill_id": "arcane_bolt", "target_id": "training_dummy_1"})
        self.assertTrue(cast["ok"])
        before = (player.x, player.z)
        _, movement = await main.handle_message(player, {"type": "move_intent", "dx": 1.0, "dz": 0.0})
        self.assertFalse(movement["ok"])
        self.assertEqual(movement["reason"], "casting")
        self.assertEqual((player.x, player.z), before)

    async def test_invalid_skill_does_not_consume_energy_or_cooldown(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "invalid-skill"})
        energy = player.energy
        _, result = await main.handle_message(player, {"type": "skill_request", "skill_id": "arcane_bolt", "target_id": "missing"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "invalid_target")
        self.assertEqual(player.energy, energy)
        self.assertNotIn("arcane_bolt", player.skill_ready_at)

    async def test_basic_attack_locks_movement_recovery_window(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "attack-lock"})
        player.x, player.z = 0.0, -4.0
        main.ENEMY_HEALTH["training_dummy_1"] = 100
        _, attack = await main.handle_message(player, {"type": "attack_request", "target_id": "training_dummy_1"})
        self.assertTrue(attack["ok"])
        _, movement = await main.handle_message(player, {"type": "move_intent", "dx": 1.0, "dz": 0.0})
        self.assertFalse(movement["ok"])
        self.assertEqual(movement["reason"], "casting")

    async def test_attack_requires_line_of_sight(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "los-test"})
        player.x, player.z = 0.0, 0.0
        main.ENEMY_POSITIONS["training_dummy_1"] = {"x": 0.0, "y": 0.8, "z": 4.0}
        _, result = await main.handle_message(player, {"type": "attack_request", "target_id": "training_dummy_1"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "line_of_sight_blocked")

    async def test_region_transition_is_persisted(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "test"})
        _, result = await main.handle_message(player, {"type": "enter_region_request", "region_id": "quiet_harbor"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["region"]["name"], "Puerto tranquilo")
        self.assertEqual(main.STORAGE.load("test")["region_id"], "quiet_harbor")

    async def test_npc_dialogue_requires_current_region(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "test"})
        _, result = await main.handle_message(player, {"type": "npc_interact", "npc_id": "mentor_arin"})
        self.assertTrue(result["ok"])
        self.assertIn("pradera", result["dialogue"])

    async def test_chat_message_is_normalized_and_bounded(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "test"})
        _, result = await main.handle_message(player, {"type": "chat_message", "text": "  hola   mundo  "})
        self.assertTrue(result["ok"])
        self.assertEqual(result["text"], "hola mundo")

    async def test_chat_channels_are_validated(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "chat-channel"})
        _, party = await main.handle_message(player, {"type": "chat_message", "channel": "party", "text": "hola"})
        self.assertTrue(party["ok"])
        self.assertEqual(party["channel"], "party")
        _, invalid = await main.handle_message(player, {"type": "chat_message", "channel": "invalid", "text": "hola"})
        self.assertFalse(invalid["ok"])

    async def test_whisper_requires_an_online_recipient(self) -> None:
        sender, _ = await main.handle_message(None, {"type": "login_request", "player_id": "whisper-sender"})
        _, missing = await main.handle_message(sender, {"type": "chat_message", "channel": "whisper", "recipient_id": "missing", "text": "hola"})
        self.assertFalse(missing["ok"])
        self.assertEqual(missing["reason"], "recipient_unavailable")
        recipient, _ = await main.handle_message(None, {"type": "login_request", "player_id": "whisper-recipient"})
        _, delivered = await main.handle_message(sender, {"type": "chat_message", "channel": "whisper", "recipient_id": recipient.player_id, "text": "hola"})
        self.assertTrue(delivered["ok"])

    async def test_block_list_is_persistent_and_filters_chat(self) -> None:
        blocker, _ = await main.handle_message(None, {"type": "login_request", "player_id": "blocker"})
        blocked, _ = await main.handle_message(None, {"type": "login_request", "player_id": "blocked"})
        _, result = await main.handle_message(blocker, {"type": "block_player", "player_id": blocked.player_id})
        self.assertTrue(result["ok"])
        self.assertIn(blocked.player_id, blocker.blocked_players)
        saved = main.STORAGE.load(blocker.player_id)
        self.assertIn(blocked.player_id, saved["blocked_players"])
        self.assertFalse(main._chat_recipient_allowed(blocked, blocker, "whisper", blocker.player_id))

    async def test_party_create_and_join(self) -> None:
        main.PARTIES.clear()
        player_a, _ = await main.handle_message(None, {"type": "login_request", "player_id": "a"})
        _, created = await main.handle_message(player_a, {"type": "party_create"})
        self.assertTrue(created["ok"])
        player_b, _ = await main.handle_message(None, {"type": "login_request", "player_id": "b"})
        _, joined = await main.handle_message(player_b, {"type": "party_join", "party_id": created["party_id"]})
        self.assertTrue(joined["ok"])
        self.assertEqual(len(joined["members"]), 2)

    async def test_stale_party_reference_is_cleared_after_restart(self) -> None:
        main.PARTIES.clear()
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "stale"})
        _, created = await main.handle_message(player, {"type": "party_create"})
        self.assertTrue(created["ok"])
        main.PLAYERS.clear()
        main.PARTIES.clear()
        restored, _ = await main.handle_message(None, {"type": "login_request", "player_id": "stale"})
        self.assertEqual(restored.party_id, "")

    async def test_world_snapshot_contains_same_region_players(self) -> None:
        player_a, _ = await main.handle_message(None, {"type": "login_request", "player_id": "a"})
        await main.handle_message(None, {"type": "login_request", "player_id": "b"})
        main.ONLINE_PLAYER_IDS.update({"a", "b"})
        _, snapshot = await main.handle_message(player_a, {"type": "world_snapshot"})
        self.assertEqual({entry["player_id"] for entry in snapshot["players"]}, {"a", "b"})

    async def test_presence_snapshot_contains_positions(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "a"})
        main.ONLINE_PLAYER_IDS.add("a")
        await main.handle_message(player, {"type": "move_intent", "dx": 1, "dz": 2})
        snapshot = main.presence_snapshot()
        entry = next(item for item in snapshot["players"] if item["player_id"] == "a")
        self.assertEqual(entry["position"]["x"], 1)
        self.assertEqual(entry["position"]["z"], 2)

    async def test_invalid_movement_does_not_change_position(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "a"})
        _, result = await main.handle_message(player, {"type": "move_intent", "dx": "not-a-number", "dz": 0})
        self.assertEqual(result["code"], "invalid_movement")
        self.assertEqual(player.x, 0.0)

    async def test_purchase_deducts_currency_and_adds_item(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "test"})
        _, result = await main.handle_message(player, {"type": "buy_request", "item_id": "training_blade"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["currency"], 50)
        self.assertEqual(result["inventory"]["training_blade"], 1)

    async def test_defeated_enemy_cannot_be_rewarded_twice(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "test"})
        for _ in range(3):
            _, result = await main.handle_message(player, {"type": "attack_request", "target_id": "training_dummy_1"})
        self.assertTrue(result["defeated"])
        _, repeated = await main.handle_message(player, {"type": "attack_request", "target_id": "training_dummy_1"})
        self.assertFalse(repeated["ok"])

    async def test_weapon_changes_attack_value(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "test"})
        player.inventory["training_blade"] = 1
        _, result = await main.handle_message(player, {"type": "equip_request", "item_id": "training_blade"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["attack"], 15)

    async def test_skill_consumes_energy_and_applies_damage(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "mage"})
        _, result = await main.handle_message(player, {"type": "skill_request", "skill_id": "arcane_bolt", "target_id": "training_dummy_1"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["damage"], 18)
        self.assertEqual(result["energy"], 80)

    async def test_consumable_restores_energy(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "alchemist"})
        player.energy = 60
        player.inventory["mana_potion"] = 1
        _, result = await main.handle_message(player, {"type": "consume_request", "item_id": "mana_potion"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["energy"], 90)
        self.assertNotIn("mana_potion", result["inventory"])

    async def test_respawn_restores_player_resources(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "fallen"})
        player.health = 1
        player.energy = 0
        player.x = 12
        _, result = await main.handle_message(player, {"type": "respawn_request"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["state"]["health"], player.max_health)
        self.assertEqual(result["state"]["energy"], 100)
        self.assertEqual(result["state"]["position"]["x"], 0.0)

    async def test_exploration_shrine_is_persisted(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "scout"})
        _, result = await main.handle_message(player, {"type": "discover_shrine", "shrine_id": "frost_lantern"})
        self.assertTrue(result["ok"])
        self.assertIn("frost_lantern", result["discovered"])
        self.assertIn("frost_lantern", main.STORAGE.load("scout")["discovered_shrines"])

    async def test_decor_place_and_store(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "builder"})
        _, placed = await main.handle_message(player, {"type": "decor_place", "piece_id": "ice_lamp", "x": 2, "z": -1})
        self.assertTrue(placed["ok"])
        self.assertEqual(len(placed["decor"]), 1)
        _, stored = await main.handle_message(player, {"type": "decor_store", "index": 0})
        self.assertTrue(stored["ok"])
        self.assertEqual(stored["decor"], [])

    async def test_referral_code_is_stable(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "invitee"})
        _, first = await main.handle_message(player, {"type": "referral_create"})
        _, second = await main.handle_message(player, {"type": "referral_create"})
        self.assertEqual(first["code"], second["code"])

    async def test_pvp_requires_opt_in_for_both_players(self) -> None:
        attacker, _ = await main.handle_message(None, {"type": "login_request", "player_id": "attacker"})
        target, _ = await main.handle_message(None, {"type": "login_request", "player_id": "target"})
        target.x = 1.0
        _, rejected = await main.handle_message(attacker, {"type": "pvp_attack", "target_id": "target"})
        self.assertEqual(rejected["reason"], "pvp_unavailable")
        await main.handle_message(attacker, {"type": "pvp_toggle", "enabled": True})
        await main.handle_message(target, {"type": "pvp_toggle", "enabled": True})
        _, hit = await main.handle_message(attacker, {"type": "pvp_attack", "target_id": "target"})
        self.assertTrue(hit["ok"])
        self.assertEqual(hit["damage"], 10)

    async def test_trade_moves_offered_items(self) -> None:
        first, _ = await main.handle_message(None, {"type": "login_request", "player_id": "trader-a"})
        second, _ = await main.handle_message(None, {"type": "login_request", "player_id": "trader-b"})
        first.inventory["monster_core"] = 2
        await main.handle_message(first, {"type": "trade_request", "target_id": "trader-b"})
        _, opened = await main.handle_message(second, {"type": "trade_accept"})
        self.assertTrue(opened["ok"])
        await main.handle_message(first, {"type": "trade_offer", "partner_id": "trader-b", "item_id": "monster_core", "amount": 1})
        commit_request = {"type": "trade_commit", "partner_id": "trader-b", "request_id": "trade-1"}
        _, committed = await main.handle_message(first, commit_request)
        _, duplicate = await main.handle_message(first, commit_request)
        self.assertTrue(committed["ok"])
        self.assertEqual(committed, duplicate)
        self.assertEqual(first.inventory["monster_core"], 1)
        self.assertEqual(second.inventory["monster_core"], 1)

    async def test_clan_create_and_join(self) -> None:
        first, _ = await main.handle_message(None, {"type": "login_request", "player_id": "leader"})
        second, _ = await main.handle_message(None, {"type": "login_request", "player_id": "member"})
        _, created = await main.handle_message(first, {"type": "clan_create"})
        self.assertTrue(created["ok"])
        _, joined = await main.handle_message(second, {"type": "clan_join", "clan_id": created["clan_id"]})
        self.assertEqual(joined["members"], ["leader", "member"])

    async def test_login_issues_session_token_and_rejects_bad_token(self) -> None:
        player, login = await main.handle_message(None, {"type": "login_request", "player_id": "secure"})
        self.assertTrue(login["token"])
        _, rejected = await main.handle_message(player, {"type": "world_snapshot", "session_token": "bad"})
        self.assertEqual(rejected["code"], "invalid_session")
        _, accepted = await main.handle_message(player, {"type": "world_snapshot", "session_token": login["token"]})
        self.assertEqual(accepted["type"], "world_snapshot")

    async def test_matchmaking_pairs_two_players(self) -> None:
        first, _ = await main.handle_message(None, {"type": "login_request", "player_id": "queue-a"})
        second, _ = await main.handle_message(None, {"type": "login_request", "player_id": "queue-b"})
        _, queued = await main.handle_message(first, {"type": "matchmake_join"})
        self.assertEqual(queued["state"], "queued")
        _, matched = await main.handle_message(second, {"type": "matchmake_join"})
        self.assertEqual(matched["state"], "matched")
        self.assertEqual(len(main.MATCHES[matched["match_id"]]), 2)

    async def test_account_register_login_and_refresh(self) -> None:
        _, registered = await main.handle_message(None, {"type": "auth_register", "username": "Hero.One", "password": "strong-pass"})
        self.assertTrue(registered["ok"])
        _, logged_in = await main.handle_message(None, {"type": "auth_login", "username": "Hero.One", "password": "strong-pass"})
        self.assertTrue(logged_in["ok"])
        _, refreshed = await main.handle_message(None, {"type": "auth_refresh", "username": "Hero.One", "refresh_token": logged_in["refresh_token"]})
        self.assertTrue(refreshed["ok"])

    async def test_leaderboard_orders_by_level_and_kills(self) -> None:
        first, _ = await main.handle_message(None, {"type": "login_request", "player_id": "rank-a"})
        second, _ = await main.handle_message(None, {"type": "login_request", "player_id": "rank-b"})
        first.level = 3
        second.level = 2
        _, result = await main.handle_message(first, {"type": "leaderboard_request"})
        self.assertEqual(result["entries"][0]["player_id"], "rank-a")

    async def test_frostwood_region_and_shrine(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "ranger"})
        player.level = 3
        _, entered = await main.handle_message(player, {"type": "enter_region_request", "region_id": "frostwood"})
        self.assertTrue(entered["ok"])
        _, shrine = await main.handle_message(player, {"type": "discover_shrine", "shrine_id": "frostwood_root"})
        self.assertTrue(shrine["ok"])

    async def test_metrics_are_available_to_authenticated_player(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "observer"})
        _, result = await main.handle_message(player, {"type": "metrics_request"})
        self.assertTrue(result["ok"])
        self.assertGreaterEqual(result["metrics"]["messages"], 2)

    async def test_defeated_enemy_respawns_on_world_tick(self) -> None:
        player, _ = await main.handle_message(None, {"type": "login_request", "player_id": "respawner"})
        main.ENEMY_HEALTH["training_dummy_1"] = 0
        main.ENEMY_RESPAWN_AT["training_dummy_1"] = 0.0
        _, result = await main.handle_message(player, {"type": "world_tick"})
        self.assertTrue(result["ok"])
        self.assertEqual(main.ENEMY_HEALTH["training_dummy_1"], 30)

    async def test_totp_mfa_can_be_enabled_and_required(self) -> None:
        _, registered = await main.handle_message(None, {"type": "auth_register", "username": "mfa-user", "password": "strong-pass"})
        player, logged_in = await main.handle_message(None, {"type": "auth_login", "username": "mfa-user", "password": "strong-pass"})
        _, setup = await main.handle_message(player, {"type": "auth_mfa_setup", "session_token": logged_in["token"]})
        self.assertTrue(setup["ok"])
        _, enabled = await main.handle_message(player, {"type": "auth_mfa_enable", "code": setup["code"], "session_token": logged_in["token"]})
        self.assertTrue(enabled["ok"])
        _, blocked = await main.handle_message(None, {"type": "auth_login", "username": "mfa-user", "password": "strong-pass"})
        self.assertEqual(blocked["reason"], "mfa_required")


if __name__ == "__main__":
    unittest.main()
