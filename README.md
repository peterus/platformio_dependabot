# PlatformIO Dependabot

This Github action is some kind of Dependabot for PlatformIO.
It will help to stay on the current platform and library releases.

## example action for your project

Copy this yml text into this file of your github project: `.github/workflows/dependabot.yml`

```
name: PlatformIO Dependabot

on:
  workflow_dispatch:
  schedule:
    # Runs every day at 00:00
    - cron: '0 0 * * *'

jobs:
  dependabot:
    runs-on: ubuntu-latest
    name: run PlatformIO Dependabot
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      - name: run PlatformIO Dependabot
        uses: peterus/platformio_dependabot@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

Every day at 00:00 this action will be triggered. With the `workflow_dispatch` option enabled, you can also manually trigger the action.
