"""Sổ đăng ký KÊNH của Hộp thư hội thoại: nơi DUY NHẤT trong lõi biết một kênh là gì.

Trước 0.61.0, "kiến thức về một kênh" (tên, logo, lấy token ở đâu, có nhóm không, gửi file
được không, lớp vận chuyển nào, ghi tin vào kho ra sao) nằm rải ở tám chỗ: `chatbot_store`,
`chatbot_runtime`, `conversations`, `GET /chatbots` trong main.py, route `/conversations/channels`,
`icons.js`, `chatbots.js`, `conversations.js`. Thêm Zalo OA hay Facebook là sửa cả tám, và Zalo
cá nhân thành một "trường hợp đặc biệt" trong mỗi chỗ. Chủ dự án yêu cầu (2026-09-21) mọi kênh
được đối xử NHƯ NHAU và thêm kênh về sau không phải đụng lõi.

Cách làm: mỗi kênh là MỘT module trong gói này, khai một `KenhSpec` và một bộ hàm theo đúng
khế ước dưới đây. Lõi (kho bot, bộ giám sát, route, giao diện) chỉ đọc sổ; giao diện KHÔNG
được đoán theo id kênh mà vẽ theo `logo`, `nhan`, `nang_luc` server trả về.

Khế ước một module kênh (hàm thiếu = năng lực đó không có, sổ tự điền False):

    SPEC: KenhSpec                                   bắt buộc
    async verify_token(token) -> dict                kind="bot": hỏi nền tảng token này là bot nào.
                                                     Trả {"ok", "username", "bot_name", ...} hoặc
                                                     {"ok": False, "error"}.
    Transport: class                                 kind="bot": lớp long-polling (khế ước TelegramBot)
    tai_khoan() -> list[dict]                        kind="account": tài khoản đang có (id, label,
                                                     theo_doi, lan_cuoi, loi, so_tin)
    bat(account_id, on) -> dict                      kind="account": bật/tắt ghi vào hộp thư
    async gui(tk: dict, chat_id, text, chat_type)    gửi MỘT tin chữ từ tài khoản `tk` tới cuộc
                                                     chat. Trả (ok, loi). Có hàm này = kênh có
                                                     năng lực "trả lời từ Javis".

Ba LOẠI kênh (`kind`), khác nhau ở cách có tài khoản chứ không ở cách hiện ra:
    bot      - tài khoản là một TOKEN bot (Telegram Bot API, Zalo Bot API). Lưu ở
               `channel_accounts`, long-poll bằng `Transport`.
    account  - tài khoản là một PHIÊN đăng nhập sẵn có ở nơi khác (Zalo cá nhân qua MCP). Module
               tự liệt kê qua `tai_khoan()`, có công tắc ghi.
    webhook  - nền tảng GỌI NGƯỢC vào Javis (chừa chỗ, chưa kênh nào dùng). WhatsApp, Messenger và Zalo OA
               (0.412.0) cũng nhận tin qua webhook nhưng khai kind "bot": tài khoản vẫn là token lưu ở kho tài
               khoản, module khai thêm `WEBHOOK_PATH` để form thêm tài khoản hiện địa chỉ cần dán sang nền tảng.

Thêm một kênh = thêm một file ở đây + một dòng trong `_MODULES` + một logo trong icons.js.
Không sửa gì khác.

Channels from a Store pack: a pack lists `provides.channels: [channels/<name>.py]` in its manifest. The module
follows the same contract as a core channel and may carry its own logo in `SPEC.logo_svg` (the inner SVG of a
24x24 viewBox, filtered to a safe whitelist), so neither `_MODULES` nor icons.js changes. A pack channel loads
after the core ones, only from an ENABLED pack whose code passed the install gate (`packs.cho_chay_ma`), and
never replaces a channel id that already exists: on any problem it is MISSING, never half-loaded.

Optional module attributes (0.459.0, internal API channel):
    GENERATED_KEY = True          the account secret is a key Javis generates on Save and shows once (no pasted token);
                                  the module provides `new_key()`, `key_meta(raw)`, `default_settings()`
    PERMISSION_CEILING = "<level>"  the highest Chatbot permission level a turn on this channel may run at;
                                  `chatbot_runtime` refuses a turn above it
    clean_settings(data), account_settings_spec()   numeric account settings edited on the account form
    TOKEN_FORM = {...}            the account form as declared fields instead of one token box (see `_token_form`)
    MAX_ACCOUNTS_PER_BOT = <n>    how many accounts of this channel one bot may serve (default 20, see
                                  `max_accounts_per_bot`)
"""
from __future__ import annotations

import importlib
import importlib.util
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

KIND = ("bot", "account", "webhook")

# Năng lực mà lõi và giao diện hỏi. Khoá thiếu trong spec thì là False.
NANG_LUC_MAC_DINH = {
    "nhom": False,            # bot đứng được trong nhóm
    "gui_chu": False,         # gửi được chữ ra ngoài
    "gui_file": False,        # gửi được ảnh/tài liệu ra ngoài
    "tra_loi_tu_javis": False,   # chủ trả lời khách ngay từ Hộp thư (cần hàm `gui`)
    "bot": False,             # gắn được một Bot chuyên trách (kind == "bot")
    "ghi_theo_cong_tac": False,  # ghi vào hộp thư khi chủ BẬT (kind == "account")
    "nhap_lich_su": False,    # nhập lại tin cũ vào hộp thư khi chủ bấm (0.174.0, cần hàm `nhap_lich_su`)
}


@dataclass
class KenhSpec:
    id: str                     # id kho hiểu: telegram | zalo | zalo_personal | ...
    nhan: str                   # tên hiện ra: "Telegram", "Zalo Bot", "Zalo cá nhân"
    kind: str                   # bot | account | webhook
    logo: str = ""              # khoá logo trong icons.js (Icons.kenh): "telegram", "zalo"
    mau: str = ""               # màu thương hiệu, cho giao diện tô chip
    lay_token: str = ""         # kind=bot: hướng dẫn lấy token, một câu
    nang_luc: Dict[str, bool] = field(default_factory=dict)
    # Một câu tóm tắt cho ô chọn kênh (ai nhắn được, kênh này KHÔNG làm được gì).
    tom_tat: str = ""
    # Tên tài khoản phía nền tảng có tiền tố "@" không (Telegram có, Zalo không).
    tien_to_ten: str = ""
    # Bản tiếng Anh của chữ hiện ra (`nhan`, `lay_token`, `tom_tat`). Thiếu thì lấy ở
    # `_EN_MAC_DINH` theo id, rồi mới tới bản tiếng Việt.
    en: Dict[str, str] = field(default_factory=dict)
    # Logo of a channel that icons.js does not know (pack channels): inner SVG of a 24x24 viewBox.
    logo_svg: str = ""
    # Id of the Store pack that added this channel ("" for core channels).
    pack: str = ""

    def nl(self, khoa: str) -> bool:
        return bool(self.nang_luc.get(khoa, NANG_LUC_MAC_DINH.get(khoa, False)))


# Thứ tự ở đây là thứ tự hiện trên giao diện. KHÔNG có kênh nào "chính": Zalo đứng đầu vì
# khách Việt Nam dùng nhiều nhất, không phải vì nó được ưu ái trong mã.
_MODULES = ("channels.zalo_bot", "channels.zalo_personal", "channels.zalo_oa", "channels.messenger", "channels.threads",
            "channels.telegram", "channels.slack", "channels.whatsapp", "channels.wechat", "channels.lark",
            "channels.api")

# Chữ tiếng Anh cho các kênh có sẵn. Để ở đây (chứ không trong từng module kênh) cho một chỗ
# duy nhất phải sửa khi đổi chữ hiển thị; kênh mới có thể tự khai `en=` trong SPEC.
_EN_MAC_DINH: Dict[str, Dict[str, str]] = {
    "telegram": {
        "lay_token": "Message @BotFather on Telegram, type /newbot and follow the steps.",
        "tom_tat": "Can join groups and send images and documents. Less common in Vietnam.",
    },
    "zalo": {
        "lay_token": "Open the Zalo app, find the Official Account \"Zalo Bot Manager\" and choose Create bot. "
                     "The bot name must start with \"Bot\". The token is sent to you as a Zalo message.",
        "tom_tat": "Vietnamese customers already have it on their phones. Private chats only, cannot send documents yet.",
    },
    "zalo_personal": {
        "nhan": "Personal Zalo",
        "tom_tat": "Your own Zalo account. When a bot is on duty it replies in private chats and allowed groups, under your name.",
    },
}

_DS: Optional[Dict[str, KenhSpec]] = None
_DS_SIG: Optional[str] = None
_MOD: Dict[str, object] = {}


def _nap() -> Dict[str, KenhSpec]:
    global _DS, _DS_SIG
    sig = _goi_sig()
    if _DS is not None and _DS_SIG == sig:
        return _DS
    _DS_SIG = sig
    ds: Dict[str, KenhSpec] = {}
    mods: dict = {}
    nguon = [(ten, "") for ten in _MODULES] + _kenh_cua_goi()
    for ten, pid in nguon:
        try:
            m = _nap_module_goi(ten, pid) if pid else importlib.import_module(ten)
        except Exception as e:      # một kênh hỏng KHÔNG được kéo cả sổ chết
            print(f"[channels] không nạp được {ten}: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        spec: KenhSpec = getattr(m, "SPEC", None)
        if not isinstance(spec, KenhSpec) or spec.kind not in KIND or not spec.id:
            print(f"[channels] {ten} không có SPEC hợp lệ, bỏ qua", file=sys.stderr)
            continue
        if pid:
            if spec.id in ds:
                print(f"[channels] gói {pid}: kênh '{spec.id}' trùng kênh đã có, bỏ qua", file=sys.stderr)
                continue
            spec.pack = pid
            spec.logo_svg = _svg_sach(spec.logo_svg)
        nl = dict(NANG_LUC_MAC_DINH)
        nl.update(spec.nang_luc or {})
        # Hai năng lực suy ra từ chính module, không tin lời khai: có hàm mới có năng lực.
        nl["tra_loi_tu_javis"] = bool(nl.get("gui_chu")) and callable(getattr(m, "gui", None))
        # Kênh nào có lớp vận chuyển thì gắn được bot. Từ 0.64.80 gồm cả kind "account" (Zalo cá
        # nhân): nó không có token nhưng tin đi vào qua vòng đọc của chính module, và bot trả lời
        # bằng `gui`. Cái khác nhau giữa hai loại là NGUỒN tài khoản (token ở kho tài khoản, hay
        # kết nối ở trang Kết nối), xem `bot_token_ids`.
        nl["bot"] = spec.kind in ("bot", "account") and getattr(m, "Transport", None) is not None
        nl["ghi_theo_cong_tac"] = spec.kind == "account" and callable(getattr(m, "bat", None))
        nl["nhap_lich_su"] = callable(getattr(m, "nhap_lich_su", None))
        spec.nang_luc = nl
        if not spec.logo:
            spec.logo = spec.id
        ds[spec.id] = spec
        mods[spec.id] = m
    # Swap both at once: a channel of a pack that was just removed must not linger in _MOD.
    _MOD.clear()
    _MOD.update(mods)
    _DS = ds
    return ds


def _goi_sig() -> str:
    try:
        import packs
        return str(packs.signature())
    except Exception:  # noqa: BLE001
        return ""


def _kenh_cua_goi() -> list:
    """[(file path, pack id)] of pack channels allowed to run. Never raises."""
    try:
        import packs
        ra = []
        for pid, path in packs.channel_files():
            ok, vi_sao = packs.cho_chay_ma(pid)
            if not ok:
                print(f"[channels] gói {pid}: không nạp kênh {path.name}: {vi_sao}", file=sys.stderr)
                continue
            ra.append((str(path), pid))
        return ra
    except Exception as e:  # noqa: BLE001
        print(f"[channels] không đọc được kênh của gói: {type(e).__name__}: {e}", file=sys.stderr)
        return []


def _nap_module_goi(path: str, pid: str):
    """Import one pack channel file as `channels._pack_<pack>_<name>` (stable name, so a reload replaces it)."""
    from pathlib import Path
    ten = "channels._pack_" + re.sub(r"[^a-z0-9_]", "_", pid) + "_" + Path(path).stem
    spec = importlib.util.spec_from_file_location(ten, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[ten] = m
    try:
        spec.loader.exec_module(m)
    except BaseException:
        sys.modules.pop(ten, None)
        raise
    return m


def nap_lai() -> None:
    """Forget the registry so the next read rebuilds it (a pack was installed, removed, switched)."""
    global _DS, _DS_SIG
    _DS, _DS_SIG = None, None
    _MOD.clear()


# Whitelist for `SPEC.logo_svg`. The logo is put into the page as markup, so anything outside plain drawing
# (script, foreignObject, event handlers, links, external references, style) is refused, and the WHOLE logo is
# dropped rather than repaired: a pack channel without a logo still reads fine next to its name.
_SVG_THE = {"g", "path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "defs",
            "lineargradient", "radialgradient", "stop", "title"}
_SVG_THUOC_TINH = {"d", "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry", "width", "height",
                   "points", "fill", "fill-rule", "clip-rule", "fill-opacity", "stroke", "stroke-width",
                   "stroke-linecap", "stroke-linejoin", "stroke-opacity", "opacity", "transform", "id",
                   "offset", "stop-color", "stop-opacity", "gradientunits", "gradienttransform"}
_SVG_GIA_TRI_XAU = re.compile(r"url\(\s*(?!#)|javascript:|data:|expression|[<>]", re.I)


def _svg_sach(svg: str) -> str:
    svg = str(svg or "").strip()
    if not svg or len(svg) > 8000:
        return ""
    import xml.etree.ElementTree as ET
    try:
        goc = ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg">' + svg + "</svg>")
    except ET.ParseError:
        return ""
    for el in goc.iter():
        if el is goc:
            continue
        the = el.tag.split("}")[-1].lower()
        if the not in _SVG_THE:
            return ""
        for k, v in el.attrib.items():
            k = k.split("}")[-1].lower()
            if k not in _SVG_THUOC_TINH or _SVG_GIA_TRI_XAU.search(str(v)):
                return ""
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    return "".join(ET.tostring(c, encoding="unicode") for c in goc).replace(' xmlns="http://www.w3.org/2000/svg"', "")


def danh_sach() -> List[KenhSpec]:
    return list(_nap().values())


def ids() -> tuple:
    return tuple(_nap().keys())


def spec(kenh: str) -> Optional[KenhSpec]:
    return _nap().get(str(kenh or "").strip().lower())


def module(kenh: str):
    _nap()
    return _MOD.get(str(kenh or "").strip().lower())


def bot_ids() -> tuple:
    """Kênh gắn được Bot chuyên trách (có Transport). Thứ tự = thứ tự sổ."""
    return tuple(k for k, s in _nap().items() if s.nl("bot"))


def bot_token_ids() -> tuple:
    """Kênh gắn được bot VÀ tài khoản là một token lưu ở kho tài khoản (Telegram, Zalo Bot).

    Khác `bot_ids` ở đúng Zalo cá nhân: tài khoản của nó là kết nối ở trang Kết nối, không có
    token để tạo/lưu, nên mọi đường "tạo tài khoản token" phải dùng danh sách này.
    """
    return tuple(k for k, s in _nap().items() if s.nl("bot") and s.kind == "bot")


# How many accounts of ONE channel one bot may serve, when the channel module does not say. A channel that polls or
# holds a session per account (personal Zalo, Telegram, Zalo Bot) pays for each account the whole time the bot runs,
# so it keeps this cap. A webhook channel (Messenger: the platform pushes to one route, nothing is held per Page)
# declares a larger one with `MAX_ACCOUNTS_PER_BOT` (owner 2026-11-04: a shop with 26 Fanpages wants one bot).
MAX_ACCOUNTS_PER_BOT_DEFAULT = 20


def max_accounts_per_bot(kenh: str) -> int:
    """The cap on accounts of channel `kenh` one bot may serve: the module's `MAX_ACCOUNTS_PER_BOT`, else 20."""
    try:
        n = int(getattr(module(kenh), "MAX_ACCOUNTS_PER_BOT", 0) or 0)
    except (TypeError, ValueError):
        n = 0
    return n if n > 0 else MAX_ACCOUNTS_PER_BOT_DEFAULT


def nhan(kenh: str) -> str:
    s = spec(kenh)
    return s.nhan if s else str(kenh or "")


def logo(kenh: str) -> str:
    s = spec(kenh)
    return s.logo if s else ""


def nhan_theo_id() -> Dict[str, str]:
    return {k: s.nhan for k, s in _nap().items()}


def _chu_spec(s: KenhSpec, khoa: str) -> str:
    """Chữ hiện ra của spec theo ngôn ngữ giao diện. Chỉ cho màn hình, không cho prompt."""
    import localefmt   # lười: sổ kênh được nạp sớm, không kéo cấu hình lúc import
    vi = str(getattr(s, khoa, "") or "")
    en = (s.en or {}).get(khoa) or (_EN_MAC_DINH.get(s.id) or {}).get(khoa) or vi
    return localefmt.chu(vi, en) if vi else ""


def nhan_giao_dien(kenh: str) -> str:
    """Tên kênh để HIỆN TRÊN MÀN HÌNH (theo ngôn ngữ giao diện). Prompt vẫn dùng `nhan`."""
    s = spec(kenh)
    return _chu_spec(s, "nhan") if s else str(kenh or "")


def cho_giao_dien() -> List[dict]:
    """Bản cho giao diện: đủ để vẽ ô chọn kênh, chip, form thêm tài khoản, KHÔNG đoán gì thêm."""
    out = []
    for s in danh_sach():
        out.append({
            "id": s.id, "nhan": _chu_spec(s, "nhan"), "kind": s.kind, "logo": s.logo, "mau": s.mau,
            # Pack channels draw their own logo (icons.js does not know them), see `Icons.napKenh`.
            "logo_svg": s.logo_svg, "pack": s.pack,
            "lay_token": _chu_spec(s, "lay_token"), "tom_tat": _chu_spec(s, "tom_tat"),
            "tien_to_ten": s.tien_to_ten,
            "nang_luc": dict(s.nang_luc),
            # Hai cờ cũ giao diện Chatbot đang đọc; giữ để không đổi hai chỗ cùng lúc.
            # `co_nhom` là câu hỏi của form BOT: bot có đứng được trong nhóm không. Từ 0.64.82 gồm
            # cả Zalo cá nhân (bot trả lời trong nhóm đã cho phép); Zalo Bot thì không có `nhom`.
            "co_nhom": s.nl("nhom") and s.nl("bot"), "gui_tai_lieu": s.nl("gui_file"),
            # Kênh nhận tin qua webhook (Messenger, 0.134.0): form thêm tài khoản hỏi
            # GET /channels/webhook-info để hiện địa chỉ và mã xác minh cần dán sang nền tảng.
            "webhook": str(getattr(_MOD.get(s.id), "WEBHOOK_PATH", "") or ""),
            # Step-by-step guide (0.436.1): {"vi": "<file in docs/>", "en": "<file in docs/en/>"}. The add-account
            # form links to it next to the token hint; a channel without one shows no link.
            "huong_dan": dict(getattr(_MOD.get(s.id), "GUIDE", None) or {}),
            # The channel has its own card on the Connections page (Messenger, 0.436.2).
            "the_ket_noi": bool(getattr(_MOD.get(s.id), "CONNECT_CARD", False)),
            # Javis generates the account key and shows it once (internal API, 0.459.0): no token field, a Rotate button.
            "khoa_tu_sinh": bool(getattr(_MOD.get(s.id), "GENERATED_KEY", False)),
            "tran_muc_quyen": str(getattr(_MOD.get(s.id), "PERMISSION_CEILING", "") or ""),
            "cai_dat_tk": _account_settings(_MOD.get(s.id)),
            # Declarative credential form (pack channels): fields the dashboard draws instead of one token box.
            "form_tk": _token_form(_MOD.get(s.id)),
        })
    return out


# `TOKEN_FORM` (optional module attribute): the account form as DATA, so a channel with a structured credential
# (several ids, a connection to pick, accounts to list) needs no code in conversations.js and a pack ships no
# dashboard JS. The dashboard joins the sent fields into one JSON object and posts it as the token; the module's
# `prepare_token` / `verify_token` read it as usual. Anything outside this shape is dropped here, field by field:
#
#   {"fields": [{"key": "account_id", "type": "text" | "password" | "select", "label": str | {"vi","en"},
#                "hint": ..., "required": bool, "required_unless": "<other key>", "hidden_when": "<other key>",
#                "send": bool (default True), "initial": "external_id" | "meta.<key>",
#                "options": {"url": "/ext/<slug>/<path>", "list": "<array key>", "value": "<item key>",
#                            "label": "@{username} ({platform})", "empty": label, "from": ["<keys>"],
#                            "fill": {"<field key>": "<item key>"}, "button": label, "auto_single": bool}}],
#    "webhook_params": {"<query param>": "<field key>"}}
#
# A select with `options.from` POSTs those fields as a form body (a typed key never lands in a URL); without it,
# a GET. Option URLs must stay under /ext/ (plugin routes), so a declared form can never call a core route.
_FORM_KHOA = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
_FORM_URL = re.compile(r"^/ext/[a-z0-9][a-z0-9._-]{0,63}(/[A-Za-z0-9._-]+){1,4}$")
_FORM_KIEU = ("text", "password", "select")


def _form_chu(v, toi_da: int = 300) -> str:
    import localefmt
    if isinstance(v, dict):
        vi, en = str(v.get("vi") or ""), str(v.get("en") or "")
        v = localefmt.chu(vi or en, en or vi) if (vi or en) else ""
    return str(v or "")[:toi_da] if isinstance(v, str) else ""


def _form_khoa(v) -> str:
    v = str(v or "")
    return v if _FORM_KHOA.match(v) else ""


def _token_form(m) -> dict:
    tf = getattr(m, "TOKEN_FORM", None)
    if not isinstance(tf, dict) or not isinstance(tf.get("fields"), list):
        return {}
    try:
        fields = []
        for f in tf["fields"][:12]:
            if not isinstance(f, dict) or not _form_khoa(f.get("key")) or f.get("type") not in _FORM_KIEU:
                continue
            o = {"key": f["key"], "type": f["type"], "label": _form_chu(f.get("label"), 120) or f["key"],
                 "hint": _form_chu(f.get("hint")), "required": bool(f.get("required")),
                 "send": f.get("send", True) is not False}
            for k in ("required_unless", "hidden_when"):
                if _form_khoa(f.get(k)):
                    o[k] = f[k]
            ini = str(f.get("initial") or "")
            if ini == "external_id" or (ini.startswith("meta.") and _form_khoa(ini[5:])):
                o["initial"] = ini
            if f["type"] == "select":
                op = f.get("options") if isinstance(f.get("options"), dict) else {}
                url = str(op.get("url") or "")
                if not _FORM_URL.match(url) or any(p in (".", "..") for p in url.split("/")):
                    continue
                o["options"] = {
                    "url": url, "list": _form_khoa(op.get("list")) or "items",
                    "value": _form_khoa(op.get("value")) or "id",
                    "label": str(op.get("label") or "{" + (_form_khoa(op.get("value")) or "id") + "}")[:80],
                    "empty": _form_chu(op.get("empty"), 120),
                    "from": [k for k in (op.get("from") or []) if _form_khoa(k)][:4],
                    "fill": {k: v for k, v in (op.get("fill") or {}).items() if _form_khoa(k) and _form_khoa(v)},
                    "button": _form_chu(op.get("button"), 60),
                    "auto_single": bool(op.get("auto_single")),
                }
            fields.append(o)
        if not fields:
            return {}
        keys = {f["key"] for f in fields}
        wp = tf.get("webhook_params") if isinstance(tf.get("webhook_params"), dict) else {}
        return {"fields": fields,
                "webhook_params": {k: v for k, v in wp.items() if _form_khoa(k) and v in keys}}
    except Exception as e:  # noqa: BLE001 - a broken form must not take the channel list down
        print(f"[channels] token form of {getattr(m, '__name__', m)}: {type(e).__name__}: {e}", file=sys.stderr)
        return {}


def _account_settings(m) -> List[dict]:
    fn = getattr(m, "account_settings_spec", None)
    try:
        return list(fn()) if callable(fn) else []
    except Exception as e:      # a broken spec must not take the channel list down
        print(f"[channels] account settings of {getattr(m, '__name__', m)}: {type(e).__name__}: {e}", file=sys.stderr)
        return []


async def gui(kenh: str, tk: dict, chat_id: str, text: str, chat_type: str = "private", **extra):
    """Gửi một tin chữ qua kênh. Trả (ok, lỗi). Kênh không có năng lực -> (False, lý do).

    `extra` (hiện chỉ có `mention` của Zalo cá nhân) được chuyển nguyên cho kênh; kênh nào không nhận thì người gọi không truyền."""
    s = spec(kenh)
    m = module(kenh)
    if not s or not m:
        return False, f"kênh '{kenh}' không có trong sổ đăng ký"
    if not s.nl("tra_loi_tu_javis"):
        return False, f"{s.nhan} chưa gửi được tin từ Javis"
    try:
        return await m.gui(tk, str(chat_id), str(text or ""), chat_type or "private", **extra)
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def reset_cho_test() -> None:
    """Chỉ cho test: nạp lại sổ (sau khi monkeypatch một module kênh)."""
    global _DS
    _DS = None
    _MOD.clear()
