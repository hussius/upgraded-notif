import os
from collections import defaultdict

import resend


def _listing_html(listing: dict) -> str:
    roles_str = ", ".join(listing["matched_roles"])
    return f"""
<div style="margin-bottom:20px;padding:16px;border:1px solid #e0e0e0;border-radius:8px;font-family:sans-serif;">
  <h3 style="margin:0 0 6px 0;">
    <a href="{listing['link']}" style="color:#1a1a1a;text-decoration:none;">{listing['title']}</a>
  </h3>
  <p style="margin:0 0 8px 0;color:#888;font-size:13px;">Posted {listing['date']}</p>
  <p style="margin:0;font-size:13px;">
    <span style="background:#e8f0fe;color:#1a73e8;padding:2px 8px;border-radius:12px;font-weight:600;">{roles_str}</span>
  </p>
</div>"""


def _source_section_html(source: str, listings: list[dict]) -> str:
    items_html = "\n".join(_listing_html(m) for m in listings)
    count = len(listings)
    return f"""
<h3 style="margin:24px 0 12px 0;padding-bottom:6px;border-bottom:2px solid #e0e0e0;color:#555;">
  {source} — {count} match{'es' if count != 1 else ''}
</h3>
{items_html}"""


def send_notification(matches: list[dict], config: dict) -> None:
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        raise EnvironmentError("RESEND_API_KEY is not set or empty")
    resend.api_key = api_key
    from_addr = os.environ.get("FROM_EMAIL", "onboarding@resend.dev")

    by_source: dict[str, list] = defaultdict(list)
    for m in matches:
        by_source[m.get("source", "unknown")].append(m)

    count = len(matches)
    sources_str = " + ".join(by_source.keys())
    subject = f"[{sources_str}] {count} new matching result{'s' if count != 1 else ''}"

    sections_html = "\n".join(
        _source_section_html(source, listings)
        for source, listings in by_source.items()
    )
    watching = ", ".join(config["roles"])

    html = f"""<!DOCTYPE html>
<html>
<body style="font-family:sans-serif;max-width:620px;margin:40px auto;padding:0 16px;color:#1a1a1a;">
  <h2 style="margin-bottom:4px;">New matching results</h2>
  <p style="color:#555;margin-top:0;">
    {count} new result{'s' if count != 1 else ''} matched your role criteria.
  </p>
  {sections_html}
  <hr style="border:none;border-top:1px solid #e0e0e0;margin:24px 0;">
  <p style="color:#aaa;font-size:12px;margin:0;">Watching: {watching}</p>
</body>
</html>"""

    resend.Emails.send(
        {
            "from": from_addr,
            "to": [config["recipient_email"]],
            "subject": subject,
            "html": html,
        }
    )
    print(f"Email sent to {config['recipient_email']}")
