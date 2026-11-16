import subprocess
from unittest import mock

import pytest
from git import Repo
from github import UnknownObjectException

import platformio_dependabot.__main__ as app
from platformio_dependabot.argparser import Configuration
from platformio_dependabot.platformio import PackageDefinition

INI = "[env:native]\nlib_deps = bblanchon/ArduinoJson @ ^6.21.3\n"


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def remote(tmp_path):
    """Bare remote with 'main' (default) and 'develop' (one commit ahead)."""
    seed = tmp_path / "seed"
    seed.mkdir()
    git(seed, "init", "-q", "-b", "main")
    git(seed, "config", "user.email", "t@t")
    git(seed, "config", "user.name", "t")
    (seed / "platformio.ini").write_text(INI)
    git(seed, "add", ".")
    git(seed, "commit", "-qm", "init")
    git(seed, "checkout", "-qb", "develop")
    (seed / "src.txt").write_text("develop work")
    git(seed, "add", ".")
    git(seed, "commit", "-qm", "develop work")
    bare = tmp_path / "remote.git"
    git(tmp_path, "clone", "-q", "--bare", str(seed), str(bare))
    return bare


def clone(tmp_path, remote, branch, shallow=False):
    work = tmp_path / "work"
    args = ["clone", "-q", "-b", branch]
    if shallow:
        args += ["--depth=1"]
    git(tmp_path, *args, f"file://{remote}", str(work))
    git(work, "config", "user.email", "t@t")
    git(work, "config", "user.name", "t")
    return work


def run(work, base_branch, packages):
    config = Configuration(str(work), str(work / "platformio.ini"), "o/r", "token", None, base_branch)
    github_repo = mock.MagicMock()
    github_repo.get_branch.side_effect = UnknownObjectException(404, {}, {})
    with mock.patch.object(app, "install_libraries"), \
            mock.patch.object(app, "get_outdated_libraries", return_value=packages):
        failed = app.update_packages(config, github_repo, Repo(work), base_branch)
    return failed, github_repo


ARDUINOJSON = PackageDefinition("ArduinoJson", "6.21.6", "7.4.3", "^6.21.3")
BRANCH = "platformio_dependabot/ArduinoJson/7.4.3"


@pytest.mark.parametrize("shallow", [False, True])
def test_branch_is_based_on_base_branch_not_on_checkout(tmp_path, remote, shallow):
    work = clone(tmp_path, remote, "main", shallow)
    git(work, "checkout", "-qb", "feature")
    (work / "feature.txt").write_text("unrelated")
    git(work, "add", ".")
    git(work, "commit", "-qm", "feature work")

    failed, github_repo = run(work, "develop", [ARDUINOJSON])

    assert failed == []
    github_repo.create_pull.assert_called_once()
    assert github_repo.create_pull.call_args.kwargs["base"] == "develop"
    assert github_repo.create_pull.call_args.kwargs["head"] == BRANCH
    # the update branch contains exactly develop + the bump commit
    assert git(remote, "rev-parse", f"{BRANCH}^") == git(remote, "rev-parse", "develop")
    assert "^7.4.3" in git(remote, "show", f"{BRANCH}:platformio.ini")
    assert "feature.txt" not in git(remote, "ls-tree", "--name-only", BRANCH)


def test_failure_continues_and_leaves_clean_tree(tmp_path, remote):
    work = clone(tmp_path, remote, "main")
    other = PackageDefinition("Other", "1.0.0", "2.0.0", "^1.0.0")
    (work / "platformio.ini").write_text(INI + "    Other @ ^1.0.0\n")
    git(work, "commit", "-qam", "add other")
    git(work, "push", "-q", "origin", "main")

    with mock.patch.object(app, "create_pull_request", side_effect=[RuntimeError("403"), None]):
        failed, _ = run(work, "main", [ARDUINOJSON, other])

    assert failed == ["ArduinoJson"]
    assert git(work, "status", "--porcelain") == ""
    assert "^2.0.0" in git(remote, "show", "platformio_dependabot/Other/2.0.0:platformio.ini")


def _pr(number, ref, full_name="o/r"):
    pr = mock.MagicMock(number=number)
    pr.head.ref = ref
    pr.head.repo.full_name = full_name
    return pr


def test_close_outdated_pull_requests():
    github_repo = mock.MagicMock(full_name="o/r")
    old = _pr(1, "platformio_dependabot/ArduinoJson/7.0.0")
    current = _pr(2, BRANCH)
    up_to_date = _pr(3, "platformio_dependabot/Gone/1.0.0")
    failed_pkg = _pr(4, "platformio_dependabot/Broken/1.0.0")
    fork = _pr(5, "platformio_dependabot/Gone/0.9.0", full_name="someone/fork")
    manual = _pr(6, "feature/x")
    github_repo.get_pulls.return_value = [old, current, up_to_date, failed_pkg, fork, manual]
    broken = PackageDefinition("Broken", "1.0.0", "2.0.0", "^1.0.0")

    failed = app.close_outdated_pull_requests(github_repo, "main", [ARDUINOJSON, broken], {}, {"Broken"})

    assert failed == []
    old.create_issue_comment.assert_called_once_with("Superseded by #2.")
    old.edit.assert_called_once_with(state="closed")
    up_to_date.edit.assert_called_once_with(state="closed")
    assert "up to date" in up_to_date.create_issue_comment.call_args.args[0]
    for pr in (current, failed_pkg, fork, manual):
        pr.edit.assert_not_called()
    deleted = [c.args[0] for c in github_repo.get_git_ref.call_args_list]
    assert deleted == ["heads/platformio_dependabot/ArduinoJson/7.0.0", "heads/platformio_dependabot/Gone/1.0.0"]


def test_keep_old_pull_request_if_newer_one_was_closed_by_hand():
    github_repo = mock.MagicMock(full_name="o/r")
    old = _pr(1, "platformio_dependabot/ArduinoJson/7.0.0")
    github_repo.get_pulls.return_value = [old]

    assert app.close_outdated_pull_requests(github_repo, "main", [ARDUINOJSON], {}, set()) == []
    old.edit.assert_not_called()


def test_new_pull_request_supersedes_old_one_in_same_run(tmp_path, remote):
    work = clone(tmp_path, remote, "main")
    config = Configuration(str(work), str(work / "platformio.ini"), "o/r", "token", None, "main")
    github_repo = mock.MagicMock(full_name="o/r")
    github_repo.get_branch.side_effect = UnknownObjectException(404, {}, {})
    old = _pr(1, "platformio_dependabot/ArduinoJson/7.0.0")
    github_repo.get_pulls.return_value = [old]  # API does not list the new PR yet
    github_repo.create_pull.return_value = mock.MagicMock(number=7)
    with mock.patch.object(app, "install_libraries"), \
            mock.patch.object(app, "get_outdated_libraries", return_value=[ARDUINOJSON]):
        assert app.update_packages(config, github_repo, Repo(work), "main") == []
    old.create_issue_comment.assert_called_once_with("Superseded by #7.")
