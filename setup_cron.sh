#!/bin/bash

# Path to python & agent
AGENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PYTHON_BIN="$(which python3)"
CRON_CMD="0 7 * * 0 $PYTHON_BIN $AGENT_DIR/agent.py --run-now --send-email >> $AGENT_DIR/agent.log 2>&1"

echo "=================================================="
echo " DU 5th Grade Weekly Agent - Sunday Cron Setup"
echo "=================================================="

# Check existing cron
(crontab -l 2>/dev/null | grep -F "$AGENT_DIR/agent.py") >/dev/null
if [ $? -eq 0 ]; then
    echo "[STATUS] Sunday morning cron job is currently ACTIVE!"
    echo "Current schedule: Every Sunday at 7:00 AM"
else
    echo "[STATUS] Cron job is currently NOT installed."
    echo "Adding cron job: Every Sunday at 7:00 AM..."
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "[SUCCESS] Sunday 7:00 AM cron job successfully installed!"
fi

echo "=================================================="
