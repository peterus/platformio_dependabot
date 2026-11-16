
from pathlib import Path
from dataclasses import dataclass
from typing import List
import re

from platformio import fs
from platformio.package.commands.outdated import fetch_outdated_candidates
from platformio.package.commands.install import install_project_dependencies


def install_libraries(project_dir):
    options = {}
    options["environments"] = []
    options["project_dir"] = project_dir
    install_project_dependencies(options)


@dataclass(eq=True, frozen=True)
class PackageDefinition:
    name: str
    currentVersion: str
    latestVersion: str
    requirements: str


def get_outdated_libraries(project_path: Path) -> List[PackageDefinition]:
    with fs.cd(project_path):
        candidates = fetch_outdated_candidates([])

    packages: List[PackageDefinition] = []
    for candidate in candidates:
        packages.append(PackageDefinition(candidate.pkg.metadata.name,
                        candidate.outdated.wanted, candidate.outdated.latest, f"{candidate.spec.requirements}"))

    # remove duplicates, keep a stable order so PRs are created in the same order every run
    return sorted(set(packages), key=lambda p: (p.name.lower(), p.requirements, p.latestVersion))


def update_ini_file(iniFile: Path, package: PackageDefinition) -> bool:
    matches = re.search(r"^\s*([\^~<>=]*)\s*(.+?)\s*$", package.requirements)
    if not matches:
        return False
    operator = matches.group(1)
    requiredVersion = matches.group(2)

    eName = re.escape(package.name)
    eOperator = re.escape(operator)
    eRequiredVersion = re.escape(requiredVersion)

    # the name must not be the tail of another name (e.g. "MyArduinoJson" for "ArduinoJson"),
    # an owner prefix like "bblanchon/ArduinoJson" is fine
    pattern = rf"(?<![\w.\-]){eName}(\s*)@(\s*){eOperator}(\s*){eRequiredVersion}(?![\w.\-+])"

    with open(iniFile, "rt") as f:
        data = f.read()

    data, count = re.subn(
        pattern,
        lambda m: f"{package.name}{m.group(1)}@{m.group(2)}{operator}{m.group(3)}{package.latestVersion}",
        data)

    if count:
        with open(iniFile, "wt") as f:
            f.write(data)

    return count > 0
