import pytest

from platformio_dependabot.platformio import PackageDefinition, update_ini_file


def _run(tmp_path, content, package):
    ini = tmp_path / "platformio.ini"
    ini.write_text(content)
    updated = update_ini_file(ini, package)
    return updated, ini.read_text()


def _pkg(name, requirements, latest):
    return PackageDefinition(name, "0.0.0", latest, requirements)


@pytest.mark.parametrize("line, expected", [
    ("lib_deps = bblanchon/ArduinoJson @ ^6.21.3", "lib_deps = bblanchon/ArduinoJson @ ^7.0.0"),
    ("lib_deps = ArduinoJson@^6.21.3", "lib_deps = ArduinoJson@^7.0.0"),
    ("lib_deps = ArduinoJson @ ~ 6.21.3", "lib_deps = ArduinoJson @ ~ 7.0.0"),
    ("lib_deps =\n    ArduinoJson @ 6.21.3\n", "lib_deps =\n    ArduinoJson @ 7.0.0\n"),
])
def test_updates_version(tmp_path, line, expected):
    requirements = line.split("@", 1)[1].strip()
    updated, data = _run(tmp_path, line, _pkg("ArduinoJson", requirements, "7.0.0"))
    assert updated
    assert data == expected


def test_does_not_touch_other_package_with_same_suffix(tmp_path):
    content = "lib_deps =\n    MyArduinoJson @ ^6.21.3\n    ArduinoJson @ ^6.21.3\n"
    updated, data = _run(tmp_path, content, _pkg("ArduinoJson", "^6.21.3", "7.0.0"))
    assert updated
    assert data == "lib_deps =\n    MyArduinoJson @ ^6.21.3\n    ArduinoJson @ ^7.0.0\n"


def test_does_not_match_longer_version(tmp_path):
    content = "lib_deps = ArduinoJson @ ^6.21.30\n"
    updated, data = _run(tmp_path, content, _pkg("ArduinoJson", "^6.21.3", "7.0.0"))
    assert not updated
    assert data == content


def test_updates_all_environments(tmp_path):
    content = "[env:a]\nlib_deps = ArduinoJson @ ^6.21.3\n[env:b]\nlib_deps = ArduinoJson @ ^6.21.3\n"
    updated, data = _run(tmp_path, content, _pkg("ArduinoJson", "^6.21.3", "7.0.0"))
    assert updated
    assert data.count("ArduinoJson @ ^7.0.0") == 2


def test_platform(tmp_path):
    content = "platform = espressif32 @ 6.5.0\n"
    updated, data = _run(tmp_path, content, _pkg("espressif32", "6.5.0", "6.9.0"))
    assert updated
    assert data == "platform = espressif32 @ 6.9.0\n"


def test_no_match_leaves_file_untouched(tmp_path):
    content = "lib_deps = ArduinoJson\n"
    updated, data = _run(tmp_path, content, _pkg("ArduinoJson", "None", "7.0.0"))
    assert not updated
    assert data == content


def test_empty_requirements(tmp_path):
    updated, _ = _run(tmp_path, "lib_deps = ArduinoJson\n", _pkg("ArduinoJson", "", "7.0.0"))
    assert not updated
