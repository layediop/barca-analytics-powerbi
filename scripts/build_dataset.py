"""
Barça Analytics – pipeline de préparation des données
=====================================================
Source : StatsBomb Open Data (https://github.com/statsbomb/open-data)
Périmètre : FC Barcelone, La Liga 2018/19, 2019/20, 2020/21

Entrée  : dossier raw/ contenant matches/, events/, lineups/ (JSON StatsBomb)
Sortie  : dossier data/ contenant un modèle en étoile en CSV (UTF-8 avec BOM,
          pour que Power BI et Excel lisent correctement les accents).

Usage   : python build_dataset.py <dossier_raw> <dossier_sortie>
"""
import json
import math
import sys
from pathlib import Path

import pandas as pd

RAW = Path(sys.argv[1] if len(sys.argv) > 1 else "raw")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "data")
OUT.mkdir(parents=True, exist_ok=True)

BARCA_ID = 217
SEASONS = {4: "2018/19", 42: "2019/20", 90: "2020/21"}
GOAL_X, GOAL_Y = 120.0, 40.0  # centre du but adverse (terrain StatsBomb 120 x 80)

POSITION_GROUP = {
    "Goalkeeper": "Gardien",
    "Back": "Défenseur", "Center Back": "Défenseur", "Wing Back": "Défenseur",
    "Defensive Midfield": "Milieu", "Center Midfield": "Milieu",
    "Midfield": "Milieu", "Attacking Midfield": "Milieu",
    "Wing": "Attaquant", "Forward": "Attaquant", "Striker": "Attaquant",
}


def position_group(pos: str) -> str:
    if not pos:
        return "Inconnu"
    if pos == "Goalkeeper":
        return "Gardien"
    # on teste les motifs les plus spécifiques d'abord
    for key in ["Wing Back", "Center Back", "Back", "Defensive Midfield",
                "Attacking Midfield", "Center Midfield", "Midfield",
                "Wing", "Forward", "Striker"]:
        if key in pos:
            return POSITION_GROUP[key]
    return "Inconnu"


def mmss_to_min(t: str) -> float:
    m, s = t.split(":")
    return int(m) + int(s) / 60


def dist(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)


def shot_zone(x, y):
    if x >= 114 and 30 <= y <= 50:
        return "Surface de but"
    if x >= 102 and 18 <= y <= 62:
        return "Surface de réparation"
    return "Hors surface"


teams, players, matches = {}, {}, []
shots, player_match, team_match = [], [], []

for season_id, season_name in SEASONS.items():
    for m in json.load(open(RAW / "matches" / f"{season_id}.json", encoding="utf-8")):
        mid = m["match_id"]
        home, away = m["home_team"], m["away_team"]
        teams[home["home_team_id"]] = home["home_team_name"]
        teams[away["away_team_id"]] = away["away_team_name"]
        barca_home = home["home_team_id"] == BARCA_ID
        opp = away if barca_home else home
        opp_id = opp["away_team_id"] if barca_home else opp["home_team_id"]
        gf = m["home_score"] if barca_home else m["away_score"]
        ga = m["away_score"] if barca_home else m["home_score"]
        res = "Victoire" if gf > ga else ("Nul" if gf == ga else "Défaite")
        mgr = lambda t: ", ".join(x.get("nickname") or x["name"] for x in (t.get("managers") or []))
        matches.append({
            "match_id": mid,
            "match_date": m["match_date"],
            "kick_off": (m.get("kick_off") or "")[:5],
            "season": season_name,
            "matchweek": m.get("match_week"),
            "opponent_id": opp_id,
            "opponent_name": opp["away_team_name"] if barca_home else opp["home_team_name"],
            "venue": "Domicile" if barca_home else "Extérieur",
            "stadium": (m.get("stadium") or {}).get("name"),
            "referee": (m.get("referee") or {}).get("name"),
            "barca_manager": mgr(home if barca_home else away),
            "opponent_manager": mgr(opp),
            "goals_for": gf,
            "goals_against": ga,
            "result": res,
            "points": 3 if res == "Victoire" else (1 if res == "Nul" else 0),
            "score_label": f"{gf}-{ga}",
            "result_code": res[0],  # V / N / D
            "match_label": f"{season_name} J{m.get('match_week')} · {(opp['away_team_name'] if barca_home else opp['home_team_name'])} "
                           f"({'D' if barca_home else 'E'}) {gf}-{ga}",
        })

        events = json.load(open(RAW / "events" / f"{mid}.json", encoding="utf-8"))
        lineups = json.load(open(RAW / "lineups" / f"{mid}.json", encoding="utf-8"))
        match_end = max(e["minute"] + e["second"] / 60 for e in events)
        ev_by_id = {e["id"]: e for e in events}

        # ---------- possession (part du temps de jeu par équipe en possession) ----
        poss = {}
        for e in events:
            if e.get("duration") and e.get("possession_team"):
                t = e["possession_team"]["id"]
                poss[t] = poss.get(t, 0) + e["duration"]
        tot_poss = sum(poss.values()) or 1

        # ---------- joueurs / minutes ----------
        pm = {}
        for team in lineups:
            tid = team["team_id"]
            for p in team["lineup"]:
                pid = p["player_id"]
                if not p["positions"]:
                    continue  # remplaçant non entré
                main_pos = max(
                    p["positions"],
                    key=lambda x: (mmss_to_min(x["to"]) if x["to"] else match_end) - mmss_to_min(x["from"]),
                )["position"]
                start = min(mmss_to_min(x["from"]) for x in p["positions"])
                end = max(mmss_to_min(x["to"]) if x["to"] else match_end for x in p["positions"])
                cards = [c["card_type"] for c in p.get("cards", [])]
                players.setdefault(pid, {
                    "player_id": pid,
                    "player_name": p.get("player_nickname") or p["player_name"],
                    "full_name": p["player_name"],
                    "country": (p.get("country") or {}).get("name"),
                    "_positions": [],
                })
                players[pid]["_positions"].append(main_pos)
                pm[pid] = {
                    "match_id": mid, "player_id": pid, "team_id": tid,
                    "is_starter": int(any(x["start_reason"] == "Starting XI" for x in p["positions"])),
                    "position": main_pos,
                    "position_group": position_group(main_pos),
                    "minutes": round(max(end - start, 0), 1),
                    "yellow_cards": sum(c in ("Yellow Card", "Second Yellow") for c in cards),
                    "red_cards": sum(c in ("Red Card", "Second Yellow") for c in cards),
                    "goals": 0, "non_penalty_goals": 0, "shots": 0, "shots_on_target": 0,
                    "xg": 0.0, "npxg": 0.0, "assists": 0, "xa": 0.0, "key_passes": 0,
                    "passes": 0, "passes_completed": 0, "progressive_passes": 0,
                    "passes_into_box": 0, "crosses": 0,
                    "dribbles": 0, "dribbles_completed": 0, "progressive_carries": 0,
                    "tackles": 0, "tackles_won": 0, "interceptions": 0,
                    "ball_recoveries": 0, "pressures": 0, "fouls_committed": 0, "fouls_won": 0,
                    "touches": 0,
                }

        # ---------- statistiques d'équipe par match ----------
        tm = {}
        for team in lineups:
            tid = team["team_id"]
            tm[tid] = {
                "match_id": mid, "team_id": tid, "is_barca": int(tid == BARCA_ID),
                "goals": m["home_score"] if tid == home["home_team_id"] else m["away_score"],
                "possession_pct": round(poss.get(tid, 0) / tot_poss, 4),
                "shots": 0, "shots_on_target": 0, "xg": 0.0, "passes": 0, "passes_completed": 0,
            }

        def P(e):
            pid = (e.get("player") or {}).get("id")
            return pm.get(pid)

        for e in events:
            typ = e["type"]["name"]
            p = P(e)
            tid = (e.get("team") or {}).get("id")
            if p and typ in ("Pass", "Carry", "Ball Receipt*", "Shot", "Dribble",
                             "Ball Recovery", "Clearance", "Interception", "Miscontrol"):
                p["touches"] += 1

            if typ == "Pass":
                ps = e["pass"]
                if ps.get("type", {}).get("name") in ("Throw-in",):
                    pass
                completed = "outcome" not in ps
                if tid in tm:
                    tm[tid]["passes"] += 1
                    tm[tid]["passes_completed"] += completed
                if p:
                    p["passes"] += 1
                    p["passes_completed"] += completed
                    if ps.get("goal_assist"):
                        p["assists"] += 1
                    if ps.get("shot_assist") or ps.get("goal_assist"):
                        p["key_passes"] += 1
                    if ps.get("cross"):
                        p["crosses"] += 1
                    x0, y0 = e["location"]
                    x1, y1 = ps["end_location"]
                    if completed:
                        if dist(x0, y0, GOAL_X, GOAL_Y) - dist(x1, y1, GOAL_X, GOAL_Y) >= 10 and x1 > 60:
                            p["progressive_passes"] += 1
                        if x1 >= 102 and 18 <= y1 <= 62 and not (x0 >= 102 and 18 <= y0 <= 62):
                            p["passes_into_box"] += 1

            elif typ == "Carry" and p:
                x0, y0 = e["location"]
                x1, y1 = e["carry"]["end_location"]
                if dist(x0, y0, GOAL_X, GOAL_Y) - dist(x1, y1, GOAL_X, GOAL_Y) >= 10 and x1 > 60:
                    p["progressive_carries"] += 1

            elif typ == "Dribble" and p:
                p["dribbles"] += 1
                p["dribbles_completed"] += e["dribble"]["outcome"]["name"] == "Complete"

            elif typ == "Duel" and p and e["duel"].get("type", {}).get("name") == "Tackle":
                p["tackles"] += 1
                p["tackles_won"] += e["duel"].get("outcome", {}).get("name") in ("Won", "Success In Play", "Success Out")

            elif typ == "Interception" and p:
                p["interceptions"] += 1
            elif typ == "Ball Recovery" and p:
                p["ball_recoveries"] += 1
            elif typ == "Pressure" and p:
                p["pressures"] += 1
            elif typ == "Foul Committed" and p:
                p["fouls_committed"] += 1
            elif typ == "Foul Won" and p:
                p["fouls_won"] += 1

            elif typ == "Shot":
                s = e["shot"]
                outcome = s["outcome"]["name"]
                is_goal = int(outcome == "Goal")
                on_target = int(outcome in ("Goal", "Saved", "Saved To Post"))
                stype = s["type"]["name"]
                xg = s.get("statsbomb_xg") or 0.0
                x, y = e["location"]
                kp = ev_by_id.get(s.get("key_pass_id")) if s.get("key_pass_id") else None
                assister = (kp.get("player") or {}).get("id") if kp else None
                shots.append({
                    "shot_id": e["id"], "match_id": mid, "team_id": tid,
                    "player_id": e["player"]["id"], "assist_player_id": assister,
                    "period": e["period"], "minute": e["minute"], "second": e["second"],
                    "minute_bucket": f"{min(e['minute'] // 15, 5) * 15}-{min(e['minute'] // 15, 5) * 15 + 15}"
                                     .replace("75-90", "75-90+"),
                    "xg": round(xg, 4), "outcome": outcome,
                    "shot_result": "But" if is_goal else ("Cadré" if on_target else "Non cadré"),
                    "is_goal": is_goal, "is_on_target": on_target,
                    "is_penalty": int(stype == "Penalty"),
                    "shot_type": stype, "body_part": s["body_part"]["name"],
                    "technique": s["technique"]["name"],
                    "play_pattern": e["play_pattern"]["name"],
                    "under_pressure": int(bool(e.get("under_pressure"))),
                    "first_time": int(bool(s.get("first_time"))),
                    "x": x, "y": y,
                    "map_x": y, "map_y": x,  # coordonnées pour une demi-surface verticale (but en haut)
                    "distance_m": round(dist(x, y, GOAL_X, GOAL_Y) * 0.9144, 1),  # yards → mètres
                    "zone": shot_zone(x, y),
                })
                if tid in tm:
                    tm[tid]["shots"] += 1
                    tm[tid]["shots_on_target"] += on_target
                    tm[tid]["xg"] += xg
                if p:
                    p["shots"] += 1
                    p["shots_on_target"] += on_target
                    p["goals"] += is_goal
                    p["xg"] += xg
                    if stype != "Penalty":
                        p["non_penalty_goals"] += is_goal
                        p["npxg"] += xg
                if assister in pm:
                    pm[assister]["xa"] += xg

        player_match.extend(pm.values())
        team_match.extend(tm.values())

# ---------- DimPlayer ----------
for p in players.values():
    main = pd.Series(p.pop("_positions")).mode().iloc[0]
    p["main_position"] = main
    p["position_group"] = position_group(main)

# ---------- export ----------
def save(rows, name, round_cols=None):
    df = pd.DataFrame(rows)
    if "assist_player_id" in df:
        df["assist_player_id"] = df["assist_player_id"].astype("Int64")  # entier nullable, pas de « 5503.0 »
    for c in df.select_dtypes("float").columns:
        df[c] = df[c].round(4)
    df.to_csv(OUT / f"{name}.csv", index=False, encoding="utf-8-sig")
    print(f"{name:<20} {len(df):>7} lignes")
    return df

save(sorted(matches, key=lambda r: r["match_date"]), "DimMatch")
save([{"team_id": k, "team_name": v, "is_barca": int(k == BARCA_ID),
       "team_side": "FC Barcelone" if k == BARCA_ID else "Adversaire"}
      for k, v in sorted(teams.items(), key=lambda x: x[1])], "DimTeam")
barca_players = {r["player_id"] for r in player_match if r["team_id"] == BARCA_ID}
for p in players.values():
    p["is_barca_player"] = int(p["player_id"] in barca_players)
save(list(players.values()), "DimPlayer")
save(shots, "FactShots")
save(player_match, "FactPlayerMatch")
save(team_match, "FactTeamMatch")
