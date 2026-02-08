# 🎯 Claude Job Alert System

A Python job search automation tool that searches multiple job boards, uses Claude AI to rank relevance to your profile, and sends you email digests every 2 hours.

## Features

✅ Searches GitHub Jobs, Wellfound, and other job boards
✅ Filters jobs by: Product Owner, Product Manager, Project Manager, Business Analyst
✅ Location filtering: Remote + Boston + US
✅ Uses Claude AI to rank job relevance to your profile
✅ Sends email digests every 2 hours
✅ Prevents duplicate notifications
✅ Runs continuously on Replit (free tier supported)

## Setup Instructions

### Step 1: Get Your API Keys

1. **Anthropic API Key** (for Claude):
   - Go to: https://console.anthropic.com/
   - Create account or login
   - Generate API key
   - Copy the key

2. **Gmail App Password** (already have this):
   - You already generated: `adpvvojceheirsb`

### Step 2: Set Up on Replit

1. Go to: https://replit.com/
2. Create a new Python project
3. Upload or copy-paste these files:
   - `job_alert_system.py` (main script)
   - `requirements.txt` (dependencies)

### Step 3: Add Environment Variables

On Replit, click the "Secrets" button (padlock icon) and add:

```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

### Step 4: Install Dependencies

In Replit terminal, run:
```bash
pip install -r requirements.txt
```

### Step 5: Run the Script

In Replit terminal:
```bash
python job_alert_system.py
```

## How It Works

1. **Search Phase**: Script searches GitHub Jobs and Wellfound for matching positions
2. **Filter Phase**: Claude AI filters and ranks jobs by relevance to your profile
3. **Email Phase**: If good matches found, sends email digest to your inbox
4. **Loop**: Repeats every 2 hours automatically

## Email Format

You'll receive emails like:

```
Subject: 🎯 Job Alerts: 5 Matching Opportunities

Found 5 matching job opportunities for you:

Job ID | Rank | Title | Company | Why It Matches | URL
...
```

## Customization

Edit these in `job_alert_system.py`:

- **JOB_TITLES**: Change job titles you're searching for
- **LOCATIONS**: Modify location preferences
- **CHECK_INTERVAL**: Change from 7200 seconds (2 hours) to different interval
- **GMAIL_ADDRESS**: Change email if needed

## Troubleshooting

**"No emails coming?"**
- Check Replit is running (green "Run" button)
- Verify ANTHROPIC_API_KEY is set in Secrets
- Check spam folder in Gmail
- Check logs in Replit console

**"Module not found error?"**
- Run: `pip install -r requirements.txt`
- Restart Replit project

**"Gmail login failed?"**
- Verify App Password is correct: `adpvvojceheirsb`
- Make sure 2FA is enabled on Gmail account
- Regenerate App Password if needed

## Job Sources

- **GitHub Jobs**: Free, tech-focused roles
- **Wellfound**: Startup funding data with job postings
- **Indeed**: (Requires publisher ID, currently disabled)

To add Indeed:
1. Sign up for Indeed Publisher at: https://opensource.indeedeng.io/
2. Get publisher ID
3. Add to environment variables
4. Uncomment Indeed search in script

## Cost

✅ **FREE**
- Replit: Free tier (covers continuous running)
- Anthropic Claude: $0.003 per 1K input tokens (very affordable for job filtering)
- Gmail SMTP: Free
- Job APIs: Free tiers used

Estimated monthly cost: **$1-3 for Claude API usage** (optional, can upgrade)

## Support

If you need to modify:
1. Job search criteria
2. Email format
3. Search frequency
4. Add new job boards

Just let me know and I'll update the script!

---

**Created with Claude AI** | Fully customizable automation system
