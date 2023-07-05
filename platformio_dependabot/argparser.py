
import argparse
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(eq=True, frozen=True)
class Configuration:
    project_path: str
    platformio_ini: str
    github_repo_path: str
    github_token: str
    assignee: str


class ArgumentParser:
    args = None
    parser = None

    def __init__(self):
        self._init_argparse()

    @staticmethod
    def _check_file(path: Path):
        if not os.path.isfile(path):
            from . import die
            die(f"No valid file: {path}")

    @staticmethod
    def _check_dir(path: Path):
        if not os.path.isdir(path):
            from . import die
            die(f"No valid directory: {path}")

    def _init_argparse(self):
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument('--project_path', required=False, default=None)
        self.parser.add_argument('--github_repo_path', required=False, default=None)
        self.parser.add_argument('--github_token', required=False, default=None)
        self.parser.add_argument('--assignee', required=False, default=None)

    def parse_args(self, args) -> Configuration:
        from . import die
        self.args = self.parser.parse_args(args)

        project_path = Path(os.environ.get('INPUT_PROJECT_PATH', "."))
        if self.args.project_path:
            project_path = Path(self.args.project_path)
        self._check_dir(project_path)

        platformio_ini = project_path / "platformio.ini"
        self._check_file(platformio_ini)

        github_repo_path = os.environ.get('GITHUB_REPOSITORY', None)
        if self.args.github_repo_path:
            github_repo_path = self.args.github_repo_path
        if github_repo_path == None:
            die("Must set Github Repository")

        github_token = os.environ.get('INPUT_GITHUB_TOKEN', None)
        if self.args.github_token:
            github_token = self.args.github_token
        if github_token == None:
            die("Must set Github Token")

        assignee = os.environ.get('INPUT_ASSIGNEE', None)
        if self.args.assignee:
            assignee = self.args.assignee

        return Configuration(project_path, platformio_ini, github_repo_path, github_token, assignee)
