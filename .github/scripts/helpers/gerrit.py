import json
import requests


class Gerrit:
    def __init__(self, env, auth=True):
        self.env = env
        self.auth = auth
        self.format = "o=DETAILED_ACCOUNTS&o=MESSAGES&o=LABELS&o=SKIP_DIFFSTAT"
        self.gerrit_url = "https://review.spdk.io"
        self.creds = ()
        if self.auth:
            self.creds = (self.env.gerrit_bot_user, self.env.gerrit_bot_http_passwd)
            self.gerrit_url += "/a/changes"
        else:
            self.gerrit_url += "/changes"

    def get_change(self):
        raw = requests.get(
            f"{self.gerrit_url}/{self.env.spdk_repo.replace("/", "%2F")}~{self.env.change_num}?{self.format}",
            auth=self.creds,
        )

        raw.raise_for_status()
        details = raw.text.splitlines()

        if len(details) != 2:
            return {}
        return json.loads(details[1])

    def post_comment(self, msg):
        post = requests.post(
            f"{self.gerrit_url}/{self.env.change_num}/revisions/{self.env.patch_set}/review",
            headers={"Content-Type": "application/json"},
            data=json.dumps(msg),
        )

        post.raise_for_status()
