#!/usr/bin/env python3

import re
import sys

from helpers import Env, Gerrit, GitHub


def is_wip(change):
    return change.get("work_in_progress")


def is_current_revision(change, patch_set):
    return change.get("current_revision_number") == patch_set


def is_negative_from_user(change, user):
    user_ver = next(
        (ver for ver in change["labels"]["Verified"]["all"] if ver["username"] == user),
        {},
    )

    return user_ver and user_ver.get("value", 0) == -1


def is_issue_state(issue, state="open"):
    set_state = issue.get("state").lower()
    return set_state == state.lower()


def get_failed_builds_for_patch_by_user(change, user, patch_set):
    # Group comments into respective patchsets, pick the latest "Build failed" comment from
    # the latest patchset it was recorded at and check if that patchset is older or the
    # same as patch_set.

    pattern = "Build failed. Results: "
    comments_per_patchset = {}

    for msg in change["messages"]:
        if msg["author"]["username"] != user:
            continue
        if msg["_revision_number"] not in comments_per_patchset:
            comments_per_patchset[msg["_revision_number"]] = []
        comments_per_patchset[msg["_revision_number"]].append(msg["message"])

    latest_build_failed_patchset = -1
    for p in sorted(comments_per_patchset.keys()):
        if pattern in "\n".join(comments_per_patchset[p]):
            latest_build_failed_patchset = p

    if latest_build_failed_patchset == -1 or latest_build_failed_patchset > patch_set:
        return []

    failed_builds = []
    for comment in comments_per_patchset[latest_build_failed_patchset]:
        for line in comment.splitlines():
            if pattern in line:
                failed_builds.append(line)

    return failed_builds


def get_url_details_from_failed_build(build):
    run_url_pattern = re.compile(r"\((https://.+)\)")
    run_id_pattern = re.compile(r"\[([0-9]+)/[0-9]+\]")

    return (
        re.search(run_url_pattern, build).groups()[0],
        re.search(run_id_pattern, build).groups()[0],
    )


def main():
    env = Env()
    gerrit = Gerrit(env, auth=True)
    github = GitHub(env, auth=True)

    change_details = gerrit.get_change()
    change_gh_details = github.get_issue_from_gerrit_comment()

    (gh_issue, gh_issue_j) = change_gh_details

    if not change_details:
        print(f"Change {env.change_num} does not exist? Verify the environment.")
        sys.exit(0)

    if not gh_issue:
        print(
            "Ignore. Comment does not include valid false positive phrase, no issue number found."
        )
        sys.exit(0)

    if is_wip(change_details):
        print("Ignore. Comment posted to WIP change.")
        sys.exit(0)

    if not is_current_revision(change_details, env.patch_set):
        print("Ignore. Comment posted to different patch set.")
        sys.exit(0)

    if not is_negative_from_user(change_details, env.gerrit_bot_user):
        print("Ignore. Comment posted with no negative vote from CI")
        sys.exit(0)

    if not is_issue_state(gh_issue_j, "open"):
        print("Comment points to incorrect GitHub issue.")
        gerrit.post_to_gerrit(
            {"message": f"Issue #{gh_issue} does not exist or is already closed."}
        )
        sys.exit(0)

    failed_builds = get_failed_builds_for_patch_by_user(
        change_details, env.gerrit_bot_user, env.patch_set
    )

    if not failed_builds:
        print("Did not find comments indicating build failure")
        sys.exit(1)

    (fp_run_url, fp_run_id) = get_url_details_from_failed_build(failed_builds[-1])

    github.post_comment(
        gh_issue,
        {
            "body": f"Another instance of this failure. Reported by @{env.reported_by}. Log: {fp_run_url}"
        },
    )

    github.post_rerun(fp_run_id)
    gerrit.post_comment({"message": "Retriggered", "labels": {"Verified": 0}})


if __name__ == "__main__":
    main()
