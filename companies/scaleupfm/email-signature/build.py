#!/usr/bin/env python3
"""Build and check the ScaleUp mailbox signature (ORG-416; client-mailbox service standard).

Same approach as ``clients/stromy/email-signature/build.py``: one template, per-person
selections in ``people.json`` (this folder) resolved against the brand's people register
(``../people.json``), one hosted https logo, a plain-text twin, and the same signature
rules. Outputs:

* ``signatures.json``  the catalog the ms365 signature hook and persona-outreach read
  (``mailbox``, ``aliases``, ``ready``, ``signature_html``/``signature_text``,
  ``reply_html``/``reply_text``), keyed by sender ID.
* ``preview/<sender_id>.html`` / ``.txt``  a light and dark-background preview, and the text twin.
* ``install/<sender_id>[-reply].html``  clean copy-and-paste pages (only the signature on the page).
* ``index.html``  the install instructions for Outlook on the web, desktop and phone.
* ``../templates/html/``  the brand's signature templates, regenerated from the same source.

Usage:
    build.py                 write the outputs
    build.py --check         fail (exit 1) if outputs are stale or a signature breaks the rules
    build.py --require-ready also fail while a sender has pending details
    build.py --senders-py PATH  also run Stromy's authoritative validate_signature_html
                             (Stromy/stromy/agents/email_agents/utils/signatures.py)

Stdlib only. The local rules are imported from the Stromy builder, so both brands are checked
by one copy of them; --senders-py proves they still agree with Stromy's validator.
"""
from __future__ import annotations

import argparse
import html
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PEOPLE = HERE / "people.json"
REGISTRY = HERE.parent / "people.json"
OUT = HERE / "signatures.json"
PREVIEW = HERE / "preview"
INSTALL = HERE / "install"
TEMPLATES = HERE.parent / "templates" / "html"
STROMY_BUILDER = HERE.parent.parent / "stromy" / "email-signature" / "build.py"

# Brand tokens (charter.json / tokens.css), email-safe: Archivo is a web font, so the
# charter's webSafe fallbacks stand in (heading Arial, body Segoe UI).
NAVY = "#0A1F3D"     # name, title, links (Midnight Navy)
AMBER = "#E8A33D"    # the one amber signal per surface: the rule
MUTED = "#6B7280"    # tagline
HEAD = "Arial, Helvetica, sans-serif"
BODY = "'Segoe UI', Arial, Helvetica, sans-serif"
TAGLINE = "Start to Scale"
BRAND = "ScaleUp Financial Management"

# ONE hosted https image: the brand logo the website already serves from its brand overlay
# (client-data logos/logo.png, synced to the site's public/brand/logos/). 690x168 source,
# shown at 140x34 so it stays sharp on high-density screens.
LOGO_URL = "https://www.scaleupfm.com/brand/logos/logo.png"
LOGO_W, LOGO_H = 140, 34
SENDER_DOMAINS = {"scaleupfm.com"}


def _load_rules():
    spec = importlib.util.spec_from_file_location("stromy_signature_build", STROMY_BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.local_validate, mod.PLACEHOLDER


local_validate, PLACEHOLDER = _load_rules()


def _link(href: str, label: str) -> str:
    return (f'<a href="{html.escape(href, quote=True)}" style="color:{NAVY};text-decoration:none;" '
            f'target="_blank">{html.escape(label)}</a>')


def render(person: dict) -> tuple[str, str]:
    """Return (signature_html, signature_text) for one person."""
    name, title = person["name"], person.get("title") or ""
    rows, text = [], [name]
    if title:
        text.append(f"{title}, {BRAND}")
    else:
        text.append(BRAND)

    def row(inner: str) -> None:
        rows.append(f'<tr><td style="padding:0 0 2px 0;font-family:{BODY};font-size:12px;line-height:18px;'
                    f'color:{NAVY};">{inner}</td></tr>')

    if person.get("phone"):
        row(_link("tel:" + re.sub(r"[^\d+]", "", person["phone"]), person["phone"]))
        text.append(person["phone"])
    if person.get("email"):
        row(_link(f"mailto:{person['email']}", person["email"]))
        text.append(person["email"])
    row(_link(person["website_url"], person["website_label"]))
    text.append(person["website_url"])
    if person.get("linkedin"):
        row(_link(person["linkedin"], "LinkedIn"))
        text.append(f"LinkedIn {person['linkedin']}")
    text.append(TAGLINE)

    title_row = (f'<tr><td style="font-family:{BODY};font-size:12px;line-height:18px;color:{NAVY};'
                 f'padding:0 0 6px 0;">{html.escape(title)}</td></tr>') if title else ""
    sig = (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" bgcolor="#FFFFFF" '
        'style="border-collapse:collapse;mso-table-lspace:0pt;mso-table-rspace:0pt;background-color:#FFFFFF;"><tr>'
        f'<td width="2" style="width:2px;background-color:{AMBER};font-size:0;line-height:0;">&nbsp;</td>'
        '<td valign="top" style="padding:6px 8px 6px 12px;">'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">'
        f'<tr><td style="font-family:{HEAD};font-size:16px;line-height:21px;font-weight:bold;color:{NAVY};">'
        f'{html.escape(name)}</td></tr>'
        f'{title_row}'
        f'{"".join(rows)}'
        f'<tr><td style="padding:8px 0 0 0;"><img src="{LOGO_URL}" width="{LOGO_W}" height="{LOGO_H}" '
        f'alt="{BRAND}" border="0" style="display:block;border:0;outline:none;width:{LOGO_W}px;height:{LOGO_H}px;"></td></tr>'
        f'<tr><td style="font-family:{BODY};font-size:11px;line-height:16px;font-style:italic;color:{MUTED};'
        f'padding:4px 0 0 0;">{TAGLINE}</td></tr>'
        '</table></td></tr></table>')
    return sig, "\n".join(text)


def render_reply(person: dict) -> tuple[str, str]:
    links = [_link(person["website_url"], person["website_label"])]
    text = [person["website_label"]]
    if person.get("phone"):
        links.insert(0, _link("tel:" + re.sub(r"[^\d+]", "", person["phone"]), person["phone"]))
        text.insert(0, person["phone"])
    markup = (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" bgcolor="#FFFFFF" '
        f'style="background-color:#FFFFFF;border-collapse:collapse;font-family:{BODY};font-size:12px;line-height:19px;">'
        f'<tr><td style="color:{NAVY};font-weight:bold;">{html.escape(person["name"])} &middot; ScaleUp</td></tr>'
        f'<tr><td>{" &middot; ".join(links)}</td></tr></table>')
    return markup, f'{person["name"]} · ScaleUp\n' + " · ".join(text)


def load_people() -> list[dict]:
    data = json.loads(PEOPLE.read_text())
    by_id = {p["id"]: p for p in json.loads(REGISTRY.read_text())}
    resolved, seen = [], set()
    for selection in data["people"]:
        sid = selection["sender_id"]
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", sid) or sid in seen:
            raise ValueError(f"invalid or duplicate signature sender ID: {sid!r}")
        seen.add(sid)
        person = by_id[selection["person_id"]]
        contact = {k: person.get(k) for k in ("name", "title", "email", "phone", "linkedin", "emailAliases")}
        resolved.append({**data["defaults"], **contact, **selection})
    return resolved


def build() -> dict:
    out = {}
    for p in load_people():
        sig_html, sig_text = render(p)
        reply_html, reply_text = render_reply(p)
        pending = list(p.get("pending_fields", []))
        email = p.get("email") or ""
        if email.rpartition("@")[2].lower() not in SENDER_DOMAINS and "sending_email" not in pending:
            pending.append("sending_email")
        out[p["sender_id"]] = {
            "sender_id": p["sender_id"], "name": p["name"], "mailbox_role": p.get("mailbox_note", ""),
            "mailbox": email, "aliases": p.get("emailAliases") or [],
            "ready": not pending and not (PLACEHOLDER.search(sig_html) or PLACEHOLDER.search(sig_text)),
            "pending_fields": pending,
            "signature_html": sig_html, "signature_text": sig_text,
            "reply_html": reply_html, "reply_text": reply_text,
        }
    return out


def preview_page(entry: dict) -> str:
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Signature preview</title>'
        '<style>body{font-family:Arial;margin:12px}.p{padding:8px;margin:0 0 16px;border:1px solid #ccc;max-width:560px}'
        'pre{white-space:pre-wrap;overflow-wrap:anywhere}.l{background:#fff}.d{background:#1f1f23;color:#e6e6ea}</style>'
        f'<h3>{html.escape(entry["name"])}</h3>'
        f'<p>{"Ready for installation" if entry["ready"] else "Draft: confirm " + html.escape(", ".join(entry["pending_fields"]))}</p>'
        f'<div class="p l"><p>Full signature</p>{entry["signature_html"]}</div>'
        f'<div class="p d"><p>Full signature on a dark message background</p>{entry["signature_html"]}</div>'
        f'<div class="p l"><p>Reply signature</p>{entry["reply_html"]}</div>'
        f'<pre>{html.escape(entry["signature_text"])}</pre></html>\n')


def install_page(markup: str, name: str) -> str:
    # No visible instructions: Cmd+A / Ctrl+A copies only the signature.
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(name)} - ScaleUp signature</title>'
            '<body style="margin:0;padding:8px;background:#fff;">' + markup + '</body></html>\n')


INSTALL_STEPS = (
    '<h2>Install (about five minutes)</h2>'
    '<p>Open <em>Copy full signature</em>, press Cmd+A then Cmd+C (Ctrl+A, Ctrl+C on Windows). '
    'Paste it with Cmd+V (Ctrl+V) into the signature box, then do the same with <em>Copy reply signature</em>.</p>'
    '<ul>'
    '<li><strong>Outlook on the web</strong> (outlook.office.com): Settings (gear) &rarr; Account &rarr; Signatures '
    '(older layout: Mail &rarr; Compose and reply). Add <em>ScaleUp full</em> and <em>ScaleUp reply</em>, '
    'pick the full one for new messages and the reply one for replies and forwards, save.</li>'
    '<li><strong>Outlook on the laptop</strong>: new Outlook (Mac or Windows) uses the same Settings &rarr; '
    'Account &rarr; Signatures and syncs with the web. Classic Outlook for Windows: File &rarr; Options &rarr; '
    'Mail &rarr; Signatures. Legacy Outlook for Mac: Outlook &rarr; Settings &rarr; Signatures. '
    'Choose the ScaleUp account as the one the defaults apply to.</li>'
    '<li><strong>Outlook on the phone</strong>: Settings &rarr; Signature, pick the ScaleUp account and paste the '
    'text version (the phone app keeps its own, simpler signature).</li>'
    '</ul>'
    '<p>Then send one mail to yourself and check: the logo shows, there is no attachment icon, and the links open.</p>')


def output_files(built: dict) -> dict[Path, str]:
    files = {OUT: json.dumps(built, indent=2, ensure_ascii=False) + "\n"}
    items = []
    for sid, entry in built.items():
        files[PREVIEW / f"{sid}.html"] = preview_page(entry)
        files[PREVIEW / f"{sid}.txt"] = entry["signature_text"] + "\n"
        files[INSTALL / f"{sid}.html"] = install_page(entry["signature_html"], entry["name"])
        files[INSTALL / f"{sid}-reply.html"] = install_page(entry["reply_html"], entry["name"])
        state = "Ready" if entry["ready"] else "Draft: " + ", ".join(entry["pending_fields"])
        items.append(
            f'<li><strong>{html.escape(entry["name"])}</strong> ({html.escape(entry["mailbox"])}): {html.escape(state)}<br>'
            f'<a href="preview/{sid}.html">Preview</a> · <a href="install/{sid}.html">Copy full signature</a> · '
            f'<a href="install/{sid}-reply.html">Copy reply signature</a></li>')
    files[HERE / "index.html"] = (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>ScaleUp email signature</title><body style="font-family:Arial;max-width:760px;margin:24px;line-height:1.6">'
        '<h1>Your ScaleUp email signature</h1><ol>' + "".join(items) + '</ol>' + INSTALL_STEPS + '</body></html>\n')
    first = next(iter(built.values()))
    files[TEMPLATES / "email-signature.html"] = first["signature_html"] + "\n"
    files[TEMPLATES / "signatures" / "icon.fragment.html"] = first["signature_html"] + "\n"
    files[TEMPLATES / "signatures" / "text-only.fragment.html"] = first["reply_html"] + "\n"
    files[TEMPLATES / "signatures" / "mobile-plaintext.txt"] = first["signature_text"] + "\n"
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--require-ready", action="store_true")
    ap.add_argument("--senders-py")
    args = ap.parse_args()
    built = build()
    authoritative = None
    if args.senders_py:
        spec = importlib.util.spec_from_file_location("signatures", args.senders_py)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        authoritative = mod.validate_signature_html
    problems = []
    for sid, e in built.items():
        for key in ("signature_html", "reply_html"):
            try:
                local_validate(e[key])
                if authoritative:
                    authoritative(e[key])
            except ValueError as exc:
                problems.append(f"{sid} {key}: {exc}")
        if len(e["signature_html"]) > 5000:
            problems.append(f"{sid}: html over 5000 chars (transport-rule limit)")
        if not e["ready"]:
            msg = f"{sid}: confirm {', '.join(e['pending_fields']) or 'unresolved placeholder'}"
            if args.require_ready:
                problems.append(msg)
            else:
                print("WARN " + msg)
    for path, rendered in output_files(built).items():
        if args.check:
            if not path.exists() or path.read_text() != rendered:
                problems.append(f"{path.relative_to(HERE.parent)} is stale; run build.py")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered)
    for p in problems:
        print("FAIL", p)
    print(f"{len(built)} signatures, {len(problems)} problems" + (" (Stromy validator used)" if authoritative else ""))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
