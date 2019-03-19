from setuptools import setup, find_packages

from pathlib import Path


setup(
    name="updater",
    version=Path.cwd().joinpath("updater/VERSION").read_text(),
    long_description=Path.cwd().joinpath("README.md").read_text(),
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
    ],
    entry_points="""
        [console_scripts]
        updater=check_version:cli
    """,
    include_package_data=True,
)
