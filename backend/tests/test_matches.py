"""
Lifecycle tests for assisted mode: start -> events -> finish.

These are the guardrails for the things that are easy to get subtly wrong
and hard to notice at the table: double-scoring on a retry, the score
drifting away from the goal log, and stats being rolled up twice.
"""


def test_start_match_creates_in_progress(client, roster):
    r = client.post("/matches/start", json={
        "player1_id": roster[0], "player2_id": roster[1],
        "player3_id": roster[2], "player4_id": roster[3],
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "in_progress"
    assert data["score_blue"] == 0 and data["score_red"] == 0
    assert data["started_at"] is not None


def test_only_one_match_in_progress(client, roster, match):
    r = client.post("/matches/start", json={
        "player1_id": roster[0], "player2_id": roster[1],
        "player3_id": roster[2], "player4_id": roster[3],
    })
    assert r.status_code == 409
    assert str(match["id"]) in r.json()["detail"]


def test_duplicate_player_rejected(client, roster):
    r = client.post("/matches/start", json={
        "player1_id": roster[0], "player2_id": roster[0],
        "player3_id": roster[2], "player4_id": roster[3],
    })
    assert r.status_code == 400


def test_active_match_endpoint(client, match):
    r = client.get("/matches/active")
    assert r.status_code == 200
    assert r.json()["id"] == match["id"]


def test_no_active_match_returns_null(client):
    r = client.get("/matches/active")
    assert r.status_code == 200
    assert r.json() is None


def test_goal_event_scores(client, match, roster):
    r = client.post(f"/matches/{match['id']}/events", json={
        "team": "blue", "player_id": roster[0], "bar": "3bar",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["score"] == {"blue": 1, "red": 0}
    assert body["event"]["status"] == "confirmed"   # manual taps are confirmed
    assert body["duplicate"] is False


def test_camera_goal_is_pending_review(client, match):
    r = client.post(f"/matches/{match['id']}/events", json={
        "team": "red", "source": "camera", "confidence": 0.8,
        "detector_note": "line_crossing",
    })
    assert r.status_code == 200, r.text
    event = r.json()["event"]
    assert event["status"] == "pending_review"
    assert event["player_id"] is None
    assert event["bar"] == "unknown"
    # ...but it still counts, so the scoreboard is right with nobody watching
    assert r.json()["score"] == {"blue": 0, "red": 1}


def test_event_uuid_is_idempotent(client, match):
    payload = {"team": "blue", "event_uuid": "fixed-uuid-1", "source": "camera"}
    first = client.post(f"/matches/{match['id']}/events", json=payload)
    second = client.post(f"/matches/{match['id']}/events", json=payload)
    assert first.status_code == 200 and second.status_code == 200
    assert second.json()["duplicate"] is True
    # The retry must NOT have scored a second time.
    assert second.json()["score"] == {"blue": 1, "red": 0}
    assert len(client.get(f"/matches/{match['id']}/events").json()) == 1


def test_reject_removes_from_score(client, match):
    r = client.post(f"/matches/{match['id']}/events",
                    json={"team": "blue", "source": "camera"})
    event_id = r.json()["event"]["id"]

    r = client.patch(f"/matches/{match['id']}/events/{event_id}",
                     json={"status": "rejected"})
    assert r.status_code == 200
    assert r.json()["score"] == {"blue": 0, "red": 0}


def test_correcting_a_camera_event_confirms_it(client, match, roster):
    r = client.post(f"/matches/{match['id']}/events",
                    json={"team": "blue", "source": "camera"})
    event_id = r.json()["event"]["id"]

    r = client.patch(f"/matches/{match['id']}/events/{event_id}",
                     json={"player_id": roster[0], "bar": "5bar"})
    assert r.status_code == 200
    event = r.json()["event"]
    assert event["status"] == "confirmed"
    assert event["player_id"] == roster[0]
    assert event["bar"] == "5bar"


def test_player_not_in_match_rejected(client, match):
    other = client.post("/users/", json={"name": "spectator"}).json()
    r = client.post(f"/matches/{match['id']}/events",
                    json={"team": "blue", "player_id": other["id"]})
    assert r.status_code == 400


def test_delete_event_rewinds_score(client, match, roster):
    r = client.post(f"/matches/{match['id']}/events",
                    json={"team": "red", "player_id": roster[2]})
    event_id = r.json()["event"]["id"]
    r = client.delete(f"/matches/{match['id']}/events/{event_id}")
    assert r.status_code == 200
    assert r.json() == {"blue": 0, "red": 0}


def test_finish_derives_score_and_stats(client, match, roster):
    blue_off, blue_def, red_off, _red_def = roster
    goals = [
        {"team": "blue", "player_id": blue_off, "bar": "3bar"},
        {"team": "blue", "player_id": blue_off, "bar": "5bar"},
        {"team": "blue", "player_id": blue_def, "bar": "2bar"},
        {"team": "red", "player_id": red_off, "bar": "3bar"},
        {"team": "blue", "source": "camera"},          # unattributed
    ]
    for g in goals:
        assert client.post(f"/matches/{match['id']}/events", json=g).status_code == 200

    r = client.post(f"/matches/{match['id']}/finish", json={})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "completed"
    assert data["score_blue"] == 4 and data["score_red"] == 1
    assert data["winner_team"] == "blue"

    stats = client.get("/stats/users", params={"username": "blue_off"}).json()
    assert stats["goals"] == 2
    assert stats["goals_from_offense"] == 2
    assert stats["matches_played"] == 1
    assert stats["matches_won"] == 1

    defender = client.get("/stats/users", params={"username": "blue_def"}).json()
    assert defender["goals"] == 1
    assert defender["goals_from_defense"] == 1

    loser = client.get("/stats/users", params={"username": "red_off"}).json()
    assert loser["matches_played"] == 1
    assert loser["matches_won"] == 0


def test_own_goal_scores_for_opponent_only(client, match, roster):
    blue_off = roster[0]
    # Blue's offense puts it in their own net: RED gets the point, and it
    # lands on blue_off's own_goals, not their goals.
    r = client.post(f"/matches/{match['id']}/events", json={
        "team": "red", "player_id": blue_off, "own_goal": True,
    })
    assert r.status_code == 200
    assert r.json()["score"] == {"blue": 0, "red": 1}

    client.post(f"/matches/{match['id']}/finish", json={})
    stats = client.get("/stats/users", params={"username": "blue_off"}).json()
    assert stats["goals"] == 0
    assert stats["own_goals"] == 1


def test_finish_twice_is_rejected(client, match):
    assert client.post(f"/matches/{match['id']}/finish", json={}).status_code == 200
    assert client.post(f"/matches/{match['id']}/finish", json={}).status_code == 409


def test_no_goals_after_finish(client, match):
    client.post(f"/matches/{match['id']}/finish", json={})
    r = client.post(f"/matches/{match['id']}/events", json={"team": "blue"})
    assert r.status_code == 409


def test_abandon_skips_stat_rollup(client, match, roster):
    client.post(f"/matches/{match['id']}/events",
                json={"team": "blue", "player_id": roster[0]})
    r = client.post(f"/matches/{match['id']}/finish", json={"abandoned": True})
    assert r.status_code == 200
    assert r.json()["status"] == "abandoned"

    r = client.get("/stats/users", params={"username": "blue_off"})
    assert r.status_code == 404   # no stats row was ever created


def test_match_detail_survives_refresh(client, match, roster):
    client.post(f"/matches/{match['id']}/events",
                json={"team": "blue", "player_id": roster[0], "bar": "3bar"})
    r = client.get(f"/matches/{match['id']}")
    assert r.status_code == 200
    data = r.json()
    assert len(data["goal_events"]) == 1
    assert data["score_blue"] == 1


def test_websocket_receives_goal(client, match, roster):
    with client.websocket_connect(f"/matches/ws/{match['id']}") as ws:
        client.post(f"/matches/{match['id']}/events",
                    json={"team": "red", "player_id": roster[2]})
        message = ws.receive_json()
        assert message["type"] == "goal_added"
        assert message["score"] == {"blue": 0, "red": 1}
        assert message["event"]["team"] == "red"


def test_video_path_recorded(client, match):
    r = client.post(f"/matches/{match['id']}/video",
                    json={"video_path": "recordings/match_1.mp4"})
    assert r.status_code == 200
    assert r.json()["video_path"] == "recordings/match_1.mp4"


def test_legacy_create_still_works(client, roster):
    r = client.post("/matches/", json={
        "player1_id": roster[0], "player2_id": roster[1],
        "player3_id": roster[2], "player4_id": roster[3],
        "winner_team": "blue", "score_blue": 5, "score_red": 3,
        "player_stats": [{"user_id": roster[0], "goals": 3,
                          "goals_from_offense": 3, "goals_from_defense": 0,
                          "saves": 0}],
    })
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "completed"


def test_match_list_filters_by_status(client, match):
    r = client.get("/matches/", params={"status": "in_progress"})
    assert r.status_code == 200
    assert [m["id"] for m in r.json()] == [match["id"]]
    assert client.get("/matches/", params={"status": "completed"}).json() == []
