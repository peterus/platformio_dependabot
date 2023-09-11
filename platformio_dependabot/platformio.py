
from pathlib import Path
from dataclasses import dataclass
from typing import List

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


def get_outdated_libraries(project_path: Path) -> List[PackageDefinition]:
    with fs.cd(project_dir):
        candidates = fetch_outdated_candidates([])

    packages: List[PackageDefinition] = []
    for candidate in candidates:
        packages.append(PackageDefinition(candidate.pkg.metadata.name,
                        candidate.outdated.wanted, candidate.outdated.latest))

    def remove_duplicates(duplicate_list: List[PackageDefinition]) -> List[PackageDefinition]:
        return list(set(duplicate_list))

    return remove_duplicates(packages)


def update_ini_file(iniFile: Path, package: PackageDefinition) -> None:
    data = ""
    with open(iniFile, "rt") as f:
        data = f.read()
        data = data.replace(f"{package.name} @ {package.currentVersion}",
                            f"{package.name} @ {package.latestVersion}")
    with open(iniFile, "wt") as f:
        f.write(data)
