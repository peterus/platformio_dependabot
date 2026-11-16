# PlatformIO Dependabot

This Github action is some kind of Dependabot for [PlatformIO](https://github.com/platformio/platformio-core).
It will help to stay on the current platform and library releases.

The action runs a prebuilt Docker image from the GitHub Container Registry, so no image has to be
built on every run.

## Inputs

| Variable      | Description                             | Type                                     | Required |
| ------------- | --------------------------------------- | ---------------------------------------- |--------- |
| github_token  | Github Token to create the MR           | Secure String                            | Yes      |
| assignee      | MR will be assigned to this Github user | User String                              | No       |
| base_branch   | Branch the updates are based on and the pull requests are opened against (default: the repository's default branch) | Branch name | No       |
| project_path  | Directory containing `platformio.ini`, relative to the repository root (default: repository root) | Path inside repository | No       |

## Example Usage

Use this example in your project: `.github/workflows/dependabot.yml`

```
name: PlatformIO Dependabot

on:
  workflow_dispatch: # option to manually trigger the workflow
  schedule:
    # Runs every day at 00:00
    - cron: '0 0 * * *'

permissions:
  contents: write       # push the update branches
  pull-requests: write  # open the pull requests

jobs:
  dependabot:
    runs-on: ubuntu-latest
    name: run PlatformIO Dependabot
    steps:
      - name: Checkout
        uses: actions/checkout@v6
      - name: run PlatformIO Dependabot
        uses: peterus/platformio_dependabot@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          # project_path: firmware   # if platformio.ini is not in the repository root
```

## Repository settings

* Pull requests are opened against `base_branch` (default: the repository's **default branch**).
* Under *Settings → Actions → General → Workflow permissions* enable
  **"Allow GitHub Actions to create and approve pull requests"**. Without it the branch is pushed,
  but opening the pull request fails.
* Pull requests created with the default `GITHUB_TOKEN` do **not** trigger other workflows
  (e.g. your CI build). If you want CI to run on them, pass a fine-grained personal access token
  (or a GitHub App token) with *Contents* and *Pull requests* write access as `github_token` instead.

## Behaviour

* The update branches are always created from the latest `base_branch` on GitHub, no matter which
  branch the workflow was started on.
* For every outdated library or platform a branch `platformio_dependabot/<name>/<version>` is pushed
  and a pull request is opened. If that branch already exists, the package is skipped.
* If updating a single package fails, the remaining packages are still processed and the
  workflow run fails at the end.
