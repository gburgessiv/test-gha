#!/usr/bin/env python3

"""
This script, during normal operation, is careful to not leak information.

GHA logs are public, so we don't want to log sensitive information, which
includes things like "what are current issue titles," "how many issues are
there," "was an issue responded to," etc.

So:
1. Only log errors by default
2. Rather than `raise`ing in likely-to-intermittently-fail cases, log a warning
   and return an innocuous value.
3. Pad all runs to take a minute, since GH's API often responds very
   quickly. This should mask common cases of "an issue was reported."
"""

import argparse
import dataclasses
import logging
import os
import time
from typing import List, Optional, Set
import requests

import rotations

GhsaId = str


@dataclasses.dataclass(frozen=True)
class SecurityAdvisory:
    id: GhsaId
    collaborators: List[str]


def list_unpublished_security_advisories(
    repo_name: str, github_token: str
) -> List[SecurityAdvisory]:
    # Uses the API here:
    # https://docs.github.com/en/rest/security-advisories/repository-advisories?apiVersion=2022-11-28#update-a-repository-security-advisory
    resp = requests.get(
        f"https://api.github.com/repos/{repo_name}/security-advisories",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}",
            "GitHub-Api-Version": "2022-11-28",
        },
    )

    if not resp.ok:
        # Pretend these was nothing if there was an error, logging as `warning`
        # so it can be debugged with `--debug`.
        logging.warning(
            "Failed to list security advisories for %s: %d %s",
            repo_name,
            resp.status_code,
            resp.text,
        )
        return []

    advisories_json = resp.json()
    results = []
    for advisory in advisories_json:
        state = advisory["state"]
        if state not in ("draft", "triage"):
            continue
        collaborators = [x["login"] for x in advisory.get("collaborating_users", ())]
        results.append(
            SecurityAdvisory(
                id=advisory["ghsa_id"],
                collaborators=collaborators,
            )
        )

    logging.info("%d draft security advisories found.", len(results))
    return results


@dataclasses.dataclass(frozen=True)
class RotationState:
    all_members: Set[str]
    current_members: Set[str]


def load_rotation_state(now_timestamp: float) -> Optional[RotationState]:
    rotation_members_file = rotations.RotationMembersFile.parse_file(
        rotations.ROTATION_MEMBERS_FILE,
    )
    rotation_file = rotations.RotationFile.parse_file(
        rotations.ROTATION_FILE,
    )

    current_rotation = None
    # Pick the most recent rotation with a timstamp <= now
    for rotation in rotation_file.rotations:
        if rotation.start_time.timestamp() > now_timestamp:
            break
        current_rotation = rotation

    if not current_rotation:
        return None

    return RotationState(
        all_members=set(rotation_members_file.members),
        current_members=set(current_rotation.members),
    )


def add_collaborators_to_advisory_or_log(
    repo_name: str,
    github_token: str,
    advisory_id: GhsaId,
    collaborators: List[str],
):
    # Uses the API here
    # https://docs.github.com/en/rest/security-advisories/repository-advisories?apiVersion=2022-11-28#update-a-repository-security-advisory
    resp = requests.patch(
        f"https://api.github.com/repos/{repo_name}/security-advisories/{advisory_id}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}",
            "GitHub-Api-Version": "2022-11-28",
        },
        json={
            "collaborating_users": collaborators,
        },
    )

    if resp.ok:
        return

    # Warn here, since this script only logs errors by default on GHA, and this may contain
    # some sensitive information.
    logging.warning(
        "Failed to add collaborators %s to advisory %s: %d %s",
        collaborators,
        advisory_id,
        resp.status_code,
        resp.text,
    )


def run_script(
    repo_name: str,
    github_token: str,
    now_timestamp: float,
    dry_run: bool,
):
    rotation_state = load_rotation_state(now_timestamp)
    if not rotation_state:
        logging.info("No current rotation found; nothing to do.")
        return

    draft_security_advisories = list_unpublished_security_advisories(
        repo_name, github_token
    )
    for advisory in draft_security_advisories:
        has_rotation_member = any(
            member in rotation_state.current_members
            for member in advisory.collaborators
        )

        if has_rotation_member:
            logging.info(
                "Skipping advisory %s: already has rotation member(s) as collaborator.",
                advisory.id,
            )
            continue

        collaborators_to_add = sorted(rotation_state.current_members)
        if dry_run:
            logging.info(
                "Would add collaborators %s to advisory %s, if not for --dry-run.",
                collaborators_to_add,
                advisory.id,
            )
            continue

        add_collaborators_to_advisory_or_log(
            repo_name=repo_name,
            github_token=github_token,
            advisory_id=advisory.id,
            collaborators=collaborators_to_add,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Respond to new issues in a GitHub repository."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually modify issues.",
    )
    return parser.parse_args()


def main():
    opts = parse_args()

    repo_name = os.getenv("GITHUB_REPOSITORY")
    assert repo_name, "GITHUB_REPOSITORY environment variable must be set."
    github_token = os.getenv("GITHUB_TOKEN")
    assert github_token, "GITHUB_TOKEN environment variable must be set."

    script_start_time = time.time()
    script_min_end_time = script_start_time + 60
    logging.basicConfig(
        format=">> %(asctime)s: %(levelname)s: %(filename)s:%(lineno)d: %(message)s",
        level=logging.DEBUG if opts.debug else logging.INFO,
    )

    run_script(
        repo_name=repo_name,
        github_token=github_token,
        now_timestamp=script_start_time,
        dry_run=opts.dry_run,
    )

    now = time.time()
    if now < script_min_end_time:
        logging.info("Ensuring the script runs for at least 60 seconds.")
        time.sleep(script_min_end_time - now)


if __name__ == "__main__":
    main()
