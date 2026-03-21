# activity-intelligence

A local command-line tool for logging what you're working on, classifying it with AI, and getting a clear weekly breakdown of where your time actually went.

---

## What it is

You type what you're doing. It stores it, classifies it, and at the end of the week gives you a summary of how you spent your time — including an AI-written review of your focus patterns.

No timers. No categories to pre-define. Just log what you're doing in plain language and let the system figure out the rest.

---

## What it does

- Logs activities from the command line in natural language
- Uses OpenAI to classify each activity into a category
- Links each new event to the previous one to understand transitions
- Stores everything locally in SQLite
- Generates a weekly summary with time breakdowns and an AI review
- Runs a daily checkup showing today's events, category and productivity breakdown, and an optional AI summary
- Exports a clean CSV you can open in Numbers or Excel
- Tracks open work items separately — meaningful tasks like research, university work, writing, and personal projects. Distractions, breaks, and low-value events are not included

---

## Why I made it

I kept losing track of where my time went. I'd end a week having been "busy" the whole time but couldn't say what I'd actually done or how focused I'd been. Most time-tracking tools require too much upfront setup or force you into rigid categories.

This is the version I actually wanted: type one line, get useful data back.

---

## How it works

1. **You log an activity** — a short plain-language description of what you're starting
2. **OpenAI classifies it** — assigns it a category (coding, learning, admin, etc.)
3. **The system links it** — each event records what came before it, so transitions are preserved
4. **It's saved to SQLite** — all events live in a local `activity.db` file
5. **Weekly summary** — run one command to get a time breakdown by category, plus an AI-written review of your week
6. **Daily checkup** — run anytime to see today's events, category breakdown, productivity split, and top activity. If an API key is set, it also generates a short AI summary of how the day went
7. **CSV export** — export all events to a CSV file for analysis in Numbers or Excel
8. **Open work items** — meaningful activities (study sessions, research, writing, personal projects) are tracked as open work items with a title, tag, status, and progress context. Distractions and breaks are excluded. You can view or export these separately to see what larger work is currently in progress

---

## Example workflow

```bash
# Start a new project — run intake first
aiintake

# Log what you're starting
log "starting math revision"
log "scrolling youtube"
log "back to coding"

# View your weekly summary
week

# Run a daily checkup
checkup

# Export to CSV
exportlog

# Open in Numbers
open data/activity_log.csv

# Export open work items
python3 scripts/export_open_work_items_csv.py
```

Running without aliases:

```bash
python3 main.py "starting math revision"
python3 -m app.analytics.weekly
python3 -m app.reports.daily_report
python3 scripts/export_csv.py
```

---

## Screenshots

These are real outputs from the project.

**Terminal logging**
![Terminal log](assets/screenshots/01-terminal-log.png)

**Weekly summary**
![Weekly summary](assets/screenshots/02-weekly-summary.png)

**CSV in Numbers**
![CSV in Numbers](assets/screenshots/03-csv-numbers.png)

**Daily checkup**
![Daily checkup](assets/screenshots/04-daily-summary.png)

**Open work items**
![Open Work Items](assets/screenshots/05-open-work-items.png)

---

## Project structure

```
activity-intelligence/
├── main.py                      # Entry point — log a new activity
├── app/
│   ├── config.py                # Environment and settings
│   ├── db.py                    # Database connection
│   ├── models/activity_event.py # Event data model
│   ├── services/
│   │   ├── classifier.py        # Category classification logic
│   │   └── ai_classifier.py     # OpenAI-powered classification
│   ├── storage/events.py        # Read/write events to SQLite
│   ├── analytics/weekly.py      # Weekly summary and AI review
│   └── reports/daily_report.py  # Daily checkup with category and productivity breakdown
├── scripts/
│   └── export_csv.py            # Export events to CSV
├── assets/
│   ├── commands/run-commands.md # Quick command reference
│   └── screenshots/             # Real output screenshots
└── data/
    └── activity.db              # Local SQLite database (gitignored)
```

---

## Running the project

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Add your API key**

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your-key-here
```

**3. Log an activity**

```bash
python3 main.py "starting deep work session"
```

**4. View weekly summary**

```bash
python3 -m app.analytics.weekly
```

**5. Run a daily checkup**

```bash
python3 -m app.reports.daily_report
```

**6. Export to CSV**

```bash
python3 scripts/export_csv.py
```

**7. Export open work items**

```bash
python3 scripts/export_open_work_items_csv.py
```

---

## Notes and limitations

- **Event-based, not time-tracking** — the system records when you log something, not how long you actually spent on it. Duration is inferred from the gap between events.
- **AI classifications can vary** — OpenAI's categorisation is good but not perfect. Ambiguous descriptions may be classified inconsistently.
- **Local and CLI-first** — there's no web interface, no sync, no mobile app. Everything runs on your machine.
- **You have to remember to log** — this doesn't run in the background. It only knows what you tell it.

---

## Project intake

Before starting work on a new project (or when picking up an existing one), run:

```bash
aiintake
```

The tool reads any existing `project_context.md`, asks 4–5 focused questions in the terminal, then generates:

- **Project understanding** — a short summary of what the project is and where it stands
- **Open questions** — any gaps in what was described
- **Suggested project_context.md** — ready to copy into the file
- **Suggested current_step.md** — a next-step prompt for the AI build assistant

Save the output to a file for reference:

```bash
aiintake > intake.md
# or
python3 scripts/project_intake.py --save   # saves to data/intake_TIMESTAMP.md
```

Shell alias to add to `~/.zshrc`:

```bash
alias aiintake='python3 /path/to/activity-intelligence/scripts/project_intake.py'
```

After intake, continue with the normal workflow (`aiprompt`, `aireviewclip`).

---

## Future improvements

- Better session reconstruction — smarter handling of gaps, idle time, and end-of-day events
- Stronger weekly summaries — trend comparisons, best/worst focus days
- Shortcut automation — faster logging via keyboard shortcuts or menu bar
- Deeper analytics — streaks, category drift over time, time-of-day patterns
