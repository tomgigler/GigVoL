#!/bin/bash

ps -ef | grep $(pwd)/gigvol.py | grep -v grep | awk  '{print "kill " $2}' | /bin/bash

python3 $(pwd)/gigvol.py &
