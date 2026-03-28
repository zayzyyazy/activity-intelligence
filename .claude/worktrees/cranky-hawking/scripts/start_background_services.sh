#!/bin/zsh

cd ~/Desktop/Projects/activity-intelligence || exit 1

mkdir -p logs

nohup python3 scripts/watch_activity_inbox.py > logs/activity_inbox.log 2>&1 &
nohup python3 scripts/watch_activitywatch_import.py > logs/activitywatch_sync.log 2>&1 &
nohup python3 scripts/watch_reminder_inbox_poll.py > logs/reminder_poll.log 2>&1 &
