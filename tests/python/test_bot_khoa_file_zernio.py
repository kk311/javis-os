"""A customer-facing bot never gets the vault file tools or the Zernio inbox tools (2026-11-20).

    python tests/run.py bot_khoa_file_zernio      (no network)

Owner: Sammy answers strangers at the "auto" level. At that level the hub hands a bot the file tools (the whole
brain, raw customer notes included) and every plugin tool, among them zernio_conversations / zernio_messages that
read OTHER customers' chats. Both are closed for a bot (`for_bot`); the owner's own sessions keep them. A bot
that wants documents uses the "read_docs" level (chatbot_doc_tools) or the pre-turn search.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import asyncio
import os
import sys
import tempfile

os.environ["JAVIS_STATE_DIR"] = tempfile.mkdtemp(prefix="javis-bot-khoa-")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import mcp_hub  # noqa: E402

_fails = []


def check(name, cond, extra=""):
    print(("ok   " if cond else "FAIL ") + name + (("  [" + str(extra) + "]") if extra and not cond else ""))
    if not cond:
        _fails.append(name)


def run(c):
    return asyncio.run(c)


def names(tools):
    return {t["fn"] for t in tools}


FILE_TOOLS = {"javis_read_file", "javis_list_dir", "javis_search_files"}
ZERNIO = ["zernio_conversations", "zernio_messages", "zernio_reply", "zernio_workspaces", "zernio__accounts_list"]
check("every zernio_* name is closed for a bot", all(mcp_hub.bot_cam_hub(n) for n in ZERNIO))
check("the file tools are closed for a bot", all(mcp_hub.bot_cam_hub(n) for n in FILE_TOOLS))
check("ordinary tools stay open", not any(mcp_hub.bot_cam_hub(n) for n in
      ("javis_task", "sapo_product_get", "javis_use_skill", "sapo-rita-beauty__list_orders")))

VAULT = tempfile.mkdtemp(prefix="javis-bot-khoa-vault-")
_lazy_on = mcp_hub._lazy_on
mcp_hub._lazy_on = lambda n, chars: False
for mode in ("auto", "full"):
    tools, route = run(mcp_hub.discover_all(mode, vault_root=VAULT, force_refresh=True, for_bot=True))
    bad = {n for n in (names(tools) | set(route)) if mcp_hub.bot_cam_hub(n)}
    check(f"a bot at '{mode}' sees none of them", not bad, sorted(bad))
tools_o, route_o = run(mcp_hub.discover_all("full", vault_root=VAULT, force_refresh=True))
check("the owner's session keeps the file tools", FILE_TOOLS <= names(tools_o) | set(route_o), sorted(names(tools_o)))
# lazy tier: javis_run_tool of a bot must not dispatch them either
_tl, route_lb = run(mcp_hub.discover_all("full", vault_root=VAULT, force_refresh=True, for_bot=True, force_lazy=True))
out = run(route_lb[mcp_hub._LAZY_RUN]["call"]({"name": "javis_read_file", "args": {"path": "x.md"}}))
check("lazy run on a bot cannot read a file", str(out).startswith("ERROR"), out)
mcp_hub._lazy_on = _lazy_on

src = (SERVER / "main.py").read_text(encoding="utf-8")
check("the Claude Code bot path disallows them by name too", "BOT_CAM_HUB_TOOLS" in src)

if _fails:
    print("\nFAILED: " + ", ".join(_fails))
    sys.exit(1)
print("\nOK - test_bot_khoa_file_zernio: all pass")
