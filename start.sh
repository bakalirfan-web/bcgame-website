#!/bin/bash
screen -S bot -X quit 2>/dev/null
screen -S admin -X quit 2>/dev/null
sleep 2
screen -dmS bot bash -c 'cd /storage/T_G/BOTNEWADMINWEB && python3 bot.py > /tmp/bot.log 2>&1'
screen -dmS admin bash -c 'cd /storage/T_G/BOTNEWADMINWEB && python3 admin_web.py > /tmp/admin.log 2>&1'

