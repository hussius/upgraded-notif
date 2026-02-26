import html
import re
import requests

API_URL = "https://upgraded.se/wp-json/wp/v2/konsultuppdrag"


def strip_html(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw)
    return html.unescape(text).strip()


def fetch_listings(max_pages: int = 10) -> list[dict]:
    """Fetch all current listings from the upgraded.se REST API."""
    listings = []
    page = 1

    while page <= max_pages:
        resp = requests.get(
            API_URL,
            params={
                "per_page": 100,
                "page": page,
                "_fields": "id,title,content,excerpt,date,link",
                "orderby": "date",
                "order": "desc",
            },
            timeout=30,
        )

        if resp.status_code in (400, 404):
            break
        resp.raise_for_status()

        batch = resp.json()
        if not batch:
            break

        listings.extend(
            {
                "id": str(item["id"]),
                "title": strip_html(item["title"]["rendered"]),
                "content": strip_html(item["content"]["rendered"]),
                "date": item["date"][:10],
                "link": item["link"],
            }
            for item in batch
        )

        total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
        if page >= total_pages:
            break
        page += 1

    return listings
