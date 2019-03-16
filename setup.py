from setuptools import setup, find_packages

# read the contents of your README file
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="updater",
    version="0.1.7",
    long_description=long_description,
    description="Check and update versions of pypi packages and docker-images in your project.",
    long_description_content_type="text/markdown",
    url="https://github.com/paterit/version-checker",
    author="PaterIT",
    author_email="paterit@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Build Tools",
        "Operating System :: POSIX :: Linux",
    ],
    py_modules=["check_version"],
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "loguru==0.2.5",
        "behave==1.2.6",
        "requests==2.20.0",
        "packaging==18.0",
        "plumbum==1.6.7",
        "cachier==1.2.4",
        "python-rex==0.4",
        "pymongo==3.7.2",
        "click==7.0",
        "maya==0.6.1",
    ],
    entry_points="""
        [console_scripts]
        updater=check_version:cli
    """,
)
