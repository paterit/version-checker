import sys


if __name__ == "__main__":
    component = sys.argv[1]
    version = sys.argv[2]
    print("new version found in %r for version %r" % (component, version))
