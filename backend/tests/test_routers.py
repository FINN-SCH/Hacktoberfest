"""HTTP contracts with real SQLite/services and deterministic providers."""
import json
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.providers.interfaces import CompletionResult, TranscriptionResult, SpeechResult
from app.providers.errors import ProviderError
from test_turns import GOOD

class Providers:
    def __init__(self):
        self.llm=self; self.stt=self; self.tts=self
        self.closed=False; self.fail_analysis=False; self.stt_calls=0
    async def complete(self,messages,*,schema,purpose):
        if self.fail_analysis:
            raise ProviderError("unavailable","llm",retryable=True)
        output = GOOD if purpose=="turn" else {"vocab_rating":None,"vocab_evidence":[],
            "summary":{"weaknesses":[],"next_focus":"Speak a little longer next time."}}
        return CompletionResult(json.dumps(output),"fake","fake",1)
    async def transcribe(self,wav_bytes,language):
        self.stt_calls+=1
        return TranscriptionResult("Ich habe nach Berlin gegangen.","fake","fake",1)
    async def synthesize(self,text,language):
        return SpeechResult(b"test-audio","audio/mpeg","fake","fake",1)
    async def aclose(self):
        self.closed=True

@pytest.fixture
def client(tmp_path,monkeypatch):
    provider=Providers()
    monkeypatch.setattr("app.main.build_providers",lambda settings:provider)
    app=create_app(Settings(_env_file=None,db_path=tmp_path/"db.sqlite"))
    with TestClient(app) as client:
        yield client,provider
    assert provider.closed

def start(client):
    p=client.post("/api/profiles",json={"name":"Learner","native_language":"en","default_explanation_mode":"native"})
    assert p.status_code==201
    s=client.post("/api/sessions",json={"profile_id":p.json()["id"],"target_language":"de",
        "explanation_mode":"native","level":"A2","scenario":"cafe"})
    assert s.status_code==201
    return p.json(),s.json()

def test_http_session_transcript_exclusion_and_report(client):
    c,provider=client;p,started=start(c);sid=started["session"]["id"]
    assert c.post(f"/api/turns/{started['opening_turn_id']}/speech").content==b"test-audio"
    timing={"client_turn_id":"stable-1","speech_span_ms":"15000","voiced_ms":"12000","pause_ms":"3000"}
    turn=c.post(f"/api/sessions/{sid}/turns",data=timing,files={"audio":("turn.wav",b"wav","audio/wav")})
    assert turn.status_code==200,turn.text
    saved=turn.json();tid=saved["turn_id"]
    assert c.get(f"/api/sessions/{sid}/turns/by-client/stable-1").json()==saved
    assert len(c.get(f"/api/sessions/{sid}/turns").json())==2
    assert c.post(f"/api/mistakes/{saved['corrections'][0]['id']}/not-a-mistake").json()["status"]=="excluded"
    result=c.post(f"/api/sessions/{sid}/end")
    assert result.status_code==200 and result.json()["snapshot_status"]=="ok"
    assert result.json()["scores"]["grammar"]["error_count"]==0
    assert c.get(f"/api/profiles/{p['id']}/sessions").json()[0]["id"]==sid
    assert c.get(f"/api/profiles/{p['id']}/analysis?language=de").json()["session_count"]==1
    assert c.post(f"/api/turns/{tid}/misheard").json()["misheard"]

def test_http_analysis_retry_without_audio_and_validation_envelope(client):
    c,provider=client;p,s=start(c);sid=s["session"]["id"]
    timing={"client_turn_id":"retry-1","speech_span_ms":15000,"voiced_ms":12000,"pause_ms":3000}
    provider.fail_analysis=True
    failed=c.post(f"/api/sessions/{sid}/turns",data=timing,files={"audio":("turn.wav",b"wav","audio/wav")})
    assert failed.status_code==502 and failed.json()["error"]["stage"]=="analysis"
    provider.fail_analysis=False
    retried=c.post(f"/api/sessions/{sid}/turns",data=timing)
    assert retried.status_code==200 and provider.stt_calls==1
    conflict=c.post(f"/api/sessions/{sid}/turns",data={**timing,"pause_ms":2999})
    assert conflict.status_code==409 and conflict.json()["error"]["code"]=="turn_conflict"
    invalid=c.post(f"/api/sessions/{sid}/turns",data={})
    assert invalid.status_code==422 and invalid.json()["error"]["stage"]=="request"

def test_openapi_does_not_initialize_providers(monkeypatch,tmp_path):
    def forbidden(*args): raise AssertionError("providers initialized during export")
    monkeypatch.setattr("app.main.build_providers",forbidden)
    monkeypatch.setattr("app.main.make_engine",forbidden)
    app=create_app(Settings(_env_file=None,db_path=tmp_path/"absent.db"))
    assert "/api/quizzes" in app.openapi()["paths"]
    assert not (tmp_path/"absent.db").exists()
