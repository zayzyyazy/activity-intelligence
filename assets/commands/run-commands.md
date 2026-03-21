# Project intake (run before starting or resuming a project)
aiintake
python3 scripts/project_intake.py --save   # saves to data/intake_TIMESTAMP.md

# Run app
log "starting math revision"
log "scrolling youtube"
log "back to coding"

# Weekly summary
week

# Daily checkup
day

# Export CSV
exportlog

# Open CSV in Numbers
open data/activity_log.csv

# Run without aliases
python3 main.py "starting math revision"
python3 -m app.analytics.weekly
python3 -m app.reports.daily_report
python3 scripts/export_csv.py
