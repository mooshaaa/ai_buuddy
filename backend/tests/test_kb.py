import json

import httpx
import pytest

from app import agent, kb
from app.db import SessionLocal
from app.llm.base import Intent, KbResult
from app.llm.fallback import FallbackProvider
from app.llm.openai_compat import LLMError, OpenAICompatProvider
from app.llm.stub import StubProvider
from app.models import User

INTERN = User(id="intern_1", name="Анна", role="intern")
MENTOR = User(id="mentor_1", name="Игорь", role="mentor")


def reply(content):
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def make(handler, **kw):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OpenAICompatProvider("https://api.example/v1", "k", "main", client=client, **kw)


# ---------- база знаний и поиск ----------

def test_search_finds_relevant_entries():
    assert kb.search("Как подготовиться к экватору?", kb.ENTRIES).id == "kb-equator-prep"
    assert kb.search("что за 1:1", kb.ENTRIES).id in {"kb-org-week1", "kb-interim"}
    assert kb.search("где политика по защите персональных данных", kb.ENTRIES).id == "kb-data"
    assert kb.search("абракадабра", kb.ENTRIES) is None
    assert kb.search("111", kb.ENTRIES) is None


def test_role_filter():
    intern_ids = {e.id for e in kb.for_role("intern")}
    mentor_ids = {e.id for e in kb.for_role("mentor")}
    assert "kb-equator-mentor" not in intern_ids and "kb-equator-mentor" in mentor_ids
    assert intern_ids < mentor_ids


def test_entries_are_well_formed():
    ids = [e.id for e in kb.ENTRIES]
    assert len(ids) == len(set(ids))
    assert all(e.text and e.source and e.tags for e in kb.ENTRIES)
    assert all(e.source.startswith("Демо") for e in kb.ENTRIES if e.synthetic)
    assert "[kb-data]" in kb.format_for_prompt(kb.ENTRIES)
    assert kb.get("nope") is None


# ---------- заглушка ----------

def test_stub_answer():
    res = StubProvider().answer(INTERN, "Что такое экватор?", kb.for_role("intern"))
    assert res.found and res.source_ids and res.source == "stub"
    assert not StubProvider().answer(INTERN, "курс валют", kb.for_role("intern")).found


def test_stub_does_not_leak_mentor_only_entry_to_intern():
    q = "что должен сделать наставник: бриф, напутственное слово, репетиция"
    res = StubProvider().answer(INTERN, q, kb.for_role("intern"))
    assert "kb-equator-mentor" not in res.source_ids
    assert StubProvider().answer(MENTOR, q, kb.for_role("mentor")).source_ids == ["kb-equator-mentor"]


# ---------- LLM ----------

GOOD = '{"found": true, "answer": "Посмотри мастер-классы.", "sources": ["kb-equator-prep"]}'


def test_llm_answer_ok_and_prompt_has_kb():
    seen = {}

    def handler(request):
        seen["body"] = json.loads(request.content)
        return reply(GOOD)

    res = make(handler).answer(INTERN, "Как подготовиться к экватору?", kb.for_role("intern"))
    assert res.found and res.source_ids == ["kb-equator-prep"] and res.source == "llm" and res.model == "main"
    user_msg = seen["body"]["messages"][1]["content"]
    assert "[kb-equator-prep]" in user_msg and "ВОПРОС ПОЛЬЗОВАТЕЛЯ: Как подготовиться" in user_msg
    assert "[kb-equator-mentor]" not in user_msg  # записи только для наставника не уходят стажёру


def test_llm_hallucinated_source_is_rejected():
    bad = '{"found": true, "answer": "Выдумка", "sources": ["kb-does-not-exist"]}'
    assert not make(lambda r: reply(bad)).answer(INTERN, "вопрос", kb.for_role("intern")).found


def test_llm_found_without_sources_is_rejected():
    bad = '{"found": true, "answer": "Ответ без источников", "sources": []}'
    assert not make(lambda r: reply(bad)).answer(INTERN, "вопрос", kb.for_role("intern")).found


def test_llm_not_found_and_nulls():
    res = make(lambda r: reply('{"found": false, "answer": null, "sources": null}')).answer(
        INTERN, "курс валют", kb.for_role("intern"))
    assert not res.found


def test_llm_mixed_sources_keeps_only_known():
    mixed = '{"found": true, "answer": "Ответ", "sources": ["kb-data", "fake", "kb-data"]}'
    res = make(lambda r: reply(mixed)).answer(INTERN, "данные", kb.for_role("intern"))
    assert res.source_ids == ["kb-data"]


def test_llm_answer_retries_then_fails():
    calls = []

    def handler(request):
        calls.append(1)
        return reply("не json")

    with pytest.raises(LLMError):
        make(handler).answer(INTERN, "вопрос", kb.for_role("intern"))
    assert len(calls) == 2


def test_fallback_answer_uses_stub_on_failure():
    prov = FallbackProvider(make(lambda r: httpx.Response(500)), StubProvider())
    res = prov.answer(INTERN, "Что такое экватор?", kb.for_role("intern"))
    assert res.found and res.source == "stub" and res.note


def test_fallback_answer_passes_primary_result():
    prov = FallbackProvider(make(lambda r: reply(GOOD)), StubProvider())
    assert prov.answer(INTERN, "экватор", kb.for_role("intern")).source == "llm"


# ---------- агент ----------

class FakeProvider:
    def __init__(self, result=None, error=None):
        self.result, self.error = result, error

    def parse(self, user, message):
        return Intent("faq")

    def answer(self, user, question, entries):
        if self.error:
            raise self.error
        return self.result


def run_agent(client, user, provider):
    trace = {}
    with SessionLocal() as db:
        blocks = agent.handle_message(db, user, "вопрос", provider, trace)
    return blocks, trace


def test_agent_not_found_gives_escalation_text(client):
    blocks, trace = run_agent(client, INTERN, FakeProvider(KbResult(found=False)))
    assert len(blocks) == 1 and "наставника" in blocks[0].text and "куратора" in blocks[0].text
    assert trace["kb_found"] is False
    blocks, _ = run_agent(client, MENTOR, FakeProvider(KbResult(found=False)))
    assert "куратора" in blocks[0].text and "наставника" not in blocks[0].text


def test_agent_answer_has_source_block_and_trace(client):
    res = KbResult(found=True, text="Текст", source_ids=["kb-data", "kb-demo-access"], source="llm", model="m")
    blocks, trace = run_agent(client, INTERN, FakeProvider(res))
    assert blocks[0].text == "Текст" and blocks[1].type == "source"
    assert [i.id for i in blocks[1].items] == ["kb-data", "kb-demo-access"]
    assert blocks[1].items[1].synthetic is True
    assert trace["kb_sources"] == ["kb-data", "kb-demo-access"] and trace["answer_model"] == "m"
    assert trace["latency_ms"] >= 0


def test_agent_answer_error_is_graceful(client):
    blocks, trace = run_agent(client, INTERN, FakeProvider(error=RuntimeError("boom")))
    assert blocks[0].type == "error" and trace["kb_found"] is False
