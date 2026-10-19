"""Authoritative party, clan and player-trade rules."""

from typing import Any


def create_party(player: Any, parties: dict[str, set[str]], counter: int) -> tuple[dict[str, Any], int]:
    if player.party_id:
        return {"ok": False, "reason": "already_in_party"}, counter
    counter += 1
    party_id = f"party-{counter}"
    parties[party_id] = {player.player_id}
    player.party_id = party_id
    return {"ok": True, "party_id": party_id, "members": sorted(parties[party_id])}, counter


def join_party(player: Any, party_id: str, parties: dict[str, set[str]]) -> dict[str, Any]:
    if player.party_id or party_id not in parties:
        return {"ok": False, "reason": "party_unavailable"}
    if len(parties[party_id]) >= 5:
        return {"ok": False, "reason": "party_full"}
    parties[party_id].add(player.player_id)
    player.party_id = party_id
    return {"ok": True, "party_id": party_id, "members": sorted(parties[party_id])}


def create_clan(player: Any, clans: dict[str, set[str]], counter: int) -> tuple[dict[str, Any], int]:
    if player.clan_id:
        return {"ok": False, "reason": "already_in_clan"}, counter
    counter += 1
    clan_id = f"clan-{counter}"
    clans[clan_id] = {player.player_id}
    player.clan_id = clan_id
    return {"ok": True, "clan_id": clan_id, "members": sorted(clans[clan_id])}, counter


def join_clan(player: Any, clan_id: str, clans: dict[str, set[str]]) -> dict[str, Any]:
    if player.clan_id or clan_id not in clans:
        return {"ok": False, "reason": "clan_unavailable"}
    if len(clans[clan_id]) >= 20:
        return {"ok": False, "reason": "clan_full"}
    clans[clan_id].add(player.player_id)
    player.clan_id = clan_id
    return {"ok": True, "clan_id": clan_id, "members": sorted(clans[clan_id])}


def request_trade(player: Any, target_id: str, players: dict[str, Any], requests: dict[str, str]) -> dict[str, Any]:
    target = players.get(target_id)
    if target is None or target_id == player.player_id or target.region_id != player.region_id:
        return {"ok": False, "reason": "target_unavailable"}
    requests[target_id] = player.player_id
    return {"ok": True, "state": "requested", "target_id": target_id}


def accept_trade(player: Any, players: dict[str, Any], requests: dict[str, str], offers: dict) -> dict[str, Any]:
    requester_id = requests.pop(player.player_id, "")
    if not requester_id or requester_id not in players:
        return {"ok": False, "reason": "trade_not_found"}
    key = tuple(sorted((player.player_id, requester_id)))
    offers[key] = {player.player_id: {}, requester_id: {}}
    return {"ok": True, "state": "opened", "trade_id": "|".join(key), "partner_id": requester_id}


def offer_trade(player: Any, partner_id: str, item_id: str, amount: int, offers: dict) -> dict[str, Any]:
    key = tuple(sorted((player.player_id, partner_id)))
    trade = offers.get(key)
    amount = max(0, min(99, amount))
    if trade is None or item_id not in player.inventory or amount > player.inventory[item_id]:
        return {"ok": False, "reason": "invalid_offer"}
    trade[player.player_id] = {item_id: amount}
    return {"ok": True, "state": "offered", "partner_id": partner_id, "offer": trade[player.player_id]}


def commit_trade(player: Any, partner_id: str, players: dict[str, Any], offers: dict) -> dict[str, Any]:
    key = tuple(sorted((player.player_id, partner_id)))
    trade = offers.pop(key, None)
    partner = players.get(partner_id)
    if trade is None or partner is None:
        return {"ok": False, "reason": "trade_not_found"}
    for owner, recipient in ((player, partner), (partner, player)):
        for item_id, amount in trade.get(owner.player_id, {}).items():
            owner.inventory[item_id] -= amount
            if owner.inventory[item_id] <= 0:
                del owner.inventory[item_id]
            recipient.inventory[item_id] = recipient.inventory.get(item_id, 0) + amount
    return {"ok": True, "state": "completed", "inventory": player.inventory.copy(), "partner": partner}
