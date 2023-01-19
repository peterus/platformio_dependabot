import argparse
import os
from pathlib import Path


class ArgumentParser:
    args = None
    parser = None

    def __init__(self):
        self._init_argparse()

    @staticmethod
    def _check_file(path: Path):
        if not os.path.isfile(path):
            from . import die
            die('No valid file: %s', path)

    @staticmethod
    def _check_dir(path: Path):
        if not os.path.isdir(path):
            from . import die
            die('No valid directory: %s', path)

    def _init_argparse(self):
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument('--project_path', required=False, default=".")
        self.parser.add_argument('--github_repo_path', required=True)
        self.parser.add_argument('--github_token', required=False, default=None)
        self.parser.add_argument('--assignee', required=False, default=None)

    def parse_args(self, args):
        self.args = self.parser.parse_args(args)

        self.args.project_path = Path(self.args.project_path)

        self.args.platformio_ini = self.args.project_path / "platformio.ini"
        self._check_dir(self.args.project_path)
        self._check_file(self.args.platformio_ini)

        self.args.github_token = os.environ.get('GITHUB_TOKEN', self.args.github_token)

        return self.args
