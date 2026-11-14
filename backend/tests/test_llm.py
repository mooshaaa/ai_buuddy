import dataclasses
import json
from datetime import date

import httpx
import pytest

import app.llm as llm_module
from app.llm.base import Intent
from app.llm.fallback import FallbackProvider
from app.llm.openai_compat import LLMError, OpenAICompatProvider, extract_json
from app.llm.stub import StubProvider
from app.models import User

USER = User(id="intern_1", name="Анна", role="intern")
TODAY = date(2026, 11, 11)
ABSENCE = '{"intent": "create_absence", "params": {"date": "2026-11-20", "kind": "day_off"}}'


def reply(content):
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def make(handler, **kw):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OpenAICompatProvider("https://api.example/v1/", "secret", "main", client=client, today=lambda: TODAY, **kw)


def test_valid_absence_and_request_shape():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers["authorization"]
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return reply(ABSENCE)

    intent = make(handler).parse(USER, "Хочу отгул 20 ноября")
    assert intent.name == "create_absence" and intent.params == {"date": "2026-11-20", "kind": "day_off"}
    assert seen["auth"] == "Bearer secret"
    assert seen["url"] == "https://api.example/v1/chat/completions"
    assert seen["body"]["response_format"] == {"type": "json_object"}
    assert seen["body"]["messages"][1]["content"] == "Хочу отгул 20 ноября"
    assert "2026-11-11" in seen["body"]["messages"][0]["content"]


def test_json_wrapped_in_markdown():
    p = make(lambda r: reply('Вот ответ:\n```json\n{"intent": "show_stages", "params": {}}\n```'))
    assert p.parse(USER, "что дальше?").name == "show_stages"


def test_retry_on_invalid_json():
    calls = []

    def handler(request):
        calls.append(1)
        return reply("не json") if len(calls) == 1 else reply(ABSENCE)

    assert make(handler).parse(USER, "отгул 20 ноября").name == "create_absence"
    assert len(calls) == 2


def test_fallback_model_on_rate_limit():
    models = []

    def handler(request):
        model = json.loads(request.content)["model"]
        models.append(model)
        return httpx.Response(429, json={}) if model == "main" else reply(ABSENCE)

    p = make(handler, fallback_model="backup")
    intent = p.parse(USER, "отгул 20 ноября")
    assert intent.name == "create_absence" and intent.source == "llm" and intent.model == "backup"
    assert models == ["main", "backup"]


def test_all_models_fail_raises():
    with pytest.raises(LLMError):
        make(lambda r: httpx.Response(500), fallback_model="backup").parse(USER, "привет")


def test_unknown_intent_value_is_rejected():
    calls = []

    def handler(request):
        calls.append(1)
        return reply('{"intent": "delete_everything", "params": {}}')

    with pytest.raises(LLMError):
        make(handler).parse(USER, "удали всё")
    assert len(calls) == 2


def test_bad_date_from_model_is_recovered_from_message():
    p = make(lambda r: reply('{"intent": "create_absence", "params": {"date": "завтра", "kind": "oops"}}'))
    intent = p.parse(USER, "хочу отгул 20 ноября")
    assert intent.params == {"date": "2026-11-20", "kind": "day_off"}


def test_absence_without_date_stays_none():
    p = make(lambda r: reply('{"intent": "create_absence", "params": {"date": null}}'))
    assert p.parse(USER, "хочу отгул").params["date"] is None


def test_faq_intent_passes_through():
    p = make(lambda r: reply('{"intent": "faq", "params": {}}'))
    assert p.parse(USER, "Как получить доступ к Jira?").name == "faq"


def test_empty_choices_is_error():
    with pytest.raises(LLMError):
        make(lambda r: httpx.Response(200, json={"choices": []})).parse(USER, "привет")


def test_extract_json_errors():
    with pytest.raises(ValueError):
        extract_json("нет json")
    assert extract_json('текст {"a": 1} конец') == {"a": 1}


def test_fallback_provider_uses_stub_on_failure():
    class Broken:
        def parse(self, user, message, history=None):
            raise RuntimeError("down")

    fb = FallbackProvider(Broken(), StubProvider()).parse(USER, "Что мне делать дальше?")
    assert fb.name == "show_stages" and fb.source == "stub" and "down" in fb.note
    ok = Intent("faq", text="x")

    class Good:
        def parse(self, user, message, history=None):
            return ok

    assert FallbackProvider(Good(), StubProvider()).parse(USER, "привет") is ok


def _with_settings(monkeypatch, **kw):
    monkeypatch.setattr(llm_module, "settings", dataclasses.replace(llm_module.settings, **kw))
    llm_module.get_provider.cache_clear()
    try:
        return llm_module.get_provider()
    finally:
        llm_module.get_provider.cache_clear()


def test_get_provider_variants(monkeypatch):
    assert isinstance(_with_settings(monkeypatch, llm_provider="stub"), StubProvider)
    assert isinstance(_with_settings(monkeypatch, llm_provider="openai_compat", llm_api_key=""), StubProvider)
    full = _with_settings(monkeypatch, llm_provider="openai_compat", llm_base_url="https://x/v1",
                          llm_model="m", llm_api_key="k")
    assert isinstance(full, FallbackProvider)
    with pytest.raises(RuntimeError):
        _with_settings(monkeypatch, llm_provider="nope")


def test_prompt_contains_weekday_calendar():
    seen = {}

    def handler(request):
        seen["system"] = json.loads(request.content)["messages"][0]["content"]
        return reply('{"intent": "unknown", "params": {}}')

    make(handler).parse(USER, "привет")
    assert "2026-11-11 (среда)" in seen["system"]
    assert "2026-11-16 понедельник" in seen["system"]


def test_weekday_recovered_when_model_gives_no_date():
    p = make(lambda r: reply('{"intent": "create_absence", "params": {"date": null}}'))
    assert p.parse(USER, "Мне нужен выходной в понедельник").params["date"] == "2026-11-16"


def test_history_goes_into_prompt_as_data():
    seen = {}

    def handler(request):
        seen["user"] = json.loads(request.content)["messages"][1]["content"]
        return reply('{"intent": "create_absence", "params": {"date": "2026-11-25", "kind": "day_off"}}')

    history = [{"role": "user", "text": "хочу отгул"},
               {"role": "assistant", "text": "На какую дату оформить отгул?"}]
    make(handler).parse(USER, "а на 25-е?", history)
    assert "ИСТОРИЯ ДИАЛОГА" in seen["user"]
    assert "Пользователь: хочу отгул" in seen["user"] and "Помощник: На какую дату" in seen["user"]
    assert seen["user"].endswith("НОВОЕ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ: а на 25-е?")


def test_no_history_keeps_plain_message():
    seen = {}

    def handler(request):
        seen["user"] = json.loads(request.content)["messages"][1]["content"]
        return reply('{"intent": "unknown", "params": {}}')

    make(handler).parse(USER, "привет", [])
    assert seen["user"] == "привет"
