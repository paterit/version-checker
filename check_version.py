import sys
from loguru import logger
from packaging.version import parse
import requests
from cachier import cachier
import datetime


EXIT_CODE_ERROR = 1
EXIT_CODE_SUCCESS = 0


class ComponentChecker:
    def __init__(self, repo_name, component_name, current_version_tag):
        self.repo_name = repo_name
        self.component_name = component_name
        self.current_version_tag = current_version_tag
        self.current_version = parse(current_version_tag)
        self.version_tags = []
        self.highest_version = self.current_version
        super().__init__()

    def newer_version_exists(self):
        return self.highest_version > self.current_version

    def check(self):
        self.version_tags = fetch_versions(self.repo_name, self.component_name)
        self.highest_version = max([parse(tag) for tag in self.version_tags])

        return self.newer_version_exists()


@cachier(stale_after=datetime.timedelta(days=3))
def fetch_versions(repo_name, component):
    logger.info(repo_name + ":" + component + " - NOT CACHED")
    payload = {
        "service": "registry.docker.io",
        "scope": "repository:{repo}/{image}:pull".format(
            repo=repo_name, image=component
        ),
    }

    r = requests.get("https://auth.docker.io/token", params=payload)
    if not r.status_code == 200:
        print("Error status {}".format(r.status_code))
        raise Exception("Could not get auth token")

    j = r.json()
    token = j["token"]
    h = {"Authorization": "Bearer {}".format(token)}
    r = requests.get(
        "https://index.docker.io/v2/{}/{}/tags/list".format(repo_name, component),
        headers=h,
    )
    return r.json().get("tags", [])


if __name__ == "__main__":
    if len(sys.argv) < 4:
        logger.error("To less params")
        sys.exit(EXIT_CODE_ERROR)

    component = sys.argv[1]
    repo_name = sys.argv[2]
    version = sys.argv[3]

    checker = ComponentChecker(repo_name, component, version)

    if checker.check():
        sys.exit(EXIT_CODE_SUCCESS)
    else:
        sys.exit(EXIT_CODE_ERROR)
