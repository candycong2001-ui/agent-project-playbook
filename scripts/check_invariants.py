#!/usr/bin/env python3
"""Check machine-verifiable release facts across code and documentation."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any


def read_text(root: Path, relative: str, errors: list[str]) -> str:
    path = root / relative
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        errors.append(f"cannot read {relative}: {error}")
        return ""


def load_contract(root: Path, errors: list[str]) -> dict[str, Any] | None:
    raw = read_text(root, "playbook_contract.json", errors)
    if not raw:
        return None
    try:
        contract = json.loads(raw)
    except json.JSONDecodeError as error:
        errors.append(f"invalid playbook_contract.json: {error}")
        return None
    if not isinstance(contract, dict):
        errors.append("playbook_contract.json must contain one JSON object")
        return None
    if contract.get("contract_schema_version") != 1:
        errors.append("unsupported contract_schema_version; expected 1")
        return None
    return contract


def load_initializer(root: Path, errors: list[str]) -> ModuleType | None:
    path = root / "scripts" / "init_project.py"
    spec = importlib.util.spec_from_file_location("checked_init_project", path)
    if spec is None or spec.loader is None:
        errors.append("could not load scripts/init_project.py")
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as error:  # noqa: BLE001 - report contract/import failures uniformly
        errors.append(f"could not import scripts/init_project.py: {error}")
        return None
    return module


def require_match(
    text: str,
    pattern: str,
    expected: str,
    label: str,
    errors: list[str],
) -> None:
    match = re.search(pattern, text, re.MULTILINE)
    if match is None:
        errors.append(f"missing invariant: {label}")
    elif match.group("value") != expected:
        errors.append(f"{label} is {match.group('value')!r}; expected {expected!r}")


def check_documents(root: Path, contract: dict[str, Any], errors: list[str]) -> None:
    version = str(contract["playbook_version"])
    readme = read_text(root, "README.md", errors)
    portability = read_text(root, "docs/PORTABILITY.zh-CN.md", errors)
    blueprint = read_text(root, "docs/EVOLUTION_BLUEPRINT.zh-CN.md", errors)

    require_match(
        readme,
        r"^当前版本：`v(?P<value>[^`]+)`$",
        version,
        "README version",
        errors,
    )
    require_match(
        portability,
        r"^## v(?P<value>\S+) 兼容性矩阵$",
        version,
        "PORTABILITY matrix version",
        errors,
    )
    require_match(
        blueprint,
        r"^当前 `v(?P<value>[^`]+)` ",
        version,
        "EVOLUTION_BLUEPRINT version",
        errors,
    )

    for phase, settings in contract["roadmap"]["phases"].items():
        pattern = rf"^\| Phase {re.escape(phase)}：[^\n]+\| {re.escape(settings['label_zh'])} \|$"
        if re.search(pattern, blueprint, re.MULTILINE) is None:
            errors.append(
                f"EVOLUTION_BLUEPRINT Phase {phase} status is not {settings['label_zh']!r}"
            )


def check_distribution(
    root: Path,
    contract: dict[str, Any],
    initializer: ModuleType,
    errors: list[str],
) -> None:
    version = str(contract["playbook_version"])
    schema_version = int(contract["installed_schema_version"])
    if initializer.PLAYBOOK_VERSION != version:
        errors.append(
            f"initializer version is {initializer.PLAYBOOK_VERSION!r}; expected {version!r}"
        )
    if initializer.INSTALLED_SCHEMA_VERSION != schema_version:
        errors.append("initializer installed schema version differs from the contract")

    for profile, settings in contract["profiles"].items():
        expected = tuple(Path(item) for item in settings["destinations"])
        try:
            actual = initializer.profile_destinations(profile)
        except (KeyError, ValueError) as error:
            errors.append(f"initializer rejects contract profile {profile!r}: {error}")
            continue
        if actual != expected:
            errors.append(f"initializer destinations differ for profile {profile!r}")
        for locale in contract["supported_locales"]:
            try:
                files = initializer.template_files(locale, profile)
            except (KeyError, ValueError) as error:
                errors.append(f"template mapping failed for {locale}/{profile}: {error}")
                continue
            if tuple(files) != expected:
                errors.append(f"template destinations differ for {locale}/{profile}")
            for template in files.values():
                if not template.is_file():
                    errors.append(f"missing template for {locale}/{profile}: {template}")

    for name, settings in contract["capabilities"].items():
        destination = settings.get("destination")
        if destination is None:
            continue
        declared_profiles = set(settings.get("profiles", []))
        actual_profiles = {
            profile
            for profile, profile_settings in contract["profiles"].items()
            if destination in profile_settings.get("destinations", [])
        }
        if actual_profiles != declared_profiles:
            errors.append(
                f"capability {name!r} profile membership differs: "
                f"declared={sorted(declared_profiles)}, actual={sorted(actual_profiles)}"
            )
        for locale in contract["supported_locales"]:
            for profile in declared_profiles:
                template = initializer.template_files(locale, profile).get(Path(destination))
                if template is None or not template.is_file():
                    continue
                if f"name: {name}" not in template.read_text(encoding="utf-8"):
                    errors.append(f"capability {name!r} template identity differs for {locale}")

    projectmem = contract["capabilities"]["projectmem"]
    if projectmem["activation"] != contract["defaults"]["projectmem"]:
        errors.append("projectmem capability activation differs from its default")
    if contract["defaults"]["projectmem"] != "opt-in":
        errors.append("unsupported projectmem default; expected 'opt-in'")

    try:
        rendered = initializer.render(
            root / "templates" / "agent-playbook.toml",
            "invariant-check",
            str(contract["defaults"]["locale"]),
            str(contract["defaults"]["profile"]),
        )
    except (OSError, UnicodeError, KeyError, TypeError, ValueError) as error:
        errors.append(f"could not render installed metadata: {error}")
        return
    if f"schema_version = {schema_version}" not in rendered:
        errors.append("rendered metadata schema_version differs from the contract")
    if f'playbook_version = "{version}"' not in rendered:
        errors.append("rendered metadata playbook_version differs from the contract")
    if 'projectmem = "disabled"' not in rendered:
        errors.append("fresh installed metadata must record projectmem as disabled")

    upgrade = contract["upgrade"]
    distributed = {
        relative
        for settings in contract["profiles"].values()
        for relative in settings["destinations"]
    }
    owned = {upgrade["metadata"], *upgrade["managed"], *upgrade["seeded"]}
    if distributed != owned:
        errors.append("upgrade ownership does not partition every distributed destination")

    supported_from = upgrade.get("supported_from")
    if not isinstance(supported_from, list) or not supported_from:
        errors.append("upgrade supported_from must list at least one older version")
    elif any(not isinstance(item, str) or not item for item in supported_from):
        errors.append("upgrade supported_from must contain version strings")
    elif version in supported_from:
        errors.append("current playbook_version must not be listed in upgrade supported_from")


def check_cli_defaults(root: Path, contract: dict[str, Any], errors: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        project = Path(temporary) / "meminit-project"
        direct_project = Path(temporary) / "direct-project"
        project.mkdir()
        direct_project.mkdir()
        environment = os.environ.copy()
        environment["PJM_BIN"] = str(Path(temporary) / "missing-pjm")
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            [str(root / "bin" / "meminit"), str(project), "invariant-check"],
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        direct_result = subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "init_project.py"),
                str(direct_project),
            ],
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if result.returncode != 0:
        errors.append(f"default meminit dry-run failed with exit {result.returncode}")
        return
    defaults = contract["defaults"]
    for expected in (
        f"- locale: `{defaults['locale']}`",
        f"- profile: `{defaults['profile']}`",
    ):
        if expected not in result.stdout:
            errors.append(f"meminit default differs from contract: {expected}")
    if "Projectmem plan" in result.stdout or "pjm is not executable" in result.stdout:
        errors.append("meminit invokes projectmem by default, but projectmem must be opt-in")
    if direct_result.returncode != 0:
        errors.append(f"default init_project dry-run failed with exit {direct_result.returncode}")
    else:
        for expected in (
            f"- locale: `{defaults['locale']}`",
            f"- profile: `{defaults['profile']}`",
        ):
            if expected not in direct_result.stdout:
                errors.append(f"init_project default differs from contract: {expected}")


def check_invariants(root: Path) -> list[str]:
    errors: list[str] = []
    contract = load_contract(root, errors)
    if contract is None:
        return errors
    try:
        required = (
            "playbook_version",
            "installed_schema_version",
            "supported_locales",
            "defaults",
            "profiles",
            "capabilities",
            "roadmap",
            "upgrade",
        )
        missing = [key for key in required if key not in contract]
        if missing:
            errors.append(f"contract is missing required keys: {', '.join(missing)}")
            return errors
        check_documents(root, contract, errors)
        initializer = load_initializer(root, errors)
        if initializer is not None:
            check_distribution(root, contract, initializer, errors)
        check_cli_defaults(root, contract, errors)
    except (KeyError, TypeError, ValueError) as error:
        errors.append(f"invalid playbook contract structure: {error}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Playbook repository root; defaults to this checkout.",
    )
    args = parser.parse_args(argv)
    root = Path(args.repo_root).expanduser().resolve()
    errors = check_invariants(root)
    print(f"Invariant Check: {len(errors)} error(s)")
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
