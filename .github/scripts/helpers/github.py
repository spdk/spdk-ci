import re
import requests
import json


class GitHub:
    def __init__(self, env, auth=True):
        self.env = env
        self.auth = auth
        self.gh_url = f"https://api.github.com/repos/{self.env.gh_repo}"
        self.gh_auth_headers = {}
        if self.auth:
            self.gh_auth_headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.env.gh_issue_pat}",
            }

    def get_issue_from_gerrit_comment(self):
        pattern = re.compile(
            r"patch set [0-9]+:\n\nfalse positive:\s*[#]?([0-9]+)$",
            re.IGNORECASE,
        )

        gh_issue = int(re.search(pattern, self.env.gerrit_comment).groups()[0])
        gh_issue_j = requests.get(
            f"{self.gh_url}/issues/{gh_issue}", headers=self.gh_auth_headers
        ).json()

        return gh_issue, gh_issue_j

    def post_comment(self, gh_issue, msg):
        post = requests.post(
            f"{self.gh_url}/issues/{gh_issue}/comments",
            headers=self.gh_auth_headers,
            json=json.dumps(msg),
        )

        post.raise_for_status()

    def post_rerun(self, run_id):
        post = requests.post(
            f"{self.gh_url}/actions/runs/{run_id}/run",
            headers=self.gh_auth_headers,
        )

        post.raise_for_status()
