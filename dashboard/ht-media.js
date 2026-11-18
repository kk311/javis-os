/* ht-media.js - anh va file KHACH gui trong Hop thu bot (0.171.0).

   Chu repo 15/10/2026: o Hop thu bot, khach gui anh thi chi thay mot dong "image https://...jpg",
   gui file thi chi thay ten. Muon: anh hien thang trong cuoc chat, file thi bam tai ve.

   Hai nguon, deu da co san trong tin, giao dien truoc day bo qua:
     - Zalo ca nhan luu LINK: metadata.image_url (anh) va metadata.attachment {url, name, size} (file).
     - Cac kenh bot con lai (Telegram, Zalo Bot, Slack, WhatsApp, Messenger, Discord, Lark) TAI VE brain cua
       bot roi ghi mot dong "[... da tai ve: <duong dan>]" vao tin. File do di qua
       /conversations/<id>/media, duong may chu tu kiem file nam trong inbox/ hoac attachments/ cua brain.

   File nay chi giu phan THUAN de test bang node: tests/js/test_ht_media.js. Khong dung ky tu em dash. */
(function () {
  "use strict";

  var DUOI_ANH = /\.(png|jpe?g|gif|webp|bmp|heic)$/i;
  // Dong tai ve do gateway ghep, ca ban tieng Viet lan tieng Anh (localefmt.chu).
  // Ma unicode ben duoi = cum "da tai ve" co dau, viet bang ma unicode de file code khong chua chu Viet tran.
  var TAI_VE = /\[[^\]\n]*?(?:\u0111\u00e3 t\u1ea3i v\u1ec1|downloaded to):\s*([^\]\n]+)\]/i;

  function laHttps(u) { return /^https:\/\/\S+$/i.test(String(u || "").trim()); }

  function tenFile(p) {
    var s = String(p || "").replace(/[\\/]+$/, "");
    return s.split(/[\\/]/).pop() || s;
  }

  function coDungLuong(n) {
    n = Number(n);
    if (!isFinite(n) || n <= 0) return "";
    if (n < 1024) return n + " B";
    if (n < 1048576) return Math.round(n / 1024) + " KB";
    return (n / 1048576).toFixed(1) + " MB";
  }

  // Phan chu that cua nguoi gui: bo dong tai ve; bo luon chu "nen" (link anh tran, "[chat.photo]",
  // "[Zalo ca nhan: khach gui image]") vi do khong phai loi khach noi.
  function chuThich(text) {
    var s = String(text || "").replace(TAI_VE, "").trim();
    if (!s) return "";
    if (laHttps(s) || /^\[[^\]\n]*\]$/.test(s)) return "";
    return s;
  }

  // Doc mot tin cua kho hoi thoai -> { anh: src|"", file: {href, ten, coDung}|null, chu: chu thich }.
  // `cid` = id hoi thoai, de dung duong /conversations/<cid>/media cho file da tai ve may.
  function phanTich(t, cid) {
    t = t || {};
    var md = t.metadata || {};
    var loai = String(t.message_type || "");
    var text = String(t.text || "");
    var m = TAI_VE.exec(text);
    var duong = m ? m[1].trim() : "";
    var quaMay = function (p, taiVe) {
      return "/conversations/" + encodeURIComponent(String(cid || t.conversation_id || "")) +
        "/media?p=" + encodeURIComponent(p) + (taiVe ? "&dl=1" : "");
    };
    var ra = { anh: "", file: null, lien: null, chu: chuThich(text) };
    if (loai === "image" || (duong && DUOI_ANH.test(duong))) {
      if (laHttps(md.image_url)) ra.anh = String(md.image_url).trim();
      else if (duong) ra.anh = quaMay(duong, false);
      else if (laHttps(text.trim())) ra.anh = text.trim();
      if (ra.anh) return ra;
    }
    var att = md.attachment && typeof md.attachment === "object" ? md.attachment : null;
    if (att && laHttps(att.url)) {
      ra.file = { href: String(att.url).trim(), ten: String(att.name || tenFile(att.url)), coDung: coDungLuong(att.size) };
    } else if (duong) {
      ra.file = { href: quaMay(duong, true), ten: tenFile(duong), coDung: "" };
    }
    if (ra.file && ra.chu === ra.file.ten) ra.chu = "";
    if (!ra.anh && !ra.file) dinhKem(md.attachments, text, ra);
    return ra;
  }

  // Zernio (Instagram) luu metadata.attachments [{type, originalType, url, payload}] (owner 2026-11-18: truoc day
  // khach gui anh, story, bai dang thi chi thay o trong). Chi hien LINK, khong tai ve may: anh hien thang tu link,
  // bai dang hien anh bai kem caption, reel va video thanh the link. Link CDN co chu ky nen co the het han.
  function rutGon(s, n) {
    s = String(s || "").replace(/\s+/g, " ").trim();
    return s.length > n ? s.slice(0, n).replace(/\s+\S*$/, "") + "..." : s;
  }

  function dinhKem(list, text, ra) {
    if (!Array.isArray(list)) return;
    var items = list.filter(function (a) { return a && typeof a === "object"; });
    if (!items.length) return;
    var a = items[0];
    var loai = String(a.type || "").toLowerCase();
    var goc = String(a.originalType || "").toLowerCase();
    var pl = a.payload && typeof a.payload === "object" ? a.payload : {};
    var cap = rutGon(pl.title, 300);
    // Chu cua tin la nhan may chu tu ghi ("[Bai dang] ...") thi thay bang mo ta that; loi khach go thi giu nguyen.
    var nhan = /^\[[^\]\n]*\]/.test(String(text || "").trim());
    var dat = function (chu) { if (nhan || !ra.chu) ra.chu = chu; };
    if (/_post$/.test(goc) || (loai === "share" && cap)) {
      if (laHttps(a.url)) ra.anh = String(a.url).trim();
      else if (laHttps(pl.url)) ra.anh = String(pl.url).trim();
      dat(cap ? "B\u00e0i \u0111\u0103ng: " + cap : "B\u00e0i \u0111\u0103ng");
      return;
    }
    if (/_story$/.test(goc)) {
      var st = laHttps(pl.story_media_url) ? pl.story_media_url : a.url;
      if (laHttps(st)) ra.lien = { href: String(st).trim(), ten: "Story", phu: "Kh\u00e1ch tr\u1ea3 l\u1eddi story" };
      dat("");
      return;
    }
    if (/_reel$/.test(goc) || loai === "video" || loai === "audio" || loai === "file") {
      var href = laHttps(a.url) ? a.url : pl.url;
      var ten = /_reel$/.test(goc) ? "Reel" : loai === "audio" ? "Ghi \u00e2m" : loai === "file" ? "T\u1ec7p" : "Video";
      if (laHttps(href)) ra.lien = { href: String(href).trim(), ten: ten, phu: cap };
      dat("");
      return;
    }
    if (loai === "image") {
      var u = laHttps(a.url) ? a.url : pl.url;
      if (laHttps(u)) ra.anh = String(u).trim();
      dat(items.length > 1 ? "+" + (items.length - 1) + " \u1ea3nh" : "");
      return;
    }
    if (loai === "template") { dat("Tin m\u1eabu"); return; }
    var khac = laHttps(a.url) ? a.url : "";
    if (khac) ra.lien = { href: String(khac).trim(), ten: "\u0110\u00ednh k\u00e8m", phu: "" };
    dat("");
  }

  // HTML phan media cua bong bong (chua co chu thich). `esc` escape HTML, `ic` ve icon, `tw` dich chu.
  function html(pt, esc, ic, tw) {
    if (pt.anh) {
      var src = esc(pt.anh);
      return '<a class="ht-anh" href="' + src + '" target="_blank" rel="noopener noreferrer">' +
        '<img src="' + src + '" alt="" loading="lazy" referrerpolicy="no-referrer"' +
        ' onerror="this.parentNode.classList.add(\'hong\')">' +
        '<span class="ht-anh-hong">' + ic("image") + " " + esc(tw("ht.anh_hong")) + "</span></a>";
    }
    if (pt.lien) {
      return '<a class="ht-file ht-lien" href="' + esc(pt.lien.href) + '" target="_blank" rel="noopener noreferrer">' +
        '<span class="ht-file-ico">' + ic("link") + "</span>" +
        '<span class="ht-file-info"><span class="ht-file-ten">' + esc(pt.lien.ten) + "</span>" +
        (pt.lien.phu ? '<span class="ht-file-meta">' + esc(pt.lien.phu) + "</span>" : "") + "</span></a>";
    }
    if (pt.file) {
      return '<a class="ht-file" href="' + esc(pt.file.href) + '" target="_blank" rel="noopener noreferrer" download>' +
        '<span class="ht-file-ico">' + ic("paperclip") + "</span>" +
        '<span class="ht-file-info"><span class="ht-file-ten">' + esc(pt.file.ten) + "</span>" +
        '<span class="ht-file-meta">' + (pt.file.coDung ? esc(pt.file.coDung) + " · " : "") + esc(tw("ht.tai_ve")) + "</span></span>" +
        '<span class="ht-file-dl">' + ic("download") + "</span></a>";
    }
    return "";
  }

  // Dong xem truoc trong danh sach hoi thoai: khong de lo dong "[... da tai ve: <duong dan may chu>]" hay mot link anh dai.
  // Anh -> nhan "Anh" (kem chu thich neu co); file da tai ve -> ten file.
  function tomTat(text, tw) {
    var s = String(text || "");
    var m = TAI_VE.exec(s);
    var cap = chuThich(s);
    if (m) {
      var ten = tenFile(m[1].trim());
      return (DUOI_ANH.test(ten) ? tw("ht.anh") : ten) + (cap ? ": " + cap : "");
    }
    if (laHttps(s.trim()) && (DUOI_ANH.test(s.trim()) || /zdn\.vn\//i.test(s))) return tw("ht.anh");
    return s;
  }

  // Name shown in the lightbox bar: the file name, from ?p= for photos served by /conversations/<id>/media.
  function tenAnh(href) {
    try {
      var u = new URL(href, "http://x/");
      var p = u.searchParams.get("p") || u.pathname;
      return tenFile(p);
    } catch (e) { return ""; }
  }

  // Clicking a customer's photo opens it inside Javis (the chat lightbox, with a close button and Back closing it)
  // instead of a new tab (owner 2026-10-19: easier to go back to the customer's messages). Ctrl/Cmd/middle click
  // and a photo that failed to load keep the link's own new-tab behaviour.
  if (typeof document !== "undefined") {
    document.addEventListener("click", function (e) {
      var a = e.target && e.target.closest ? e.target.closest("a.ht-anh") : null;
      if (!a || a.classList.contains("hong") || !window.JavisLightbox) return;
      if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || e.button > 0) return;
      e.preventDefault();
      e.stopPropagation();
      // 0.358.0: with every photo of this conversation, swipe or arrows go to the others.
      if (window.JavisLightbox.openFrom) { window.JavisLightbox.openFrom(a); return; }
      var href = a.getAttribute("href") || "";
      window.JavisLightbox.open(href, tenAnh(href));
    }, true);
  }

  var API = { phanTich: phanTich, html: html, chuThich: chuThich, coDungLuong: coDungLuong, tomTat: tomTat, tenAnh: tenAnh };
  if (typeof window !== "undefined") window.JavisHtMedia = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})();
