#!/bin/sh -l

echo $@
printenv

export PYTHONPATH=$PYTHONPATH:/app
python3 -m platformio_dependabot
