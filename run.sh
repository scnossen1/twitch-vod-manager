#!/bin/sh
while true; do
    echo "=== Starting download cycle: $(date) ==="
    python twitch_downloader.py
    
    echo "=== Running cleanup script: $(date) ==="
    python cleanup.py
    
    echo "Cycle complete. Sleeping for 2 hours..."
    sleep 7200
done