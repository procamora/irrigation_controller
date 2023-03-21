#!/bin/bash

i=0


while true; do
  echo "bot_irrigation.py ${i}"
  (( i++ )) || true
  python3 bot_irrigation.py
  sleep 30
done
