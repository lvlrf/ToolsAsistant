#!/bin/bash
#
# Dashboard Update Script
# Runs aggregator.py to update dashboard data
#

COLLECTOR_DIR="/opt/fastly-collector"
PYTHON_CMD="/opt/fastly-collector/venv/bin/python3"
LOG_FILE="$COLLECTOR_DIR/aggregator.log"

cd $COLLECTOR_DIR

echo "[$(date)] Starting aggregation..." >> $LOG_FILE
$PYTHON_CMD aggregator.py >> $LOG_FILE 2>&1
echo "[$(date)] Aggregation complete" >> $LOG_FILE
