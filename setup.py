from pathlib import Path

from setuptools import find_packages, setup

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
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Build Tools",
        "Operating System :: POSIX :: Linux",
    ],
    py_modules=["check_version"],
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "loguru==0.5.3",
        "behave==1.2.6",
        "requests==2.26.0",
        "packaging==21.3",
        "plumbum==1.7.1",
        "cachier==1.5.3",
        "python-rex==0.4",
        "pymongo==3.12.1",
        "click==7.1",
        "PyYAML==5.4.1",
    ],
    entry_points="""
        [console_scripts]
        updater=check_version:cli
    """,
    include_package_data=True,
    python_requires=">=3.6.9",
)
