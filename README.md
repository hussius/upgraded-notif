# upgraded-notifs

Daily email digest of new consulting assignments from [upgraded.se](https://upgraded.se/lediga-uppdrag/), filtered by role categories using Claude.

Runs as a GitHub Actions cron job every morning at 07:00 Stockholm time.

## How it works

1. Fetches all listings via the upgraded.se WordPress REST API
2. Compares against previously seen listing IDs (`data/seen.json`)
3. Sends new listings to Claude Haiku for role classification
4. Emails a digest of matching assignments via Resend
5. Commits the updated `seen.json` back to the repo

## Setup

### 1. Create a GitHub repository

Push this directory to a new GitHub repo (can be private).

### 2. Add GitHub Actions secrets

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `RESEND_API_KEY` | Your Resend API key (from resend.com) |
| `FROM_EMAIL` | Sender address, e.g. `notifier@yourdomain.com` |

> **Resend sender address:** Resend requires a verified domain for the `from` address.
> Sign up at [resend.com](https://resend.com), add and verify your domain, then use
> `something@yourdomain.com` as `FROM_EMAIL`. During testing you can use
> `onboarding@resend.dev` if your recipient email matches your Resend account email.

### 3. Configure roles

Edit `config.json` to add or remove role categories:

```json
{
  "recipient_email": "mikael@codon.se",
  "roles": [
    "AI",
    "Machine learning",
    "Data science",
    "Data engineering",
    "DevOps",
    "Full stack"
  ]
}
```

Commit and push — the next scheduled run will use the updated list.

### 4. Trigger a manual run

To test immediately: go to **Actions → Daily assignment check → Run workflow**.

On first run it will process all current listings and email any that match.
Subsequent runs only process listings not seen before.

## Running locally

```bash
cd scraper
pip install -r requirements.txt
ANTHROPIC_API_KEY=... RESEND_API_KEY=... FROM_EMAIL=... python main.py
```
# upgraded-notif
