import atexit
import os
import sys

from git import Repo
from github import Auth, Github
from pathlib import Path

from platformio_dependabot import logger, argp, die
from platformio_dependabot.argparser import Configuration
from platformio_dependabot.mygit import add_file_commit_and_push, checkout_remote_branch, create_branch, create_pull_request, get_current_ref, is_branch_existing_on_github, restore_ref
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
    for package in packages:
        logger.info(f"Updating '{package.name}@{package.requirements}' from {package.currentVersion} to {package.latestVersion} ...")

        branch_name = f"platformio_dependabot/{package.name}/{package.latestVersion}"
        branch_name = branch_name.replace(" ", "_")

        try:
            if is_branch_existing_on_github(github_repo, branch_name):
                logger.warning("Pull Request already existing, will do nothing.")
                continue

            if not update_ini_file(config.platformio_ini, package):
                logger.warning("No matching string to replace, will do nothing.")
                continue

            create_branch(repo, branch_name)
            add_file_commit_and_push(repo, branch_name, config.platformio_ini, package)
            create_pull_request(github_repo, branch_name, base_branch, package, config.assignee)
        except Exception as e:
            logger.error(f"Updating '{package.name}' failed: {e}")
            failed.append(package.name)
        finally:
            restore_ref(repo, base_ref)

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
