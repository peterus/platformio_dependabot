import atexit
import sys

from git import Repo
from github import Github
from pathlib import Path

from platformio_dependabot import logger, argp
from platformio_dependabot.argparser import Configuration
from platformio_dependabot.mygit import add_file_commit_and_push, checkout_base_branch, create_branch, create_pull_request, is_branch_existing_on_github
from platformio_dependabot.platformio import get_outdated_libraries, install_libraries, update_ini_file
from platformio_dependabot.time import print_execution_time


def main():
    config: Configuration = argp.parse_args(sys.argv[1:])
    atexit.register(print_execution_time)

    logger.info("Installing PlatformIO Libraries...")
    install_libraries(config.project_path)

    logger.info("getting data from PlatformIO, this will take a while...")
    packages = get_outdated_libraries(config.project_path)

    for package in packages:
        logger.info(f"Updating '{package.name}' to {package.latestVersion} ...")

        branch_name = f"platformio_dependabot/{package.name}/{package.latestVersion}"
        branch_name = branch_name.replace(" ", "_")

        github_repo = Github(config.github_token).get_repo(config.github_repo_path)

        if is_branch_existing_on_github(github_repo, branch_name):
            logger.warning("Pull Request already existing, will do nothing.")
            continue

        repo = Repo(Path("/github/workspace"))
        create_branch(repo, branch_name)

        update_ini_file(config.platformio_ini, package)

        add_file_commit_and_push(repo, branch_name, config.platformio_ini, package)
        checkout_base_branch(repo, github_repo)
        create_pull_request(github_repo, branch_name, package, config.assignee)


if __name__ == '__main__':
    main()
