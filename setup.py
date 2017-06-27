# coding: utf-8
from __future__ import unicode_literals

import os
import codecs
from setuptools import setup, find_packages
from pip.req import parse_requirements
from pip.download import PipSession

rf = codecs.open(os.path.join(os.path.dirname(__file__), 'README.txt'), 'r')
with rf as readme:
    README = readme.read()

requirements = parse_requirements(
    os.path.join(os.path.dirname(__file__), 'requirements_as_lib.txt'),
    session=PipSession()
)

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='bernard',
    version='0.0.3',
    packages=find_packages('src'),
    package_dir={
        '': 'src',
    },
    scripts=[
        'bin/bernard'
    ],
    include_package_data=True,
    license='AGPLv3+',
    description='Bot Engine Responding Naturally At Requests Detection',
    long_description=README,
    url='https://github.com/BernardFW/bernard',
    author='Rémy Sanchez',
    author_email='remy.sanchez@hyperthese.net',
    install_requires=[str(x.req) for x in requirements],
    classifiers=[
        'License :: OSI Approved :: GNU Affero General Public License v3 or '
        'later (AGPLv3+)',
        'Development Status :: 3 - Alpha',
    ]
)
