import dataclasses

import app.main as main_module
from app import debuglog


def _debug(monkeypatch, value):
    monkeypatch.setattr(main_module, "settings", dataclasses.replace(main_module.settings, debug=value))


def test_debug_off_hides_info_and_events(client, monkeypatch):
    _debug(monkeypatch, False)
    r = client.post("/api/chat", json={"user_id": "intern_1", "message": "Что мне делать дальше?"})
    assert r.json()["debug"] is None
    assert client.get("/api/debug/events").status_code == 404


def test_debug_on_returns_trace_and_events(client, monkeypatch):
    _debug(monkeypatch, True)
    debuglog.clear()
    r = client.post("/api/chat", json={"user_id": "intern_1", "message": "Что мне делать дальше?"})
    dbg = r.json()["debug"]
    assert dbg["intent"] == "show_stages" and dbg["source"] == "stub" and dbg["latency_ms"] >= 0
    events = client.get("/api/debug/events").json()
    assert events[0]["user"] == "intern_1" and events[0]["intent"] == "show_stages"
