import os


class Env:
    def __init__(self):
        self.reported_by = os.getenv("AUTHOR")
        self.gerrit_comment = os.getenv("COMMENT")
        self.gerrit_bot_http_passwd = os.getenv("GERRIT_BOT_HTTP_PASSWD")
        self.gerrit_bot_user = os.getenv("GERRIT_BOT_USER")
        self.gh_issue_pat = os.getenv("GH_ISSUES_PAT")
        self.gh_repo = os.getenv("GH_REPO")
        self.spdk_repo = os.getenv("REPO")
        self.change_num = os.getenv("change_num")  # FIXME: to uppercase
        self.patch_set = os.getenv("patch_set")  # FIXME: to uppercase
        self.gh_auth = not os.getenv("GITHUB_DISABLE_AUTH")
        self.gerrit_auth = not os.getenv("GERRIT_DISABLE_AUTH")

        self._ignore = ["gh_auth", "gerrit_auth"]

        for var, val in self.__dict__.items():
            if var in self._ignore:
                continue
            if not val:
                raise AttributeError(
                    f"Not all env attributes were set: {self.__dict__.items()}"
                )

        self.change_num = int(self.change_num)
        self.patch_set = int(self.patch_set)
