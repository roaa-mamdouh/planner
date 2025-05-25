#!/bin/bash
echo "Restarting planner app..."
cd /workspace/development/bench
bench restart
echo "Clearing cache..."
bench --site axe.localhost clear-cache
echo "Done! Planner app has been restarted." 