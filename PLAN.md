# Technical Plan

Hackathon budget: **under 24 hours, 4 developers**. This plan was drafted, then reviewed in a 4-round architecture debate between two models (Claude and Codex). It is the **agreed starting plan**: revisit a decision at hour 0 only with a concrete reason. The hour-0 spikes decide which provider and model we use.

## 1. Settled decisions

| Topic | Decision |
|---|---|
| Inference | Hosted APIs serving open-weight models. No self-hosting. |
| Languages | User-selectable; the demo claims **German + English** only (others may exist in config). |
| Corrections | Tutor speaks **one** correction out loud per turn; all detected errors shown as cards. |
| Explanation language | User's choice: native language or target language. |
| Turn-taking | Hands-free (VAD), half-duplex: mic is paused while processing and while the tutor speaks. |
| Session setup | Level picker (A1-B2) + scenario picker (cafe, job interview, doctor, free talk). |
| Stack | React + Vite + TS frontend, FastAPI backend, SQLite via SQLModel, no auth (pick a profile). |
| Ratings | Grammar, vocabulary, fluency as separate 1-5 ratings with evidence. **No overall score.** |
| Quiz | Text: multiple choice + fill-in, built only from the user's real, still-active mistakes. |
| Analysis tab | Cross-session stats (progress over sessions, recurring mistakes, mistake frequency by predefined grammar topic) + an LLM-written analysis regenerated automatically after every session. Read-only, no practice links. |
| Demo | Local laptop first; deploy only if the local demo is already stable. |

## 2. Architecture and per-turn flow

```
LISTENING -> (VAD speech end) -> PROCESSING -> SPEAKING -> LISTENING
               (+ STOPPED, ERROR states; one "Start conversation" click unlocks mic/audio)
```

Per turn:

1. Browser VAD captures a speech segment, encodes mono 16 kHz WAV, and measures timing (section 6).
2. `POST /api/sessions/{id}/turns` with the audio, a client-generated `client_turn_id` and the timing fields.
3. Backend transcribes with the language forced to the session's target language, then **saves the transcript immediately**. The backend owns the transcript; the LLM never rewrites it.
4. One LLM call receives session settings, the last ~10 turns, and the new utterance. It returns strict JSON (section 3). The backend validates it with pydantic and retries once.
5. Backend saves the corrections and reply, then returns text to the browser. Correction cards render at once.
6. Browser calls `POST /api/turns/{turn_id}/speech`. The backend builds the spoken text from **saved evidence** (the selected correction's `corrected_sentence` + reply), synthesises it, and returns audio. When playback finishes, listening resumes.

Text-to-speech is a separate call so a TTS failure never loses the transcript or the corrections, and retrying speech never reruns the tutor or duplicates mistakes.

Groq structured outputs do not support streaming, so the MVP waits for one short JSON response. No WebSockets, no token streaming.

**Latency targets** (goals, not measurements): median from end of user speech to first tutor audio < 4 s, p95 < 7 s. Tutor speech is usually one correction plus one question, about 20-40 words. Log each stage separately: endpointing, upload+STT, LLM, TTS, playback.

### Retry semantics (single process)

- Same `client_turn_id` while processing -> return `processing`.
- Same id after completion -> return the saved result, with no new provider calls.
- Failed turn -> client retries the failed stage explicitly.
- Same id with different audio -> reject (409).
- Enforced by `UNIQUE(session_id, client_turn_id)`. The frontend never auto-retries silently.

## 3. Contracts (freeze at hour 1, mock endpoints first)

### LLM output (per turn)

```json
{
  "corrections": [
    {
      "id": "c1",
      "original": "habe nach Berlin gegangen",
      "corrected": "bin nach Berlin gegangen",
      "corrected_sentence": "Ich bin nach Berlin gegangen.",
      "kind": "error",
      "topic": "de_perfekt_auxiliary",
      "explanation": "Here, gehen forms the Perfekt with sein."
    }
  ],
  "spoken_correction_id": "c1",
  "needs_clarification": false,
  "reply": "Was hast du in Berlin gemacht?"
}
```

Validation rules, enforced by the backend. Any failure means the turn's analysis fails; it never becomes an empty list:

- `original` must match a span of the saved transcript after normalisation: collapse whitespace, unify straight/curly quotes, ignore case. Umlauts and ß are kept as they are. The backend stores the transcript's actual span, not the LLM's spelling.
- `corrected_sentence` must contain `corrected`.
- `kind` is `error` or `improvement`. Improvements are shown as cards but never count as mistakes, never lower scores, and never feed quizzes.
- `topic` must come from the target language's predefined topic list below. Free-text labels can't be counted.
- `spoken_correction_id` is `null` or references a correction with `kind=error`.
- `needs_clarification=true`: the input was unclear or unfinished. The tutor asks the user to repeat, and the turn is excluded from assessment.
- Detect **all** errors and speak one. The one-spoken limit must not cap detection.

**Grammar topics (v1).** These live in `backend/app/topics.py` as id -> display label, one list per language. The team may edit the lists before hour 1, then they freeze, because the frequency table, recurring mistakes and quiz ranking all count by topic.

| German (`de_`) | English (`en_`) |
|---|---|
| `perfekt_auxiliary` Perfekt: haben vs. sein | `third_person_s` 3rd person -s |
| `past_participle` Partizip II forms | `past_simple_irregular` Irregular past forms |
| `verb_conjugation` Present-tense conjugation | `present_perfect_vs_past` Present perfect vs. past simple |
| `verb_second` Verb in second position | `continuous_vs_simple` Continuous vs. simple |
| `verb_final_subclause` Verb at the end of subordinate clauses | `future_forms` will / going to |
| `separable_verbs` Separable verbs | `question_formation` Questions and do-support |
| `modal_infinitive` Modal verb + infinitive | `subject_verb_agreement` Subject-verb agreement |
| `noun_gender` Noun gender (der/die/das) | `articles` a / an / the / no article |
| `accusative` Accusative case | `countable_uncountable` Countable vs. uncountable |
| `dative` Dative case | `prepositions` Prepositions |
| `two_way_prepositions` Two-way prepositions | `comparatives` Comparatives and superlatives |
| `preposition_choice` Preposition choice | `pronouns` Pronouns |
| `adjective_endings` Adjective endings | |
| `plural` Plural forms | |
| `pronouns` Pronouns | |
| `negation` nicht vs. kein | |

Both languages also get `vocabulary_choice` and `other`. Full ids carry the language prefix, e.g. `de_dative`, `en_articles`.

**Highlighting:** an inline highlight appears only when `original` occurs exactly once in the transcript. The card always quotes the source.

**Spoken recast:** a language template such as `"Du meinst: {corrected_sentence}"` / `"You mean: {corrected_sentence}"`, followed by `reply`. The whole utterance is in the target language, so TTS never mixes languages. Explanations stay on the cards, in the chosen explanation language.

### API

| Method | Path | Purpose |
|---|---|---|
| GET/POST | `/api/profiles` | list / create profile (name, native language, default explanation language) |
| POST | `/api/sessions` | start session: target language, explanation language, level, scenario (snapshotted). Stores the templated opening line as a tutor-only turn (`seq=0`, no transcript, never eligible) and returns its turn id, so the opening is spoken via the normal `/speech` route. |
| POST | `/api/sessions/{id}/turns` | multipart: `audio`, `client_turn_id`, `speech_span_ms`, `voiced_ms`, `pause_ms` -> turn result |
| POST | `/api/turns/{id}/speech` | synthesise saved tutor response -> audio |
| POST | `/api/turns/{id}/misheard` | exclude whole turn (its words and errors) |
| POST | `/api/mistakes/{id}/not-a-mistake` | exclude one correction |
| POST | `/api/sessions/{id}/end` | finalise; generate vocabulary rating + summary snapshot, then queue the profile analysis (background task) |
| GET | `/api/sessions/{id}/report` | transcript + computed grammar/fluency + stored snapshot + staleness label |
| POST | `/api/sessions/{id}/report/regenerate` | redo vocabulary + summary from currently eligible evidence |
| GET | `/api/profiles/{id}/sessions` | history |
| POST | `/api/quizzes` | generate quiz for profile + language (answer keys stay server-side) |
| POST | `/api/quizzes/{id}/attempts` | submit answers -> deterministic results |
| GET | `/api/profiles/{id}/analysis?language=de` | Analysis tab: computed topic table, progress per session, recurring/improving topics + latest written analysis with its labels (section 8) |

Put example request/response JSON for each in `contracts/` at hour 1. The frontend builds against mocks until the real endpoints land.

## 4. Providers and models

| Component | Choice | Notes |
|---|---|---|
| STT | Groq `whisper-large-v3`, `language=de|en`, `temperature=0` | Switch to `whisper-large-v3-turbo` only if the spike shows equal **error preservation**. |
| LLM | Groq `openai/gpt-oss-120b`, low reasoning effort, strict JSON schema | Alternative: `llama-3.3-70b-versatile` if the correction eval favours it. Same model for report and quiz. |
| TTS | DeepInfra `ResembleAI/chatterbox-multilingual` | Request parameters (language, voice) are **not documented clearly**: confirm in spike B, never guess. If it fails, Qwen3-TTS on DeepInfra becomes the MVP choice. No automatic failover. |
| VAD | `@ricky0123/vad-react` | Pin the package and serve its model/WASM assets locally. Endpointing starts at ~1.0-1.4 s silence; tune on hesitant learner speech. |

Config lives in `backend/.env`: `GROQ_API_KEY`, `DEEPINFRA_API_KEY`, `STT_MODEL`, `LLM_MODEL`, `TTS_MODEL`, provider base URLs. Keys never reach the browser. Use three small adapter modules, and no agent frameworks, vector DBs or Redis.

## 5. Data model (SQLite, SQLModel)

| Table | Key columns |
|---|---|
| `profiles` | id, name, native_language, default_explanation_language |
| `sessions` | id, profile_id, target_language, explanation_language, level, scenario (all snapshots), status, started_at, ended_at, vocab_rating, vocab_evidence_json, summary, snapshot_at, scoring_version, is_demo_data |
| `turns` | id, session_id, seq, client_turn_id (unique per session), transcript, tutor_reply, spoken_correction_id, correction_status (`pending|done|failed`), needs_clarification, misheard, speech_span_ms, voiced_ms, pause_ms, stage timings, model/prompt version |
| `mistakes` | id, profile_id, session_id, turn_id, language, topic, kind, original, corrected, corrected_sentence, explanation, status (`active|excluded`), excluded_at |
| `quizzes` | id, profile_id, language, created_at, questions_json (immutable, includes answer keys + source mistake ids) |
| `quiz_attempts` | id, quiz_id, answers_json, results_json (per item: correct / wrong / skipped_source_excluded), score, created_at |
| `profile_analyses` | id, profile_id, language, generated_at, session_count, content_json, status (`ok|failed`) |

Store text and timing only. Audio is held in memory just long enough to process and retry. Keep transactions short and never hold a write transaction open across a provider call.

## 6. Scoring

All ratings carry a sample size. Below **5 eligible turns or 60 s voiced speech**, the report shows "not enough speech yet" instead of a rating.

**Eligible turn** = `correction_status=done`, not `misheard`, not `needs_clarification`, and at least 3 words. Failed analysis is excluded from denominators, never counted as error-free. The report shows coverage, e.g. "12 of 14 turns assessed".

- **Grammar (deterministic, computed on read):** the share of eligible turns with no active `kind=error` mistakes, mapped to fixed bands. Errors per 100 eligible words is shown as supporting evidence. Dismissing a turn's last error makes the turn error-free; marking a turn Misheard removes its words and errors. Because it's computed on every read, it is never stale.
  Bands v1: >=90% -> 5, 75-89% -> 4, 55-74% -> 3, 35-54% -> 2, <35% -> 1.
- **Fluency (deterministic, computed on read):** WPM = words / voiced time, and pause ratio = pause_ms / speech_span_ms. VAD padding before and after speech is excluded, as are processing time and tutor playback. These are shown as evidence and mapped to bands by an explicit, tunable heuristic that does **not** reward ever-faster speech. Words-per-turn is not an input, because short answers are fine.
- **Vocabulary (LLM, stored snapshot):** a fixed 1-5 rubric (repetitive basic wording -> varied, scenario-appropriate phrasing) that must quote the learner's own words. It is generated at session end, together with the summary (top weaknesses + one next-session focus). The summary model receives the computed statistics and active mistakes; it explains them but cannot override the numbers.
- **Staleness:** if any exclusion happens after `snapshot_at`, the whole generated section is labelled "generated before N later exclusions", with a **Regenerate** button.

## 7. Quiz

1. Select active `kind=error` mistakes for the profile + target language from eligible turns. Rank topics by frequency, with recency as tie-breaker. If the most recent session has eligible errors, include at least one item from it.
2. The LLM generates up to 5 questions, each tied to a source mistake id. Each question tests one distinction and is preferably a transformation of the learner's real sentence: multiple choice (option ids) or fill-in (`accepted_answers` list).
3. Validate before delivery:
   - source ids belong to this profile and language
   - MC options are distinct and the answer is among them
   - fill-ins have a usable answer key
   - drop ambiguous items
4. **Recheck source eligibility before returning the quiz and again at grading.** Items whose source was excluded in the meantime are graded `skipped_source_excluded` and left out of the denominator. If nothing remains, offer a fresh quiz.
5. Grade deterministically: MC by option id, and fill-in by matching against `accepted_answers` after Unicode/whitespace normalisation. German capitalisation and umlauts are preserved. No LLM grading.
6. Quizzes are generated on demand per "Start quiz" click, are immutable, and are not resumable (leaving one abandons it). Completed attempts stay as history.
7. With no history, show "complete a conversation first" and never generate generic questions presented as personalised.
8. Each item shows *"Practising this because you said: ..."* after answering.

## 8. Analysis tab

One tab per profile, with a language filter. Everything is read-only.

### Computed on read (deterministic, never stale)

All of this comes from completed sessions, eligible turns and active `kind=error` mistakes, so exclusions apply immediately.

1. **Topic frequency table.** Columns: topic label, errors, share of all errors, number of sessions it appeared in, last seen. Sorted by errors.
2. **Progress over sessions.** One row per session: date, scenario, level, grammar rating, error-free-turn %, errors per 100 words, WPM, vocabulary rating (snapshot). Sessions below the sample minimum show "-" for ratings. Show one simple line chart (Recharts) of error-free-turn % and errors per 100 words, plus the table.
3. **Recurring mistakes.** Topics that appear in 2 or more sessions, sorted by session count then error count, each with 2-3 quoted examples (original -> corrected). Exact repeats (same topic and same normalised `corrected` text) are grouped as "x4".
4. **Improving.** Topics seen in earlier sessions but absent from the last 2 sessions, counted only when each of those sessions has at least 5 eligible turns.

### LLM-written analysis (automatic after every session)

- **When:** after `/end` saves the session snapshot, a FastAPI background task generates the analysis, so ending a session never waits on it.
- **Input:** only the computed stats above, plus up to 30 recent active mistakes (id, topic, original, corrected).
- **Output (strict JSON):**
  - `summary`: 2-3 sentences
  - `strengths[]`: each with evidence
  - `focus_areas[]`: at most 3, each with `topic`, `why`, `tip` and `example_mistake_ids`
- **Validation:**
  - every `topic` must exist in the language's topic list **and** in the current frequency table
  - every example id must be an active mistake of this profile and language
  - the prompt allows only numbers taken from the provided stats, and the UI shows the computed tables next to the text as the source of truth
  - invalid output is retried once and then stored as `failed`
- **Storage:** `profile_analyses` keeps one row per attempt. The tab shows the latest `ok` row with "Based on N sessions, generated <time>". If exclusions happened after `generated_at`, it adds "generated before N later exclusions"; the next session end refreshes it. If the latest attempt failed, it shows "Latest analysis failed; showing the one from <date>".
- **Minimum data:** the tables work from 1 session. The written analysis needs **at least 2 completed sessions**; before that the tab says "Complete 2 sessions to unlock your analysis".

## 9. Risks and their guards

| Failure scenario | Guard |
|---|---|
| Learner says "Ich habe nach Berlin gegangen"; Whisper transcribes the *corrected* sentence, so the tutor misses the error. | Spike C measures intended-error preservation before scoring is built. If no model preserves errors adequately, narrow the demo claims; prompt changes cannot recover lost information. |
| Correct speech is mistranscribed, so the learner gets quizzed on an error they never made. | "Heard as ..." on each turn plus the **Misheard** button; exclusions propagate. |
| A thinking pause makes VAD submit half a sentence, and the tutor "corrects" it. | Conservative endpointing; `needs_clarification` asks the learner to repeat instead of correcting. |
| Tutor audio triggers VAD, and the app talks to itself. | Mic gated during processing + playback; 20-turn test on speakers and on headphones. |
| Background noise produces a hallucinated transcript. | VAD minimum speech duration, empty/implausible-output checks; when uncertain, ask to repeat and exclude from assessment. No phrase blacklist, since it would drop real speech like "Thank you". |
| LLM flags correct sentences. | Spike D eval (wrong + correct sentences, count misses and false flags); the `kind` split; the **Not a mistake** button. |
| TTS is slow, mispronounces German, or fails. | Spike B; text survives and speech retries independently; Qwen3-TTS is the chosen replacement if Chatterbox fails. |
| Retry or late response duplicates mistakes or leaks into the next session. | Client turn ids, retry semantics, session-status checks. |
| 4 devs exhaust shared free-tier quotas. | Check account limits at hour 0; routine UI work runs on fixtures and mocks. |
| Mic permission or VAD assets fail on demo day before the first turn. | Startup audio check screen; VAD assets served locally. |
| The written analysis invents a weakness, a number or a mistake the learner never made. | Input is computed stats + real mistakes only; topics and example ids validated against the DB; computed tables shown beside the text. |

## 10. Team split and timeline

**Hour 0-2: contracts + parallel spikes** (each person owns one go/no-go):

| Person | Spike | Then owns |
|---|---|---|
| A | Browser capture, VAD on hesitant speech, noise, playback feedback loop; confirm how to get voiced time / pauses (VAD frame probabilities; fallback: Whisper `verbose_json` segment timestamps) | Voice capture, VAD, playback, state machine, conversation UI |
| B | Chatterbox request shape, German/English pronunciation, latency (Qwen3-TTS if it fails) | Provider adapters, turn orchestration, retry semantics, speech endpoint |
| C | STT error preservation: ~10 deliberately wrong sentences per language, scored on whether the error survives (not word error rate) | SQLite models, exclusions, scoring, report + history APIs, Analysis stats endpoint |
| D | LLM correction eval (misses + false flags), schema validity, **validation pass rate** (target >= 95% of turns pass section 3 rules), quiz validity | Prompts + topic lists, quiz generation/validation/grading, written analysis, setup/report/quiz/Analysis UI, seed data, demo script |

| Hours | Milestone |
|---|---|
| 0-2 | `contracts/` frozen, mock endpoints up, spikes reported, provider choices locked |
| 2-6 | **One real voice turn end to end**: speak, hear the correction, turn saved |
| 6-12 | Session end + report, history, exclusions, quiz generation + grading |
| 12-17 | Analysis tab (lean: tables + one chart + written analysis), all screens integrated, failure/recovery states, 20-turn soak test |
| 17-24 | Rehearse the demo repeatedly, record a backup video, polish; deploy only if stable |

**Demo script:** pick German, cafe, A2. Speak **6+ substantive turns** (about 60 s of speech, so the ratings clear the sample minimum), including 2-3 rehearsed deliberate mistakes. Hear one spoken correction per turn and see all errors as cards. Dismiss one false positive live. End the session and show the report. Open the quiz: at least one item comes from this session (*"Practising this because you said ..."*). Finish on the Analysis tab: the topic table, the progress chart and the freshly regenerated written analysis. **Two** seeded prior sessions, clearly labelled **demo data** and seeded in the same topics as the rehearsed mistakes, provide history: the quiz has material, the chart has 3 points, and the written analysis is unlocked. If time is short on stage, show the ratings on the seeded session and use the live session for corrections and the quiz.

## 11. MVP vs stretch

**MVP:** everything above, including analysis status, idempotent turns, Not a mistake / Misheard with propagation, startup audio check, quiz source validation, deterministic grading, lean Analysis tab, labelled seed data.

**Stretch (only after the demo flow is stable):**
- deployment (note: SQLite on an ephemeral PaaS disk resets on redeploy)
- barge-in / interrupting the tutor
- MATTR or other lexical-diversity metrics
- elaborate recency weighting
- quiz-attempt history UI
- richer Analysis charts (per-topic trend lines, quiz accuracy per topic)
- automatic TTS failover
- inline highlight offsets for repeated phrases
- local-inference compatibility beyond the thin adapters
- more languages beyond German + English

## 12. Open items

- Pick a repository LICENSE (MIT suggested for a Hacktoberfest project).
- Confirm provider account quotas/credits at hour 0.
