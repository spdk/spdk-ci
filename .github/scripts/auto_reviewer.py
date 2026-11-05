#!/usr/bin/env python3
#
# Auto-Reviewer Assignment for SPDK Gerrit
#
# Scans open, CI-passed patches and randomly assigns a core maintainer.
# Runs hourly via GitHub Actions (gerrit-auto-reviewer.yml).
#
# Prerequisites (one-time Gerrit admin setup):
#
#   1. Add a custom label to the spdk/spdk project config (project.config):
#
#      [label "Auto-Reviewer"]
#        function = NoOp
#        defaultValue = 0
#        value = 0 Not assigned
#        value = 1 Jim Harris
#        value = 2 Jacek Kalwas
#        value = 3 Mateusz Kozlowski
#        value = 4 Changpeng Liu
#        value = 5 Alexey Marchuk
#        value = 6 Shuhei Matsumoto
#        value = 7 Konrad Sztyber
#        value = 8 Ben Walker
#        value = 9 Tomasz Zawadzki
#
#   2. Grant the CI bot account permission to vote on Auto-Reviewer:
#
#      [access "refs/*"]
#        label-Auto-Reviewer = -0..+9 group CI Bot
#

import os
import logging
import random
from pygerrit2 import GerritRestAPI, HTTPBasicAuth

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
GERRIT_USERNAME = os.getenv("GERRIT_USERNAME")
GERRIT_PASSWORD = os.getenv("GERRIT_PASSWORD")
GERRIT_BASE_URL = os.getenv("GERRIT_BASE_URL", "https://review.spdk.io")

# Core maintainers: (label_value, gerrit_display_name)
# Label values correspond to the custom "Auto-Reviewer" Gerrit label.
# Display names MUST match each maintainer's Gerrit profile name exactly.
MAINTAINERS = [
    (1, "Jim Harris"),
    (2, "Jacek Kalwas"),
    (3, "Mateusz Kozlowski"),
    (4, "Changpeng Liu"),
    (5, "Alexey Marchuk"),
    (6, "Shuhei Matsumoto"),
    (7, "Konrad Sztyber"),
    (8, "Ben Walker"),
    (9, "Tomasz Zawadzki"),
]

MAINTAINER_NAMES = {name for _, name in MAINTAINERS}


def get_unassigned_changes(gerrit):
    """Fetch open, CI-passed, non-WIP changes without an Auto-Reviewer assignment."""
    query = "".join([
        "/changes/",
        "?q=project:spdk/spdk status:open -is:wip label:Verified=+1",
        "&o=DETAILED_LABELS",
        "&o=DETAILED_ACCOUNTS",
    ])
    logging.info(f"Querying Gerrit: {query}")
    changes = gerrit.get(query)

    unassigned = []
    for change in changes:
        labels = change.get("labels", {})
        auto_reviewer = labels.get("Auto-Reviewer", {})
        all_votes = auto_reviewer.get("all", [])
        has_assignment = any(vote.get("value", 0) > 0 for vote in all_votes)

        if not has_assignment:
            unassigned.append(change)

    logging.info(f"Found {len(changes)} CI-passed changes, {len(unassigned)} unassigned")
    return unassigned


def pick_random_maintainer(owner_name):
    """Pick a random maintainer, excluding the patch owner."""
    candidates = [(value, name) for value, name in MAINTAINERS if name != owner_name]
    if not candidates:
        logging.warning(f"No eligible maintainers for owner '{owner_name}'")
        return None, None
    label_value, name = random.choice(candidates)
    return name, label_value


def assign_reviewer(gerrit, change, maintainer_name, label_value):
    """Assign a maintainer: set label, add as reviewer, post comment."""
    change_id = change["_number"]
    subject = change.get("subject", "N/A")
    owner = change.get("owner", {}).get("name", "Unknown")
    url = f"{GERRIT_BASE_URL}/c/spdk/spdk/+/{change_id}"

    logging.info(f"Assigning {maintainer_name} to change {change_id} "
                 f"'{subject}' by {owner} ({url})")

    # 1. Set Auto-Reviewer label and post comment
    message = f"Auto-assigned to {maintainer_name} for review."
    review_data = {
        "message": message,
        "labels": {"Auto-Reviewer": label_value},
    }
    try:
        gerrit.post(f"/changes/{change_id}/revisions/current/review", json=review_data)
        logging.info(f"Set Auto-Reviewer={label_value} and posted comment on change {change_id}")
    except Exception as e:
        logging.error(f"Failed to set label/comment on change {change_id}: {e}")
        return

    # 2. Add as reviewer
    try:
        gerrit.post(f"/changes/{change_id}/reviewers", json={"reviewer": maintainer_name})
        logging.info(f"Added {maintainer_name} as reviewer on change {change_id}")
    except Exception as e:
        logging.error(f"Failed to add reviewer {maintainer_name} to change {change_id}: {e}")


def main():
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    auth = HTTPBasicAuth(GERRIT_USERNAME, GERRIT_PASSWORD)
    gerrit = GerritRestAPI(url=GERRIT_BASE_URL, auth=auth)

    try:
        unassigned = get_unassigned_changes(gerrit)
        for change in unassigned:
            owner_name = change.get("owner", {}).get("name", "Unknown")
            maintainer_name, label_value = pick_random_maintainer(owner_name)
            if maintainer_name:
                assign_reviewer(gerrit, change, maintainer_name, label_value)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        exit(1)


if __name__ == "__main__":
    main()
