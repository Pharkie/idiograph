from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import ai_suggest as ai_mod

from . import support
from .support import (
    DEMO_QUESTION, DEMO_SHEET, ISO_OFFSET, check, demo_copy, skip,
)
import idiograph_routes


def test_review_rounds(scratch):
    print("\n70. AI review in rounds of three, numbered, Ask again folding the last round, an impersonal voice, "
          "and a reply on each card (173 to 176)")
    import subprocess
    import server as server_mod
    import themes as themes_mod
    import themes_ai

    js = support.text("apps/idiograph/static/themes.js")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    manual = support.source("docs/manual.md").read_text(encoding="utf-8")
    fn = lambda name: js.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in js else ""
    opus = ai_mod.model_name("claude-opus-5-5")

    # ── A. three a round, the most consequential first, and the impersonal voice
    known = {"g1", "g2"}
    five = json.dumps({"items": [{"about": "g1", "question": f"Does point {n} hold together?", "rule": "5", "why": "w"}
                                 for n in range(1, 6)]})
    check("174: a longer answer keeps the first three, in its order, and one question is a round of one",
          [i["question"] for i in themes_ai.parse_review(five, known)["items"]]
          == [f"Does point {n} hold together?" for n in (1, 2, 3)]
          and len(themes_ai.parse_review(json.dumps({"items": [{"question": "Does the board answer the question?"}]}),
                                         known)["items"]) == 1)

    # ── B. the board keeps its rounds, the newest on top, and each question its exchange
    flat_review = {"at": "2026-10-04T10:00:00+01:00", "model": "Haiku 4.5", "items": [
        {"about": "g1", "question": "Does the title reach every statement?", "rule": "8", "why": "w", "state": "considered"},
        {"about": None, "question": "Does the board answer the question?", "rule": "", "why": "w", "state": "open"}]}
    old = themes_mod.normalise({"review": flat_review})["review"]
    check("175: a board with the old flat list reads as one round, and writes as it did",
          old == flat_review and "earlier" not in old and themes_mod.review_rounds(old) == [old])

    def round_of(at, *questions, state="open"):
        return {"at": at, "model": "Haiku 4.5", "items": [{"about": None, "question": q, "rule": "", "why": "w", "state": state}
                                                         for q in questions]}

    r1, r2, r3 = (round_of("2026-10-04T10:00:00+01:00", "Is one apart?", "Is two apart?"),
                  round_of("2026-10-04T11:00:00+01:00", "Is three apart?"), round_of("2026-10-04T12:00:00+01:00", "Is four apart?"))
    stored = themes_mod.normalise({"review": dict(r3, earlier=[r1, {"items": []}, r2])})["review"]
    check("175: the board stores rounds in order, the newest at the top, the rest under earlier oldest first, an empty one gone",
          [r["at"] for r in themes_mod.review_rounds(stored)] == [r1["at"], r2["at"], r3["at"]]
          and stored["items"] == r3["items"] and stored["earlier"] == [r1, r2])
    many = themes_mod.normalise({"review": dict(r3, earlier=[round_of(f"t{n}", f"Is {n} apart?") for n in range(60)])})["review"]
    check("175: a board keeps fifty rounds, the oldest going past it",
          len(themes_mod.review_rounds(many)) == 50 and many["earlier"][0]["at"] == "t11" and many["at"] == r3["at"])
    said = [{"by": "analyst", "text": "  What of moving these\ninto their own PET?  ", "at": "a"},
            {"by": "ai", "text": "The two statements share the evening walk.", "at": "b", "model": "Haiku 4.5"},
            {"by": "someone", "text": "x"}, {"by": "ai", "text": "  "}]
    kept = themes_mod.normalise({"review": dict(r1, items=[dict(r1["items"][0], thread=said)])})["review"]["items"][0]
    check("173: a question keeps its exchange, his lines with their line breaks and the AI's with its model, and nothing else",
          kept["thread"] == [{"by": "analyst", "text": "What of moving these\ninto their own PET?", "at": "a"},
                             {"by": "ai", "text": "The two statements share the evening walk.", "at": "b", "model": "Haiku 4.5"}])
    check("173: a question keeps forty lines of its exchange, the oldest going past it, and one with none carries none",
          [line["text"] for line in themes_mod.thread_of([{"by": "analyst", "text": f"line {n}"} for n in range(45)])]
          == [f"line {n}" for n in range(5, 45)]
          and "thread" not in themes_mod.normalise({"review": r1})["review"]["items"][0])
    S = DEMO_SHEET
    linked = lambda at, q, about: dict(round_of(at, q), items=[dict(round_of(at, q)["items"][0], about=about)])
    board = {"cards": {f"{S}:3:0": {"x": 0, "y": 0, "text": "a"}, f"{S}:5:0": {"x": 0, "y": 100, "text": "b"}},
             "groups": [], "discarded": [], "picks": {},
             "review": dict(linked("t2", "Is the newer apart?", f"{S}:5:0"), earlier=[linked("t1", "Is the older apart?", f"{S}:3:0")])}
    moved = themes_mod._moved(board, lambda key: f"{S}:{int(key.split(':')[1]) + 2}")["review"]
    cut = themes_mod._moved(board, lambda key: None if key == f"{S}:3" else key, cut="T1")["review"]
    back = themes_mod._moved(dict(board, review=cut), lambda key: key, back="T1")["review"]
    check("175: a question's link moves with its row in every round, a cut marks it in every round, and the undo gives it back",
          moved["earlier"][0]["items"][0]["about"] == f"{S}:5:0" and moved["items"][0]["about"] == f"{S}:7:0"
          and cut["earlier"][0]["items"][0]["about"] == f"cut:T1:{S}:3:0" and cut["items"][0]["about"] == f"{S}:5:0"
          and back["earlier"][0]["items"][0]["about"] == f"{S}:3:0")

    # ── C. Ask again and a reply, through a transport that stands in for the provider
    root = scratch / "review-rounds"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    (root / "idiograph-project.json").write_text(json.dumps({"name": "Scratch", "research_question": DEMO_QUESTION}),
                                                 encoding="utf-8")
    path = themes_mod.themes_path(work)
    read = themes_mod.read_cards(work)
    keys = [c["key"] for c in read["cards"]]
    board = themes_mod.blank_version(read["cards"])
    for i, key in enumerate(keys[:4]):
        board["cards"][key].update(x=0, y=i * 100)
    for i, key in enumerate(keys[4:7]):
        board["cards"][key].update(x=900, y=i * 100)
    board["groups"] = [{"id": "g1", "label": "Mornings that belong to the dog", "members": keys[:4], "x": 0, "y": -40},
                       {"id": "g2", "label": "A house that holds two", "members": keys[4:7], "x": 900, "y": -40}]
    first = {"at": "2026-10-04T10:00:00+01:00", "model": opus, "items": [
        {"about": "g1", "question": "Does the title reach every statement under it?", "rule": "8",
         "why": "Two statements are about the evening.", "state": "considered"},
        {"about": "g2", "question": "Do the house and the dog sit as one experience?", "rule": "6",
         "why": "The title names a place.", "state": "dismissed"},
        {"about": None, "question": "Does the board answer the research question?", "rule": "",
         "why": "No PET names what the dog comes to mean.", "state": "open"}]}
    fresh = [{"about": "g1", "question": "Does the title reach every statement under it?", "rule": "8", "why": "w"},
             {"about": "g2", "question": "Does the house hold the walks as well as the rooms?", "rule": "8",
              "why": "Two walks sit under a title about the house."},
             {"about": None, "question": "Does any PET hold the hard mornings?", "rule": "9", "why": "The early starts sit apart."},
             {"about": "g1", "question": "Is the dog's need or her own the centre of the mornings?", "rule": "6", "why": "w"},
             {"about": "g2", "question": "Is a fifth question kept?", "rule": "6", "why": "w"}]
    real = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, ai_mod.find_key, ai_mod.http_call)
    config_path = scratch / "review-rounds-config.json"
    sent, replies = [], []

    def wire(method, url, headers, payload, timeout):
        sent.append(payload)
        reply = replies.pop(0) if replies else ""
        status, text = reply if isinstance(reply, tuple) else (200, reply)
        return status, json.dumps({"content": [{"type": "text", "text": text}], "stop_reason": "end_turn"})

    def settings(**extra):
        config_path.write_text(json.dumps({"ai_suggest": True, "ai_provider": "anthropic", "model": "claude-haiku-4-5",
                                           "pets_provider": "anthropic", "pets_model": "claude-opus-5-5", **extra}),
                               encoding="utf-8")

    def snapshot(folder):
        return {str(p): p.read_bytes() for p in sorted(Path(folder).rglob("*")) if p.is_file()}

    def ask(op, **extra):
        return idiograph_routes.api_themes_ai({"workbook": str(work), "op": op, "version": "v1", **extra})

    try:
        server_mod.CONFIG_PATH = config_path
        server_mod.ROOT_OVERRIDE = str(root)
        ai_mod.find_key = lambda *a, **kw: "k-test"
        ai_mod.http_call = wire
        settings()
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        body = {**{k: x for k, x in opened["version"].items() if k != "v"}, "cards": board["cards"], "groups": board["groups"], "discarded": [], "picks": {}}
        idiograph_routes.api_themes_save({"workbook": str(work), "version": body})
        replies[:] = [json.dumps({"items": fresh})]
        got = ask("review")
        call = sent[-1]
        check("174, 175: a first review asks the PETs model with nothing earlier in its prompt, and keeps three of five",
              got.get("asked") == 0 and len(got["review"]["items"]) == 3 and call["model"] == "claude-opus-5-5"
              and themes_ai.ASKED_REVIEW not in call["system"]
              and "Questions earlier rounds asked" not in call["messages"][0]["content"])

        idiograph_routes.api_themes_save({"workbook": str(work), "version": dict(body, review=first)})
        before = snapshot(root)
        sent.clear()
        replies[:] = [json.dumps({"items": fresh})]
        again = ask("review")
        user, asked_system = sent[-1]["messages"][0]["content"], " ".join(sent[-1]["system"].split())
        check("175: Ask again sends every earlier question with his tick, cross or neither, and asks for ones not yet asked",
              len(sent) == 1 and again.get("asked") == 3 and themes_ai.ASKED_REVIEW in asked_system
              and "Ask only questions not yet asked. Never ask again, in any words, a question he ticked or crossed." in asked_system
              and '- "Does the title reach every statement under it?" (ticked, actioned)' in user
              and '- "Do the house and the dog sit as one experience?" (crossed, set aside)' in user
              and '- "Does the board answer the research question?" (left open)' in user
              and user.index("Theme g1") < user.index("Questions earlier rounds asked") < user.index("Review this board."))
        check("175: a question an earlier round asked goes from the answer, and the round keeps three",
              [i["question"] for i in again["review"]["items"]]
              == ["Does the house hold the walks as well as the rooms?", "Does any PET hold the hard mornings?",
                  "Is the dog's need or her own the centre of the mornings?"])
        check("175: asking again writes nothing, the workbook and the themes file as they were", snapshot(root) == before)

        second = {k: again["review"][k] for k in ("at", "model", "items")}
        stack = dict(second, earlier=[first])
        idiograph_routes.api_themes_save({"workbook": str(work), "version": dict(body, review=stack)})
        kept = json.loads(path.read_text(encoding="utf-8"))["boards"][0]["review"]
        check("175: the autosave keeps both rounds in order, the newest on top and the first under earlier, and a reload hands them back",
              kept["items"] == second["items"] and kept["earlier"] == [first]
              and idiograph_routes.api_themes({"workbook": str(work)})["review"] == kept)
        sent.clear()
        replies[:] = [json.dumps({"items": fresh[3:]})]
        third = ask("review")
        check("175: a third round sends the questions of both earlier rounds, oldest first",
              third.get("asked") == 6 and sent[-1]["messages"][0]["content"].index("Does the title reach every statement")
              < sent[-1]["messages"][0]["content"].index("Does the house hold the walks"))

        # a reply on the newest round's first card
        words = "What do you think of moving these into their own PET?"
        answer = ("The walks sit with the mornings by time of day more than by what they are like for her. A PET of "
                  "their own might hold what the two statements share, though the board gives only two statements to it.")
        sent.clear()
        replies[:] = [answer]
        before = snapshot(root)
        answered = ask("reply", round=1, item=0, question=second["items"][0]["question"], text=words)
        call = sent[-1] if sent else {"system": "", "messages": [{"content": ""}]}
        user = call["messages"][0]["content"]
        check("173: one call per Send through the PETs model, asking for two to five sentences in the impersonal voice",
              len(sent) == 1 and call.get("model") == "claude-opus-5-5" and themes_ai.REPLY_TASK in call["system"]
              and "Answer in two to five sentences, and answer what he asked." in call["system"]
              and "agree with it or question it from the statements on the board, and never decide for him"
              in " ".join(call["system"].split())
              and themes_ai.VOICE in call["system"] and DEMO_QUESTION in call["system"]
              and all(f"{n}. {t}" in call["system"] for n, t in themes_ai.guidance_items(3)))
        check("173: the reply sends the board as the review sends it, the card's question and why, and his words",
              "Theme g1: Mornings that belong to the dog" in user and "Theme g2: A house that holds two" in user
              and f"The question the review asked: {second['items'][0]['question']}" in user
              and f"Why it was asked: {second['items'][0]['why']}" in user and "It is about g2 on the board." in user
              and f"He writes now: {words}" in user and user.rstrip().endswith("Answer him.")
              and "The exchange on it so far" not in user)
        check("173: the answer is the AI's line, its words, its time and its model, and asking writes nothing",
              answered.get("reply", {}).get("by") == "ai" and answered["reply"]["text"] == answer
              and answered["reply"]["model"] == opus and ISO_OFFSET.match(answered["reply"]["at"]) is not None
              and snapshot(root) == before)

        thread = [{"by": "analyst", "text": words, "at": answered["reply"]["at"]}, answered["reply"]]
        stack = dict(stack, items=[dict(stack["items"][0], thread=thread)] + stack["items"][1:])
        idiograph_routes.api_themes_save({"workbook": str(work), "version": dict(body, review=stack)})
        kept = json.loads(path.read_text(encoding="utf-8"))["boards"][0]["review"]
        check("173: the exchange is saved with the card on the board, a reload hands it back, and the other cards carry none",
              kept["items"][0]["thread"] == thread and "thread" not in kept["items"][1]
              and idiograph_routes.api_themes({"workbook": str(work)})["review"]["items"][0]["thread"] == thread)
        sent.clear()
        replies[:] = ["The mornings are hers in the statements."]
        ask("reply", round=1, item=0, question=second["items"][0]["question"],
            text="I think the joy frame holds because the mornings are hers.")
        user = sent[-1]["messages"][0]["content"] if sent else ""
        check("173: a second reply carries the exchange so far, his line and the answer told apart, before his new words",
              f"The exchange on it so far:\nHe wrote: {words}\nThe answer: {answer}" in user
              and user.index("The exchange on it so far") < user.index("He writes now: I think the joy frame holds"))
        sent.clear()
        replies[:] = ["An answer."]
        elsewhere = ask("reply", round=0, item=2, question=second["items"][1]["question"], text="Why so?")
        found = sent[-1]["messages"][0]["content"] if sent else ""
        sent.clear()
        unknown = ask("reply", round=1, item=0, question="Is this a question nobody asked?", text="Why so?")
        empty = ask("reply", round=1, item=0, question=second["items"][0]["question"], text="   ")
        check("173: a card whose place holds another question is found by its words, and one no round asked, or no words, is one line and no call",
              elsewhere.get("reply") and f"The question the review asked: {second['items'][1]['question']}" in found
              and unknown == {"error": themes_ai.NO_SUCH_QUESTION} and empty == {"error": themes_ai.NO_REPLY} and not sent)
        replies[:] = [(529, "")]
        failed = ask("reply", round=1, item=0, question=second["items"][0]["question"], text="Why so?")
        settings(ai_suggest=False)
        sent.clear()
        off = ask("reply", round=1, item=0, question=second["items"][0]["question"], text="Why so?")
        check("173: a failure comes back as one line, and with the switch off a reply is refused and nothing is sent",
              failed == {"error": "Anthropic did not answer (HTTP 529)."} and off == {"error": themes_ai.OFF} and not sent)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, ai_mod.find_key, ai_mod.http_call = real
    check("173: an answer is read strictly: fences go, JSON gives its words, dashes and semicolons are cleaned, one paragraph",
          themes_ai.parse_reply("```\nThe walks sit apart.\n```") == {"text": "The walks sit apart."}
          and themes_ai.parse_reply('{"answer": "The walks sit apart."}') == {"text": "The walks sit apart."}
          and themes_ai.parse_reply("The walks \u2014 apart; the mornings\n\nnot.") == {"text": "The walks, apart, the mornings not."}
          and themes_ai.parse_reply("  ") == {"error": themes_ai.NO_ANSWER}
          and themes_ai.parse_reply("Cut off", truncated=True) == {"error": ai_mod.TOO_LONG}
          and len(themes_ai.parse_reply("word " * 1000)["text"]) <= themes_ai.REPLY_TEXT)

    # ── D. the page: the numbers, the round head, the folds, Reply and Send
    check("173: Cmd + Enter in the box sends, Esc closes it, and nothing else on the screen hears its keys",
          "if (e.key === 'Enter' && MOD(e)) { e.preventDefault(); thReplySend(key); }" in js
          and "else if (e.key === 'Escape') { e.preventDefault(); thReplyClose(key); }" in js
          and "const key = e.target && e.target.dataset ? e.target.dataset.replyBox : undefined;" in js
          and "if (send) { thReplySend(send.dataset.replySend); return; }" in js
          and "if (replying) { thReplyOpen(replying.dataset.reply); return; }" in js)
    sender = fn("thReplySend")
    check("173: Send saves the canvas first, asks once with the card's place, its question and his words, and keeps the answer with the board",
          sender.index("await thFlush();") < sender.index("op: 'reply', version: board, round: r, item: i, question, text: words")
          and "thReplyKeep(target, words, data.reply, at);" in sender and "thSoon();" in sender
          and not re.search(r"thStep|thDone|thRender|thPlace", sender))

    node = shutil.which("node")
    if not node:
        skip("173 to 175: the review's rounds and replies in node", "no node on this machine")
    else:
        lines = [l for l in app.splitlines() if l.startswith(("const refusedAs = ", "const RESTART_LINE = ",
                                                                 "const needsRestart = ", "const esc = ", "const escAttr = "))]
        script = scratch / "review-rounds.js"
        script.write_text(support.i18n_js() + js + "\n" + "\n".join(lines) + r"""
const MOD = (e) => !!e.metaKey;
let calls = [];
let answer = null;
let saves = 0;
async function api(route, body) { calls.push([route, body]); if (answer instanceof Error) throw answer; return answer; }
async function thFlush() {}
function thViewEnd() {}
function thBoardDraw() {}
function thSideOpen() {}
function thTitleDone() {}
function thNoteDone() {}
function thSoon() { saves += 1; }
const REVIEW = { at: 't2', model: 'Opus 5.5', items: [
  { about: null, question: 'Does the house hold the walks?', why: 'w', rule: '8', state: 'open' },
  { about: null, question: 'Does any PET hold the hard mornings?', why: 'w', rule: '', state: 'considered' },
  { about: null, question: 'Is the centre of the mornings hers?', why: 'w', rule: '', state: 'open' }],
  earlier: [{ at: 't1', model: 'Haiku 4.5', items: [
    { about: null, question: 'Does the title reach every statement?', state: 'considered' },
    { about: null, question: 'Do the house and the dog sit as one?', state: 'dismissed' },
    { about: null, question: 'Does the board answer the question?', state: 'considered' }] }] };
TH.ai = { on: true, model_name: 'Opus 5.5' };
TH.live = true;
TH.path = 'P.xlsx';
TH.meta = { id: 'v1' };
TH.v = { cards: {}, groups: [], discarded: [], picks: {}, review: JSON.parse(JSON.stringify(REVIEW)) };
const out = {};
out.rounds = thReviewRounds(TH.v.review).map((r) => r.at);
out.flat = thReviewRounds({ at: 'x', model: 'm', items: [{ question: 'Q?' }] }).length;
out.heads = [thRoundHead(REVIEW, 2), thRoundHead(REVIEW.earlier[0], 1, true), thRoundHead({ items: [{ state: 'open' }] }, 3),
  thRoundHead({ items: [{ state: 'open' }] }, 1, true)];
const next = thReviewNext(REVIEW, { at: 't3', model: 'm', items: [{ question: 'New?' }] });
out.next = [next.at, next.earlier.map((r) => r.at), Object.keys(next).sort()];
const fromFlat = thReviewNext({ at: 'a', model: 'm', items: [{ question: 'A?' }] }, { at: 'b', model: 'm', items: [{ question: 'B?' }] });
out.fromFlat = [fromFlat.at, fromFlat.earlier.map((r) => r.at)];
out.items = [thReviewItem(REVIEW, '0:1').question, thReviewItem(REVIEW, '1:2').question, thReviewItem(REVIEW, '5:0'),
  thReviewItem(REVIEW, '0:9'), thReviewItem(REVIEW, 'x')];
TH.replies.set('1:0', { text: 'Words <b>', busy: false, said: '', ask: 0 });
const card = thReviewItemHtml(TH.v, TH.v.review.items[0], '1:0', 0);
const plain = thReviewItemHtml(TH.v, TH.v.review.items[1], '1:1', 1);
out.card = [card.includes('<span class="th-review-n">1</span>'), card.includes('data-reply="1:0"'),
  card.includes('data-reply-send="1:0"'), card.includes('>Words &lt;b&gt;</textarea>'), (card.match(/M12 3\.2c/g) || []).length];
out.plain = [plain.includes('<span class="th-review-n">2</span>'), plain.includes('th-reply-box'), plain.includes('M12 3.2c')];
out.lines = [thThreadLineHtml({ by: 'analyst', text: 'Mine' }), thThreadLineHtml({ by: 'ai', text: 'The answer', model: 'Opus 5.5' })];
(async () => {
  answer = { reply: { by: 'ai', text: 'The walks sit apart.', at: '2026-10-05T10:00:00+01:00', model: 'Opus 5.5' } };
  TH.replies.set('1:0', { text: '  What of a PET of their own?  ', busy: false, said: '', ask: 0 });
  await thReplySend('1:0');
  out.sent = calls[0];
  out.landed = [TH.v.review.items[0].thread.map((l) => [l.by, l.text, l.model || '']), TH.replies.has('1:0'), saves];
  answer = new Error('Anthropic did not answer (HTTP 529).');
  TH.replies.set('1:1', { text: 'Why so?', busy: false, said: '', ask: 0 });
  await thReplySend('1:1');
  out.failed = [TH.replies.get('1:1'), TH.v.review.items[1].thread || null];
  answer = Object.assign(new Error('No such endpoint.'), { code: 'no_endpoint' });
  TH.replies.set('1:2', { text: 'And this?', busy: false, said: '', ask: 0 });
  await thReplySend('1:2');
  out.old = TH.replies.get('1:2');
  answer = Object.assign(new Error('That is not something the AI help does, so nothing was asked.'), { code: 'unknown_op' });
  TH.replies.set('0:0', { text: 'And that?', busy: false, said: '', ask: 0 });
  await thReplySend('0:0');
  out.old2 = TH.replies.get('0:0').said;
  calls = [];
  TH.replies.set('0:1', { text: '   ', busy: false, said: '', ask: 0 });
  await thReplySend('0:1');
  out.empty = calls.length;
  TH.reviewFolds.add(0);
  answer = { review: { at: 't3', model: 'Opus 5.5', items: [{ question: 'New?' }] }, asked: 6 };
  await thReviewAsk();
  out.asked = [TH.v.review.at, TH.v.review.earlier.map((r) => r.at), TH.reviewFolds.size, TH.reviewSaid,
    TH.v.review.earlier[1].items[0].thread.length];
  answer = { review: { at: 't4', model: 'Haiku 4.5', items: [{ question: 'Old?' }] } };
  await thReviewAsk();
  out.oldReview = [TH.reviewSaid, TH.v.review.at];
  console.log(JSON.stringify(out));
})();
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("173 to 175: the review's rounds and replies run in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            check("175: in node, the rounds come oldest first, a review from before them is one round",
                  out["rounds"] == ["t1", "t2"] and out["flat"] == 1, str(out["rounds"]))
            check("174, 175: in node, the head says the round and how many, and a folded line how many he ticked",
                  out["heads"] == ["Round 2 · 3 questions", "Round 1 · 3 questions · 2 ticked", "Round 3 · 1 question",
                                   "Round 1 · 1 question"], str(out["heads"]))
            check("175: in node, Ask again's round goes on top with every round before it folded under earlier, in order",
                  out["next"] == ["t3", ["t1", "t2"], ["at", "earlier", "items", "model"]] and out["fromFlat"] == ["b", ["a"]],
                  str(out["next"]))
            check("175: in node, a question is found by its round and place, and nothing past them",
                  out["items"] == ["Do the house and the dog sit as one?", "Is the centre of the mornings hers?", None, None, None],
                  str(out["items"]))
            check("173, 174: in node, a card carries its number and Reply, its open box his words and Send with the sparkles alone",
                  out["card"] == [True, True, True, True, 1] and out["plain"] == [True, False, False], str(out["card"] + out["plain"]))
            check("173: in node, Send asks once with the board, the round, the place, the question and his words",
                  out["sent"] == ["/api/themes-ai", {"workbook": "P.xlsx", "op": "reply", "version": "v1", "round": 1, "item": 0,
                                                     "question": "Does the house hold the walks?",
                                                     "text": "What of a PET of their own?"}], str(out["sent"]))
            check("173: in node, the answer goes under his words in the card, the box closes and the board is saved",
                  out["landed"] == [[["analyst", "What of a PET of their own?", ""], ["ai", "The walks sit apart.", "Opus 5.5"]],
                                    False, 1], str(out["landed"]))
            check("173: in node, a failure is one line in the card, his words kept in the box, and nothing kept on the card",
                  out["failed"] == [{"text": "Why so?", "busy": False, "said": "Anthropic did not answer (HTTP 529).", "ask": 0}, None],
                  str(out["failed"]))
            check("173: in node, a page in front of an old server says to restart in the card, his words kept",
                  out["old"] == {"text": "And this?", "busy": False, "said": "Restart the server to finish this update.", "ask": 0}
                  and out["old2"] == "Restart the server to finish this update.", str(out["old"]))
            check("173: in node, a box with no words sends nothing", out["empty"] == 0)
            check("175: in node, Ask again puts the new round on top, folds every earlier round and keeps their exchanges",
                  out["asked"] == ["t3", ["t1", "t2"], 0, "", 2], str(out["asked"]))
            check("175: in node, a server from before the rounds says to restart and the rounds stay as they were",
                  out["oldReview"] == ["Restart the server to finish this update.", "t3"], str(out["oldReview"]))

    # ── E. the manual and the internals
    section = manual.split("\n## PETs\n", 1)[1].split("\n## ", 1)[0]
    passage = section.split("**Review.**", 1)[1].split("**Guidance.**", 1)[0] if "**Review.**" in section else ""
    said = " ".join(passage.split())
