
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

    def remove_duplicates(duplicate_list: List[PackageDefinition]) -> List[PackageDefinition]:
        return list(set(duplicate_list))

    return remove_duplicates(packages)


def update_ini_file(iniFile: Path, package: PackageDefinition) -> bool:
    updated = False
    data = ""

    matches = re.search(r"^\s*([\^~<>=]*)\s*(.+)\s*$", package.requirements)
    operator = matches.group(1)
    requiredVersion = matches.group(2)

    eName = re.escape(f"{package.name}")
    eOperator = re.escape(f"{operator}")
    eRequiredVersion = re.escape(f"{requiredVersion}")

    with open(iniFile, "rt") as f:
        data = f.read()
        matches = re.findall(rf"({eName}(\s*)@(\s*){eOperator}(\s*){eRequiredVersion})", data)

        for matched, space1, space2, space3 in matches:
            updated = True
            data = data.replace(matched, f"{package.name}{space1}@{space2}{operator}{space3}{package.latestVersion}")
    with open(iniFile, "wt") as f:
        f.write(data)

    return updated