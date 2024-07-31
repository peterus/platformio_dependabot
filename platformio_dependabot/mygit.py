#!/usr/bin/python3

from typing import Any, Optional
from git import Repo
from platformio_dependabot.platformio import PackageDefinition


def is_branch_existing_on_github(github_repo: Any, branch_name: str) -> bool:
    return branch_name in [b.name for b in list(github_repo.get_branches())]


def create_branch(repo: Repo, branch_name: str):
    repo.git.checkout("-b", branch_name)


def add_file_commit_and_push(repo: Repo, branch_name: str, platformio_ini: str, package: PackageDefinition):
    repo.index.add(f"{platformio_ini}")
    repo.index.commit(f"Bump {package.name} to {package.latestVersion}")
    repo.git(**{}).push(['--set-upstream', 'origin', branch_name])


def get_base_branch(github_repo: Any):
    branches = list(github_repo.get_branches())
    for branch in branches:
        if branch.name == "master":
            return "master"
        if branch.name == "main":
            return "main"
    return None


def checkout_base_branch(repo: Repo, github_repo: Any):
    base_branch = get_base_branch(github_repo)
    repo.git.checkout(base_branch)


def create_pull_request(github_repo: Any, branch_name: str, package: PackageDefinition, assignee: Optional[str]):
    body = f"Bump {package.name} from {package.currentVersion} to {package.latestVersion}"
    pr = github_repo.create_pull(title=body,
                                 body=body, head=branch_name, base=get_base_branch(github_repo))
    if assignee:
        pr.add_to_assignees(assignee)
