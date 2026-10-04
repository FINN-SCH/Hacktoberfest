"""Manual UI smoke check. Requires the optional playwright package and local Microsoft Edge.
Runs the built SPA with temporary SQLite and fake providers; never calls real APIs.
Usage: backend/.venv/Scripts/python.exe frontend/scripts/smoke_browser.py
"""
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import wave

ROOT = Path(__file__).resolve().parents[2]
SERVER = r'''
import io, json, os, wave
from app.main import create_app
from app.config import Settings
from app.providers.interfaces import CompletionResult,TranscriptionResult,SpeechResult
from test_turns import GOOD
import app.main as main
class Fake:
    def __init__(self): self.llm=self;self.stt=self;self.tts=self
    async def aclose(self): pass
    async def transcribe(self,audio,language): return TranscriptionResult("Ich habe nach Berlin gegangen.","fake","fake",1)
    async def synthesize(self,text,language):
        b=io.BytesIO()
        with wave.open(b,"wb") as f: f.setnchannels(1);f.setsampwidth(2);f.setframerate(16000);f.writeframes(b"\x00\x00"*1600)
        return SpeechResult(b.getvalue(),"audio/wav","fake","fake",1)
    async def complete(self,messages,*,schema,purpose):
        context=json.loads(messages[1]["content"]) if purpose!="turn" else {}
        if purpose=="turn": out=GOOD
        elif purpose=="report":
            enough=context["scores"]["sufficient_sample"]
            out={"vocab_rating":3 if enough else None,
                "vocab_evidence":[{"turn_id":context["eligible_transcripts"][0]["turn_id"],"quote":"Berlin","explanation":"A place name."}] if enough else [],
                "summary":{"weaknesses":["Auxiliary choice"],"next_focus":"Practise sein with movement."}}
        elif purpose=="quiz":
            out={"questions":[{"id":"q1","source_mistake_id":context["required_recent_source_id"],"kind":"mc",
                "question":"Ich ___ nach Berlin gegangen.","options":[{"id":"a","text":"bin"},{"id":"b","text":"habe"}],
                "correct_option_id":"a","accepted_answers":[],"explanation":"Use sein.","ambiguous":False}]}
        else:
            out={"summary":"Auxiliary choice recurs.","strengths":[{"text":"Regular practice","evidence":"Two sessions"}],
                 "focus_areas":[{"topic":"de_perfekt_auxiliary","why":"Repeated auxiliary errors","tip":"Use sein with gehen.",
                                "example_mistake_ids":[context["mistakes"][0]["id"]]}]}
        return CompletionResult(json.dumps(out),"fake","fake",1)
main.build_providers=lambda _:Fake()
app=create_app(Settings(_env_file=None,db_path=os.environ["SMOKE_DB"]))
import uvicorn
server=uvicorn.Server(uvicorn.Config(app,host="127.0.0.1",port=int(os.environ["SMOKE_PORT"]),log_level="error"))
@app.post("/__smoke_shutdown")
async def shutdown():
    server.should_exit=True
    return {"ok":True}
server.run()
'''

def run():
    from playwright.sync_api import sync_playwright, expect
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0));port=sock.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix="tutor-smoke-",dir=ROOT/"backend"/".venv") as tmp:
        env={**os.environ,"PYTHONPATH":str(ROOT/"backend")+os.pathsep+str(ROOT/"backend"/"tests"),
             "SMOKE_DB":str(Path(tmp)/"test.db"),"SMOKE_PORT":str(port)}
        server=subprocess.Popen([sys.executable,"-c",SERVER],cwd=ROOT/"backend",env=env,
                                stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        url=f"http://127.0.0.1:{port}"
        try:
            for _ in range(100):
                try:
                    with urllib.request.urlopen(url+"/api/health",timeout=1) as response:
                        if response.status==200: break
                except Exception: time.sleep(.1)
            else: raise RuntimeError("Smoke server did not start")
            with sync_playwright() as p:
                browser=p.chromium.launch(channel="msedge",headless=True,args=[
                    "--use-fake-device-for-media-stream","--use-fake-ui-for-media-stream"])
                context=browser.new_context(viewport={"width":1280,"height":900},permissions=["microphone"])
                page=context.new_page();errors=[]
                page.on("pageerror",lambda e:errors.append(str(e)))
                page.goto(url);page.wait_for_load_state("networkidle")
                print("Initial UI:",page.get_by_role("heading",level=1).inner_text())
                page.get_by_label("Your name").fill("Smoke learner")
                page.get_by_role("button",name="Create profile",exact=True).click()
                expect(page.get_by_role("heading",name="Make room for conversation.")).to_be_visible()
                expect(page.get_by_role("button",name="Start conversation",exact=True)).to_be_enabled(timeout=30000)
                def fail_start(route):
                    route.fulfill(status=502,content_type="application/json",body=json.dumps({"error":{"code":"unavailable","message":"Temporary startup failure","retryable":True}}))
                page.route("**/api/sessions",fail_start)
                page.get_by_role("button",name="Start conversation",exact=True).click()
                expect(page.get_by_role("alert")).to_contain_text("Temporary startup failure")
                page.unroute("**/api/sessions",fail_start)
                page.get_by_role("button",name="Start conversation",exact=True).click()
                expect(page.get_by_text("Your turn. Speak when you’re ready.",exact=True)).to_be_visible(timeout=30000)
                page.get_by_role("button",name="Pause microphone").click()
                print("VAD model loaded; opening WAV played; listening then pause verified")
                page.get_by_role("button",name="End session",exact=True).click()
                expect(page.get_by_role("heading",name="Session report",exact=True)).to_be_visible(timeout=15000)
                expect(page.get_by_text("Not enough speech yet.",exact=False)).to_be_visible()
                profiles=context.request.get(url+"/api/profiles").json();pid=profiles[0]["id"]
                for _ in range(2):
                    created=context.request.post(url+"/api/sessions",data={"profile_id":pid,"target_language":"de",
                        "explanation_mode":"native","level":"A2","scenario":"cafe"}).json()
                    sid=created["session"]["id"]
                    for i in range(5):
                        response=context.request.post(url+f"/api/sessions/{sid}/turns",multipart={
                            "client_turn_id":str(i),"speech_span_ms":"15000","voiced_ms":"12000","pause_ms":"3000",
                            "audio":{"name":"turn.wav","mimeType":"audio/wav","buffer":b"test"}})
                        assert response.ok,response.text()
                    assert context.request.post(url+f"/api/sessions/{sid}/end").ok
                page.get_by_role("button",name="History",exact=True).click()
                expect(page.get_by_role("button",name="View report",exact=True)).to_have_count(3)
                page.get_by_role("button",name="View report",exact=True).first.click()
                expect(page.get_by_text("Practise sein with movement.",exact=True)).to_be_visible()
                page.get_by_role("button",name="Not a mistake",exact=True).first.click()
                expect(page.get_by_text("1 exclusions since this summary",exact=False)).to_be_visible()
                page.get_by_role("button",name="Regenerate",exact=True).click()
                expect(page.get_by_text("1 exclusions since this summary",exact=False)).to_have_count(0)
                page.get_by_role("button",name="Quiz",exact=True).click()
                page.get_by_role("button",name="Create my quiz",exact=True).click()
                expect(page.get_by_role("radio",name="bin",exact=True)).to_be_visible()
                assert page.get_by_text("Practising this because",exact=False).count()==0
                page.get_by_role("radio",name="bin",exact=True).check()
                page.get_by_role("button",name="Check answers",exact=True).click()
                expect(page.get_by_text("1 of 1 correct.",exact=False)).to_be_visible()
                expect(page.get_by_text("Practising this because",exact=False)).to_be_visible()
                page.get_by_role("button",name="Analysis",exact=True).click()
                expect(page.get_by_role("heading",name="Topics to watch",exact=True)).to_be_visible()
                expect(page.get_by_text("Auxiliary choice recurs.",exact=True)).to_be_visible()
                expect(page.locator(".recharts-surface").first).to_be_visible()
                for tab in ["History","Quiz","Analysis"]:
                    page.set_viewport_size({"width":375,"height":812})
                    page.get_by_role("button",name=tab,exact=True).click()
                    page.wait_for_load_state("networkidle")
                    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"),tab+" overflows"
                page.screenshot(path=str(Path(tmp)/"mobile.png"),full_page=True)
                assert not errors,errors
                print("PASS: profile, VAD/opening playback, end/report, history, exclusion/regeneration, quiz and analysis")
                print("PASS: 375px pages fit viewport; no browser page errors")
                browser.close()
        finally:
            try:
                urllib.request.urlopen(urllib.request.Request(url+"/__smoke_shutdown",data=b"",method="POST"),timeout=5).close()
                server.wait(timeout=10)
            except Exception:
                server.terminate();server.wait(timeout=10)
if __name__=="__main__": run()
