import os

import requests

API_URL = "https://xvnvhpewkimiozhfuyco.supabase.co/rest/v1/tenders"
DASHBOARD_URL = "https://offentlig.ai/dashboard"


def fetch_listings(page_size: int = 200) -> list[dict]:
    """Fetch recent tenders from offentlig.ai via Supabase REST API."""
    api_key = os.environ["OFFENTLIG_API_KEY"]
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
    }

    resp = requests.get(
        API_URL,
        params={
            "select": "tender_hash,title,text,publication_date,tender_url,source_url,deadline_date",
            "order": "created_at.desc",
            "limit": page_size,
        },
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()

    return [
        {
            "id": f"offentlig:{item['tender_hash']}",
            "title": item["title"] or "",
            "content": item["text"] or "",
            "date": (item["publication_date"] or "")[:10],
            "link": item["source_url"] or item["tender_url"] or DASHBOARD_URL,
            "source": "offentlig.ai",
        }
        for item in resp.json()
        if item.get("tender_hash") and item.get("title")
    ]
