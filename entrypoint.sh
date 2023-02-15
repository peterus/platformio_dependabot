#!/bin/sh -l

export PYTHONPATH=$PYTHONPATH:/app
python3 -m platformio_dependabot
