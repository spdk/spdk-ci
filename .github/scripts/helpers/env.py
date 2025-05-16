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

        if not all(self.__dict__.values()):
            raise AttributeError(
                f"Not all env attributes were set: {self.__dict__.items()}"
            )

        self.change_num = int(self.change_num)
        self.patch_set = int(self.patch_set)
