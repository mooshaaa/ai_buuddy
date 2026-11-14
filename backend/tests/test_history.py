import app.main as main_module
from app import history
from app.db import SessionLocal
from app.models import Message


def chat(client, user_id, message):
    r = client.post("/api/chat", json={"user_id": user_id, "message": message})
    assert r.status_code == 200
    return r.json()


def hist(client, user_id):
    r = client.get("/api/history", params={"user_id": user_id})
    assert r.status_code == 200
    return r.json()["messages"]


def test_messages_are_saved_and_restored_in_order(client):
    chat(client, "intern_1", "Что мне делать дальше?")
    chat(client, "intern_1", "Как подготовиться к экваторной встрече?")
    msgs = hist(client, "intern_1")
    assert [m["role"] for m in msgs] == ["user", "bot", "user", "bot"]
    assert msgs[0]["blocks"][0]["text"] == "Что мне делать дальше?"
    assert msgs[3]["blocks"][1]["type"] == "source"


def test_history_is_per_user(client):
    chat(client, "intern_1", "Что мне делать дальше?")
    assert hist(client, "mentor_1") == []


def test_provider_receives_previous_turns(client, monkeypatch):
    seen = []

    class Recorder:
        def parse(self, user, message, history=None):
            seen.append(history)
            from app.llm.base import Intent
            return Intent("unknown")

    monkeypatch.setattr(main_module, "get_provider", lambda: Recorder())
    chat(client, "intern_1", "первое")
    chat(client, "intern_1", "второе")
    assert seen[0] == []
    assert [t["role"] for t in seen[1]] == ["user", "assistant"]
    assert seen[1][0]["text"] == "первое" and seen[1][1]["text"].startswith("Я помогаю")


def test_context_limited_to_last_8_and_truncated(client):
    with SessionLocal() as db:
        for i in range(6):
            history.save_turn(db, "intern_1", f"вопрос {i} " + "x" * 3000, [{"type": "text", "text": f"ответ {i}"}])
        turns = history.load(db, "intern_1")
    assert len(turns) == 8
    assert turns[-1]["text"] == "ответ 5" and turns[0]["text"].startswith("вопрос 2")
    assert all(len(t["text"]) <= 1500 for t in turns)


def test_reset_archives_but_keeps_rows(client):
    chat(client, "intern_1", "Что мне делать дальше?")
    r = client.post("/api/history/reset", json={"user_id": "intern_1"})
    assert r.json() == {"status": "ok", "archived": 2}
    assert hist(client, "intern_1") == []
    with SessionLocal() as db:
        assert history.load(db, "intern_1") == []
        assert db.query(Message).filter(Message.user_id == "intern_1").count() == 2
    chat(client, "intern_1", "Что мне делать дальше?")
    assert len(hist(client, "intern_1")) == 2


def test_reset_unknown_user(client):
    assert client.post("/api/history/reset", json={"user_id": "nobody"}).status_code == 404
    assert client.get("/api/history", params={"user_id": "nobody"}).status_code == 404


def test_restored_card_shows_current_status(client):
    data = chat(client, "intern_1", "Хочу отгул 20 ноября")
    card = next(b for b in data["blocks"] if b["type"] == "action_card")
    assert card["status"] == "needs_confirmation"
    client.post(f"/api/actions/{card['action_id']}/confirm", json={"user_id": "intern_1"})
    restored = next(b for b in hist(client, "intern_1")[1]["blocks"] if b["type"] == "action_card")
    assert restored["status"] == "done" and restored["result"]["request_id"].startswith("ABS-")


def test_date_followup_after_bot_asks(client):
    first = chat(client, "intern_1", "Хочу отгул")
    assert first["blocks"][0]["text"].startswith("На какую дату")
    second = chat(client, "intern_1", "20 ноября")
    card = next(b for b in second["blocks"] if b["type"] == "action_card")
    assert card["params"]["date"].endswith("-11-20") and card["params"]["kind"] == "day_off"


def test_vacation_followup_keeps_kind(client):
    chat(client, "intern_1", "Хочу отпуск")
    card = next(b for b in chat(client, "intern_1", "завтра")["blocks"] if b["type"] == "action_card")
    assert card["params"]["kind"] == "vacation"


def test_plain_date_without_question_is_not_absence(client):
    blocks = chat(client, "intern_1", "20 ноября")["blocks"]
    assert blocks[0]["type"] == "text" and blocks[0]["text"].startswith("Я помогаю")


def test_render_skips_errors_and_summarizes_cards():
    text = history.render([
        {"type": "error", "text": "сбой"},
        {"type": "text", "text": "привет"},
        {"type": "action_card", "title": "Заявка на отгул", "params": {"date": "2026-11-20"}},
        {"type": "source", "items": [{"title": "Выпускной"}]},
    ])
    assert "сбой" not in text and "привет" in text
    assert "Заявка на отгул" in text and "2026-11-20" in text and "[источники: Выпускной]" in text


def test_error_only_reply_not_in_context(client):
    with SessionLocal() as db:
        history.save_turn(db, "intern_1", "вопрос", [{"type": "error", "text": "сбой"}])
        turns = history.load(db, "intern_1")
    assert turns == [{"role": "user", "text": "вопрос"}]


def test_debug_trace_has_history_len(client, monkeypatch):
    import dataclasses
    monkeypatch.setattr(main_module, "settings", dataclasses.replace(main_module.settings, debug=True))
    chat(client, "intern_1", "Что мне делать дальше?")
    assert chat(client, "intern_1", "Что мне делать дальше?")["debug"]["history_len"] == 2
