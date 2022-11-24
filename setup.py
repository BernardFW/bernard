from __future__ import unicode_literals

import codecs
import os
from typing import Text

from setuptools import find_packages, setup


def parse_requirements(req_file_path: Text):
    with open(req_file_path, "r") as req_file:
        return req_file.readlines()


rf = codecs.open(os.path.join(os.path.dirname(__file__), "README.txt"), "r")
with rf as readme:
    README = readme.read()

requirements = parse_requirements(
    os.path.join(os.path.dirname(__file__), "requirements_as_lib.txt"),
)

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="bernard",
    version="0.2.0",
    packages=find_packages("src"),
    package_dir={
        "": "src",
    },
    scripts=["bin/bernard"],
    include_package_data=True,
    license="AGPLv3+",
    description="Bot Engine Responding Naturally At Requests Detection",
    long_description=README,
    url="https://github.com/BernardFW/bernard",
    author="Rémy Sanchez",
    author_email="remy.sanchez@hyperthese.net",
    install_requires=requirements,
    classifiers=[
        "License :: OSI Approved :: GNU Affero General Public License v3 or "
        "later (AGPLv3+)",
        "Development Status :: 4 - Beta",
    ],
)
