#!/bin/bash
cd /Users/zay/Desktop/Projects/activity-intelligence
python3 main.py "$@" > reports/latest_output.txt 2>&1
