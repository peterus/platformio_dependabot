#!/bin/sh -l

git config --global --add safe.directory /github/workspace
git config --global user.name 'github-actions[bot]'
git config --global user.email 'github-actions[bot]@users.noreply.github.com'

export PYTHONPATH=$PYTHONPATH:/app
python3 -m platformio_dependabot
