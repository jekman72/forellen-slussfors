#!/bin/sh
# Calendar sync for forellenslussfors.se, run every 30 minutes from cron on an
# always-on machine (the EnergyPilot Pi). Fetches the Airbnb + Booking iCal
# feeds; only when the booked dates have changed it pushes an empty commit, so
# GitHub rebuilds the site with the new calendar. Never touches anything else.
set -eu
cd "$(dirname "$0")/.."
LOG=private/pi_sync.log
STATE=private/last_booked.json
{
  echo "== $(date '+%F %T')"
  git pull --ff-only -q
  python3 tools/update_availability.py >/dev/null
  python3 -c 'import json; print(json.dumps(json.load(open("availability.json"))["booked"]))' > private/booked.now
  if [ ! -f "$STATE" ]; then
    mv private/booked.now "$STATE"; echo "baseline saved"
  elif cmp -s private/booked.now "$STATE"; then
    rm private/booked.now; echo "no change"
  else
    mv private/booked.now "$STATE"
    git -c user.name="Forellen calendar (Pi)" -c user.email="jonasekman72@gmail.com" \
      commit -q --allow-empty -m "Calendar changed, rebuild site (Pi sync)"
    git push -q && echo "changed, pushed"
  fi
} > "$LOG" 2>&1 || { echo "FAILED, see $LOG" >&2; exit 1; }
