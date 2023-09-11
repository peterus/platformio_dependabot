# PlatformIO Dependabot

This Github action is some kind of Dependabot for [PlatformIO](https://github.com/platformio/platformio-core).
It will help to stay on the current platform and library releases.

## Inputs

| Variable      | Description                             | Type                                     | Required |
| ------------- | --------------------------------------- | ---------------------------------------- |--------- |
| github_token  | Github Token to create the MR           | Secure String                            | Yes      |
| assignee      | MR will be assigned to this Github user | User String                              | No       |
| project_path  | Path to platformio.ini file (default will be root folder) | Path inside repository | No       |

## Example Usage

Use this example in your project: `.github/workflows/dependabot.yml`

```
name: PlatformIO Dependabot

on:
  workflow_dispatch: # option to manually trigger the workflow
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
