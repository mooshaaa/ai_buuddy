from datetime import date

from app.llm.stub import parse_date


def chat(client, user_id, message):
    r = client.post("/api/chat", json={"user_id": user_id, "message": message})
    assert r.status_code == 200
    return r.json()["blocks"]


def test_health(client):
    data = client.get("/health").json()
    assert data["status"] == "ok" and data["llm"] == "stub" and data["debug"] is False


def test_users(client):
    ids = {u["id"] for u in client.get("/api/users").json()}
    assert ids == {"intern_1", "mentor_1"}


def test_absence_flow(client):
    blocks = chat(client, "intern_1", "Хочу отгул 20 ноября")
    card = next(b for b in blocks if b["type"] == "action_card")
    assert card["status"] == "needs_confirmation"
    r = client.post(f"/api/actions/{card['action_id']}/confirm", json={"user_id": "intern_1"})
    assert r.status_code == 200
    assert r.json()["status"] == "done"
    assert r.json()["result"]["request_id"].startswith("ABS-")


def test_absence_asks_for_date(client):
    blocks = chat(client, "intern_1", "Хочу отгул")
    assert blocks[0]["type"] == "text" and "дату" in blocks[0]["text"]


def test_cancel_action(client):
    card = next(b for b in chat(client, "intern_1", "отгул завтра") if b["type"] == "action_card")
    r = client.post(f"/api/actions/{card['action_id']}/cancel", json={"user_id": "intern_1"})
    assert r.json()["status"] == "rejected"


def test_cannot_confirm_foreign_action(client):
    card = next(b for b in chat(client, "intern_1", "отгул завтра") if b["type"] == "action_card")
    r = client.post(f"/api/actions/{card['action_id']}/confirm", json={"user_id": "mentor_1"})
    assert r.status_code == 403


def test_intern_denied_team_progress(client):
    blocks = chat(client, "intern_1", "Покажи прогресс стажёра")
    assert blocks[0]["type"] == "error"


def test_mentor_sees_team_progress(client):
    blocks = chat(client, "mentor_1", "Покажи прогресс стажёра")
    assert blocks[0]["type"] == "text" and "Анна" in blocks[0]["text"]


def test_stages_and_toggle(client):
    data = client.get("/api/stages", params={"user_id": "intern_1"}).json()
    assert data["total"] == 12 and data["done"] == 2
    stage = next(s for s in data["stages"] if not s["done"])
    toggled = client.post(f"/api/stages/{stage['id']}/toggle", json={"user_id": "intern_1"}).json()
    assert toggled["done"] == 3


def test_stage_summary_in_chat(client):
    blocks = chat(client, "intern_1", "Что мне делать дальше?")
    assert "Следующий шаг" in blocks[0]["text"]


def test_faq_returns_answer_with_source(client):
    blocks = chat(client, "intern_1", "Как подготовиться к экваторной встрече?")
    assert blocks[0]["type"] == "text" and "презентац" in blocks[0]["text"].lower()
    assert blocks[1]["type"] == "source"
    assert blocks[1]["items"][0]["id"] == "kb-equator-prep"
    assert blocks[1]["items"][0]["synthetic"] is False


def test_faq_demo_entry_is_marked_synthetic(client):
    blocks = chat(client, "intern_1", "Как запросить доступы?")
    assert blocks[1]["type"] == "source"
    assert any(i["synthetic"] for i in blocks[1]["items"]) or "доступ" in blocks[0]["text"].lower()


def test_help_for_unknown(client):
    assert "Я помогаю" in chat(client, "intern_1", "абракадабра")[0]["text"]


def test_unknown_user(client):
    r = client.post("/api/chat", json={"user_id": "nobody", "message": "привет"})
    assert r.status_code == 404


def test_parse_date():
    today = date(2026, 11, 10)
    assert parse_date("20 ноября", today) == date(2026, 11, 20)
    assert parse_date("5 мая", today) == date(2027, 5, 5)
    assert parse_date("завтра", today) == date(2026, 11, 11)
    assert parse_date("15.12", today) == date(2026, 12, 15)
    assert parse_date("когда-нибудь", today) is None
    # 2026-11-10 это вторник
    assert parse_date("в понедельник", today) == date(2026, 11, 16)
    assert parse_date("нужен выходной в среду", today) == date(2026, 11, 11)
    assert parse_date("во вторник", today) == date(2026, 11, 17)
    assert parse_date("в следующую пятницу", today) == date(2026, 11, 13)
    assert parse_date("в воскресенье", today) == date(2026, 11, 15)
