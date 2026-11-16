import atexit
import os
import sys

from git import Repo
from github import Auth, Github
from pathlib import Path

from platformio_dependabot import logger, argp, die
from platformio_dependabot.argparser import Configuration
from platformio_dependabot.mygit import add_file_commit_and_push, checkout_remote_branch, close_pull_request, create_branch, create_pull_request, get_branch_name, get_current_ref, get_open_update_pull_requests, get_package_key_of_branch, is_branch_existing_on_github, package_key, restore_ref
from platformio_dependabot.platformio import get_outdated_libraries, install_libraries, update_ini_file
from platformio_dependabot.time import print_execution_time


def update_packages(config: Configuration, github_repo, repo: Repo, base_branch: str) -> list:
    """Look for outdated packages on base_branch and open a pull request for each; returns the failed package names."""
    base_ref = checkout_remote_branch(repo, base_branch)

    logger.info("Installing PlatformIO Libraries...")
    install_libraries(config.project_path)

    logger.info("getting data from PlatformIO, this will take a while...")
    packages = get_outdated_libraries(config.project_path)

    failed = []
    created = {}
    for package in packages:
        logger.info(f"Updating '{package.name}@{package.requirements}' from {package.currentVersion} to {package.latestVersion} ...")

        branch_name = get_branch_name(package)

        try:
            if is_branch_existing_on_github(github_repo, branch_name):
                logger.warning("Pull Request already existing, will do nothing.")
                continue

            if not update_ini_file(config.platformio_ini, package):
                logger.warning("No matching string to replace, will do nothing.")
                continue

            create_branch(repo, branch_name)
            add_file_commit_and_push(repo, branch_name, config.platformio_ini, package)
            created[branch_name] = create_pull_request(github_repo, branch_name, base_branch, package, config.assignee)
        except Exception as e:
            logger.error(f"Updating '{package.name}' failed: {e}")
            failed.append(package.name)
        finally:
            restore_ref(repo, base_ref)

    failed_keys = {package_key(p) for p in packages if p.name in failed}
    failed += close_outdated_pull_requests(github_repo, base_branch, packages, created, failed_keys)
    return failed


def close_outdated_pull_requests(github_repo, base_branch: str, packages: list, created: dict, skip_keys: set) -> list:
    """Close update PRs superseded by a newer version or whose package is up to date; returns what failed."""
    wanted = {package_key(p): get_branch_name(p) for p in packages}
    open_pulls = get_open_update_pull_requests(github_repo, base_branch)
    open_by_branch = {pr.head.ref: pr for pr in open_pulls} | created

    failed = []
    for pr in open_pulls:
        branch_name = pr.head.ref
        key = get_package_key_of_branch(branch_name)
        if branch_name in wanted.values() or key in skip_keys:
            continue

        if key not in wanted:
            comment = f"`{key}` is up to date on `{base_branch}`, closing this pull request."
        elif wanted[key] in open_by_branch:
            comment = f"Superseded by #{open_by_branch[wanted[key]].number}."
        else:
            # newer version known, but no pull request for it (e.g. it was closed by hand): keep this one
            continue

        logger.info(f"Closing #{pr.number} ({branch_name}): {comment}")
        try:
            close_pull_request(github_repo, pr, comment)
        except Exception as e:
            logger.error(f"Closing #{pr.number} failed: {e}")
            failed.append(f"#{pr.number}")
    return failed


def main():
    config: Configuration = argp.parse_args(sys.argv[1:])
    atexit.register(print_execution_time)

    github_repo = Github(auth=Auth.Token(config.github_token)).get_repo(config.github_repo_path)
    base_branch = config.base_branch or github_repo.default_branch
    logger.info(f"Base branch: {base_branch}")

    repo = Repo(Path(os.environ.get("GITHUB_WORKSPACE", ".")), search_parent_directories=True)
    start_ref = get_current_ref(repo)
    try:
        failed = update_packages(config, github_repo, repo, base_branch)
    finally:
        restore_ref(repo, start_ref)

    if failed:
        die(f"Failed to update: {', '.join(failed)}")


if __name__ == '__main__':
    main()
