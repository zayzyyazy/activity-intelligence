# Run app
log "starting math revision"
log "scrolling youtube"
log "back to coding"

# Weekly summary
week

# Export CSV
exportlog

# Open CSV in Numbers
open data/activity_log.csv

# Run without aliases
python3 main.py "starting math revision"
python3 -m app.analytics.weekly
python3 scripts/export_csv.py
