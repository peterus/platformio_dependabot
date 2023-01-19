import atexit
import sys

from git import Repo
from github import Github

from platformio_dependabot import logger, argp
from platformio_dependabot.git import add_file_commit_and_push, checkout_base_branch, create_branch, create_pull_request, is_branch_existing_on_github
from platformio_dependabot.platformio import get_outdated_libraries, update_ini_file
from platformio_dependabot.time import print_execution_time


def main():
    args = argp.parse_args(sys.argv[1:])
    atexit.register(print_execution_time)

    logger.info("getting data from PlatformIO, this will take a while...")
    packages = get_outdated_libraries(args.project_path)

    for package in packages:
        logger.info(f"Updating '{package.name}' to {package.latestVersion} ...")

        branch_name = f"platformio_dependabot/{package.name}/{package.latestVersion}"

        github_repo = Github(args.github_token).get_repo(args.github_repo_path)

        if is_branch_existing_on_github(github_repo, branch_name):
            logger.warning("Pull Request already existing, will do nothing.")
            continue

        repo = Repo(args.project_path)
        create_branch(repo, branch_name)

        update_ini_file(args.platformio_ini, package)

        add_file_commit_and_push(repo, branch_name, args.platformio_ini, package)
        checkout_base_branch(repo)
        create_pull_request(repo, github_repo, branch_name, package, args.assignee)


if __name__ == '__main__':
    main()
