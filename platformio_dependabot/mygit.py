#!/usr/bin/python3

from pathlib import Path
from typing import Any, Optional
from git import Repo
from github import UnknownObjectException
from platformio_dependabot.platformio import PackageDefinition


BRANCH_PREFIX = "platformio_dependabot/"


def package_key(package: PackageDefinition) -> str:
    return package.name.replace(" ", "_")


def get_branch_name(package: PackageDefinition) -> str:
    return f"{BRANCH_PREFIX}{package_key(package)}/{package.latestVersion}".replace(" ", "_")


def get_open_update_pull_requests(github_repo: Any, base_branch: str) -> list:
    return [pr for pr in github_repo.get_pulls(state="open", base=base_branch)
            if pr.head.ref.startswith(BRANCH_PREFIX)
            and pr.head.repo is not None and pr.head.repo.full_name == github_repo.full_name]


def get_package_key_of_branch(branch_name: str) -> str:
    return branch_name[len(BRANCH_PREFIX):].rsplit("/", 1)[0]


def close_pull_request(github_repo: Any, pr: Any, comment: str):
    pr.create_issue_comment(comment)
    pr.edit(state="closed")
    github_repo.get_git_ref(f"heads/{pr.head.ref}").delete()


def is_branch_existing_on_github(github_repo: Any, branch_name: str) -> bool:
    try:
        github_repo.get_branch(branch_name)
        return True
    except UnknownObjectException:
        return False


def get_current_ref(repo: Repo) -> str:
    if repo.head.is_detached:
        return repo.head.commit.hexsha
    return repo.active_branch.name


def checkout_remote_branch(repo: Repo, branch_name: str) -> str:
    """Fetch the branch from origin and check it out detached; returns the commit sha."""
    fetch_args = ["origin", f"+refs/heads/{branch_name}:refs/remotes/origin/{branch_name}"]
    if repo.git.rev_parse("--is-shallow-repository") == "true":
        fetch_args.insert(0, "--depth=1")
    repo.git.fetch(*fetch_args)
    repo.git.checkout("-f", "--detach", f"origin/{branch_name}")
    return repo.head.commit.hexsha


def create_branch(repo: Repo, branch_name: str):
    repo.git.checkout("-b", branch_name)


def add_file_commit_and_push(repo: Repo, branch_name: str, platformio_ini: Path, package: PackageDefinition):
    repo.index.add([str(Path(platformio_ini).resolve())])
    repo.index.commit(f"Bump {package.name} to {package.latestVersion}")
    repo.git.push('--set-upstream', 'origin', branch_name)


def restore_ref(repo: Repo, ref: str):
    # -f drops uncommitted changes to tracked files (e.g. a half-updated platformio.ini)
    repo.git.checkout("-f", ref)


def create_pull_request(github_repo: Any, branch_name: str, base_branch: str, package: PackageDefinition, assignee: Optional[str]):
    body = f"Bump {package.name} from {package.currentVersion} to {package.latestVersion}"
    pr = github_repo.create_pull(title=body, body=body, head=branch_name, base=base_branch)
    if assignee:
        pr.add_to_assignees(assignee)
    return pr
