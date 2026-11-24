"""Optional channel hook `prepare_manual_reply(conv, msgs)` for the inbox draft ("Javis soạn" / "Reply for me").

    python tests/run.py channel_manual_reply_hook      (no network, fake engine)

A channel (core or pack) may interpret the customer's last turn itself, for example read the photos a customer sent
through its own reader. Locked here:
  1. A channel without the hook behaves exactly as before: a photo with no caption has nothing to answer.
  2. The hook's text is what the model reads, and the core does not look at the photo a second time.
  3. The hook can refuse (`handled` + `ok: False`): its code and message reach the owner, the model is never called.
  4. The hook returning None keeps the old path.
  5. A hook that raises or returns junk fails the draft cleanly and never leaves the chat marked busy.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

os.environ["JAVIS_STATE_DIR"] = tempfile.mkdtemp(prefix="javis-manualhook-")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import chatbot_runtime  # noqa: E402
import chatbot_store  # noqa: E402

fails = []


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name + (("  [" + str(detail)[:400] + "]") if detail != "" and not cond else ""))
    if not cond:
        fails.append(name)


SENDER = "1000000002"      # fake platform id, never a real person
BRAIN = Path(tempfile.mkdtemp(prefix="brain-manualhook-"))
texts, media_looks = [], []


async def _answer(text, meta=None, progress=None, channel="telegram", bot=None, **kw):
    texts.append(text)
    return {"text": "Dạ shop còn màu này ạ.", "files": []}


async def _fake_media(text_engine, meta, cfg):
    media_looks.append(dict(meta or {}))
    return text_engine, []


chatbot_runtime.wire(answer=_answer, brain_root=lambda b: str(BRAIN),
                     read_agent=lambda br, slug: ({"name": "Trợ lý thử", "role": "Trực kênh"}, "Luật riêng."))
chatbot_runtime.anh_cho_bot = _fake_media
bid, err = chatbot_store.create_bot({"name": "Bot thử", "agent_slug": "tro-ly", "brain": "b",
                                     "token": "1:x", "channel": "telegram", "muc_quyen": "suggest",
                                     "audience": "all", "xac_nhan_rui_ro": True})
check("(setup) bot created", bool(bid) and not err, err)

CHANNEL = "fakehook"
hook = {"fn": None}
real_module = chatbot_runtime.channels.module


def fake_module(name):
    if name == CHANNEL:
        return SimpleNamespace(prepare_manual_reply=hook["fn"]) if hook["fn"] else SimpleNamespace()
    return real_module(name)


chatbot_runtime.channels.module = fake_module


def conv_for(channel, cid):
    return {"id": cid, "bot_id": bid, "channel": channel, "external_chat_id": SENDER, "chat_type": "private",
            "title": ""}


photo = [{"sender_type": "customer", "message_type": "image", "text": "https://example.invalid/p.jpg",
          "sender_id": SENDER, "sender_name": "Khách", "external_message_id": "p1", "created_at": 1}]
words = [{"sender_type": "customer", "text": "còn màu 120 không", "sender_id": SENDER, "sender_name": "Khách",
          "external_message_id": "w1", "created_at": 2}]


def run(conv, msgs):
    return asyncio.run(chatbot_runtime.manual_answer(conv, msgs, draft=True))


# ---- 1. no hook: unchanged
r = run(conv_for(CHANNEL, "c1"), photo)
check("no hook: a bare photo has nothing to answer", r.get("code") == "no_message", r)
n = len(texts)
r = run(conv_for(CHANNEL, "c1"), words)
check("no hook: a text message is drafted from the customer's words",
      r.get("ok") and len(texts) == n + 1 and "còn màu 120 không" in texts[-1], r)

# ---- 2. hook text wins, no second look at the photo
seen = []


async def prepare_ok(conv, msgs):
    seen.append(len(msgs))
    return {"handled": True, "ok": True, "text": "<<ảnh: son màu 120>> còn màu này không"}

hook["fn"] = prepare_ok
looks = len(media_looks)
r = run(conv_for(CHANNEL, "c2"), photo)
check("hook: a bare photo is drafted from the channel's text", r.get("ok") and "son màu 120" in texts[-1], r)
check("hook: receives the conversation and its messages", seen == [1], seen)
check("hook: the core does not read the photo again", len(media_looks) == looks, media_looks[looks:])

# ---- 3. hook refuses
calls = len(texts)


async def prepare_refuse(conv, msgs):
    return {"handled": True, "ok": False, "code": "vision_off", "error": "Đọc ảnh đang tắt"}

hook["fn"] = prepare_refuse
r = run(conv_for(CHANNEL, "c3"), photo)
check("hook refusal: its code and message reach the owner",
      not r.get("ok") and r.get("code") == "vision_off" and r.get("error") == "Đọc ảnh đang tắt", r)
check("hook refusal: the model is never called", len(texts) == calls, texts[calls:])


async def prepare_refuse_bare(conv, msgs):
    return {"handled": True, "ok": False}

hook["fn"] = prepare_refuse_bare
r = run(conv_for(CHANNEL, "c3b"), photo)
check("hook refusal without details: a default code and message",
      r.get("code") == "media_unavailable" and bool(r.get("error")), r)

# ---- 4. hook declines (None): old path
async def prepare_none(conv, msgs):
    return None

hook["fn"] = prepare_none
r = run(conv_for(CHANNEL, "c4"), photo)
check("hook returns None: a bare photo still has nothing to answer", r.get("code") == "no_message", r)
r = run(conv_for(CHANNEL, "c4"), words)
check("hook returns None: a text message is drafted as before", r.get("ok") and "còn màu 120 không" in texts[-1], r)

# ---- 5. broken hooks fail cleanly and release the chat
async def prepare_boom(conv, msgs):
    raise RuntimeError("reader down")

hook["fn"] = prepare_boom
r = run(conv_for(CHANNEL, "c5"), photo)
check("hook raises: the draft fails with an engine error", not r.get("ok") and r.get("code") == "engine", r)
check("hook raises: the chat is not left busy", "c5" not in chatbot_runtime._MANUAL_BUSY)


async def prepare_junk(conv, msgs):
    return {"ok": True, "text": "x"}      # missing "handled"

hook["fn"] = prepare_junk
r = run(conv_for(CHANNEL, "c6"), photo)
check("hook returns junk: the draft fails", not r.get("ok"), r)


async def prepare_empty(conv, msgs):
    return {"handled": True, "ok": True, "text": "  "}

hook["fn"] = prepare_empty
r = run(conv_for(CHANNEL, "c7"), photo)
check("hook returns empty text: the draft fails", not r.get("ok"), r)
hook["fn"] = prepare_ok
r = run(conv_for(CHANNEL, "c5"), photo)
check("after a failure the same chat drafts again", r.get("ok"), r)

# ---- core channels are untouched
r = run(conv_for("telegram", "c8"), photo)
check("core channel without the hook: unchanged", r.get("code") == "no_message", r)

print("\n" + ("ALL OK" if not fails else f"{len(fails)} FAIL: {fails}"))
sys.exit(1 if fails else 0)
