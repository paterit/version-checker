import sys
from loguru import logger
from packaging.version import parse
import requests
from cachier import cachier
import datetime


EXIT_CODE_ERROR = 1


@cachier(stale_after=datetime.timedelta(days=3))
def fetch_versions(repo_name, component):
    logger.info(repo_name + ":" + component + " - NOT CACHED")
    payload = {
        'service': 'registry.docker.io',
        'scope': 'repository:{repo}/{image}:pull'.format(repo=repo_name, image=component)
    }

    r = requests.get('https://auth.docker.io/token', params=payload)
    if not r.status_code == 200:
        print("Error status {}".format(r.status_code))
        raise Exception("Could not get auth token")

    j = r.json()
    token = j['token']
    h = {'Authorization': "Bearer {}".format(token)}
    r = requests.get('https://index.docker.io/v2/{}/{}/tags/list'.format(repo_name, component),
                     headers=h)
    return r.json().get("tags", [])


if __name__ == "__main__":
    if len(sys.argv) < 4:
        logger.error("To less params")
        sys.exit(EXIT_CODE_ERROR)

    component = sys.argv[1]
    repo_name = sys.argv[2]
    version = sys.argv[3]

    tags = fetch_versions(repo_name, component)
    highest = max([parse(tag) for tag in tags])
    current = parse(version)

    if highest > current:
        print("For %r new version found : %r" % (component, highest))
    else:
        print("For %r no newer version found in %r" % (component, tags))
