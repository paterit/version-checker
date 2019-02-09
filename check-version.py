import sys
from loguru import logger
from packaging.version import parse


EXIT_CODE_ERROR = 1


def fetch_versions(component):
    return ["v1.1.1", "v2.1.1"]


if __name__ == "__main__":
    if len(sys.argv) < 3:
        logger.error("To less params")
        sys.exit(EXIT_CODE_ERROR)

    component = sys.argv[1]
    version = sys.argv[2]

    tags = fetch_versions(component)
    highest = max([parse(tag) for tag in tags])
    current = parse(version)

    if highest > current:
        print("For %r new version found : %r" % (component, highest))
    else:
        print("For %r no newer version found in %r" % (component, tags))
