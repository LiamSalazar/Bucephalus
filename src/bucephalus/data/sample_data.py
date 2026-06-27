from __future__ import annotations

FALLBACK_COMPETITIONS = [
    {
        "competition_id": 999,
        "season_id": 2024,
        "country_name": "Sampleland",
        "competition_name": "Bucephalus Sample Cup",
        "competition_gender": "male",
        "season_name": "2024",
    }
]

FALLBACK_MATCHES = [
    {
        "match_id": 900001,
        "match_date": "2024-05-01",
        "kick_off": "20:00:00.000",
        "competition": {"competition_id": 999, "competition_name": "Bucephalus Sample Cup"},
        "season": {"season_id": 2024, "season_name": "2024"},
        "home_team": {"home_team_id": 100, "home_team_name": "Bucephalus FC"},
        "away_team": {"away_team_id": 200, "away_team_name": "Alexandria United"},
        "home_score": 2,
        "away_score": 1,
        "competition_stage": {"id": 1, "name": "Final"},
    },
    {
        "match_id": 900002,
        "match_date": "2024-05-08",
        "kick_off": "20:00:00.000",
        "competition": {"competition_id": 999, "competition_name": "Bucephalus Sample Cup"},
        "season": {"season_id": 2024, "season_name": "2024"},
        "home_team": {"home_team_id": 200, "home_team_name": "Alexandria United"},
        "away_team": {"away_team_id": 100, "away_team_name": "Bucephalus FC"},
        "home_score": 0,
        "away_score": 1,
        "competition_stage": {"id": 1, "name": "Final"},
    },
]

FALLBACK_LINEUPS = [
    {
        "team_id": 100,
        "team_name": "Bucephalus FC",
        "lineup": [
            {
                "player_id": 10,
                "player_name": "Bernardo Silva Sample",
                "player_nickname": "Bernardo",
                "country": {"id": 620, "name": "Portugal"},
                "positions": [{"position_id": 13, "position": "Right Center Midfield"}],
            },
            {
                "player_id": 11,
                "player_name": "Valverde Sample",
                "country": {"id": 242, "name": "Uruguay"},
                "positions": [{"position_id": 15, "position": "Left Center Midfield"}],
            },
            {
                "player_id": 12,
                "player_name": "Haaland Sample",
                "country": {"id": 174, "name": "Norway"},
                "positions": [{"position_id": 23, "position": "Center Forward"}],
            },
        ],
    },
    {
        "team_id": 200,
        "team_name": "Alexandria United",
        "lineup": [
            {
                "player_id": 20,
                "player_name": "Mbappe Sample",
                "country": {"id": 78, "name": "France"},
                "positions": [{"position_id": 21, "position": "Left Wing"}],
            },
            {
                "player_id": 21,
                "player_name": "Keeper Sample",
                "country": {"id": 68, "name": "England"},
                "positions": [{"position_id": 1, "position": "Goalkeeper"}],
            },
        ],
    },
]


def fallback_events(match_id: int) -> list[dict]:
    home_team = {"id": 100, "name": "Bucephalus FC"}
    away_team = {"id": 200, "name": "Alexandria United"}
    rows = [
        _event(match_id, 1, 1, 3, "Pass", home_team, 10, "Bernardo Silva Sample", [40, 40]),
        _event(match_id, 2, 1, 4, "Carry", home_team, 10, "Bernardo Silva Sample", [50, 42]),
        _event(
            match_id,
            3,
            1,
            8,
            "Shot",
            home_team,
            12,
            "Haaland Sample",
            [108, 40],
            shot={"statsbomb_xg": 0.32, "outcome": {"name": "Goal"}, "type": {"name": "Open Play"}},
        ),
        _event(match_id, 4, 1, 18, "Pressure", away_team, 20, "Mbappe Sample", [55, 30]),
        _event(
            match_id,
            5,
            1,
            32,
            "Duel",
            away_team,
            20,
            "Mbappe Sample",
            [70, 62],
            duel={"type": {"name": "Aerial Lost"}, "outcome": {"name": "Lost Out"}},
        ),
        _event(match_id, 6, 1, 44, "Pass", away_team, 20, "Mbappe Sample", [42, 20]),
        _event(
            match_id,
            7,
            2,
            58,
            "Goal Keeper",
            away_team,
            21,
            "Keeper Sample",
            [5, 40],
            goalkeeper={"type": {"name": "Shot Saved"}, "outcome": {"name": "Success"}},
        ),
        _event(
            match_id,
            8,
            2,
            74,
            "Shot",
            away_team,
            20,
            "Mbappe Sample",
            [103, 33],
            shot={"statsbomb_xg": 0.12, "outcome": {"name": "Saved"}, "type": {"name": "Open Play"}},
        ),
        _event(match_id, 9, 2, 82, "Pressure", home_team, 11, "Valverde Sample", [62, 52]),
        _event(
            match_id,
            10,
            2,
            88,
            "Shot",
            home_team,
            11,
            "Valverde Sample",
            [92, 46],
            shot={"statsbomb_xg": 0.06, "outcome": {"name": "Off T"}, "type": {"name": "Free Kick"}},
        ),
    ]
    return rows


def fallback_three_sixty(match_id: int) -> list[dict]:
    return [
        {
            "event_uuid": f"sample-{match_id}-3",
            "visible_area": [0, 0, 120, 0, 120, 80, 0, 80],
            "freeze_frame": [
                {"teammate": True, "actor": True, "keeper": False, "location": [108, 40]},
                {"teammate": False, "actor": False, "keeper": True, "location": [116, 40]},
            ],
        }
    ]


def _event(
    match_id: int,
    idx: int,
    period: int,
    minute: int,
    event_type: str,
    team: dict,
    player_id: int,
    player_name: str,
    location: list[float],
    shot: dict | None = None,
    duel: dict | None = None,
    goalkeeper: dict | None = None,
) -> dict:
    event = {
        "id": f"sample-{match_id}-{idx}",
        "index": idx,
        "period": period,
        "timestamp": f"00:{minute % 60:02d}:00.000",
        "minute": minute,
        "second": 0,
        "type": {"id": idx, "name": event_type},
        "possession": max(1, idx // 2),
        "possession_team": team,
        "team": team,
        "player": {"id": player_id, "name": player_name},
        "position": {"id": 13, "name": "Center Midfield"},
        "location": location,
        "play_pattern": {"id": 1, "name": "Regular Play"},
    }
    if event_type == "Pass":
        event["pass"] = {"end_location": [location[0] + 18, location[1]], "outcome": None}
    if event_type == "Carry":
        event["carry"] = {"end_location": [location[0] + 12, location[1] + 3]}
    if shot:
        event["shot"] = shot
    if duel:
        event["duel"] = duel
    if goalkeeper:
        event["goalkeeper"] = goalkeeper
    return event
