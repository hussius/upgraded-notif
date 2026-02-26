import json
import os

import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def analyze_listing(listing: dict, roles: list[str]) -> list[str]:
    """Return the subset of `roles` that this listing matches."""
    roles_str = "\n".join(f"- {r}" for r in roles)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": f"""Classify this consulting assignment against a set of role categories.

Title: {listing['title']}
Description: {listing['content'][:2000]}

Role categories:
{roles_str}

Which categories does this assignment match? A match means the role is primarily about that type of work. Be inclusive but accurate — a full-stack role with heavy ML work should match both.

Respond with ONLY a JSON array of matching category names, exactly as written above.
If none match, respond with [].

Examples of valid responses:
["AI", "Machine learning"]
["Full stack"]
[]""",
            }
        ],
    )

    text = message.content[0].text.strip()
    try:
        matched = json.loads(text)
        return [r for r in matched if r in roles]
    except (json.JSONDecodeError, TypeError):
        return []
