#!/bin/sh -l

git config --global --add safe.directory /github/workspace

export PYTHONPATH=$PYTHONPATH:/app
python3 -m platformio_dependabot
