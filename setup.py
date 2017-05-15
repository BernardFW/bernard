# coding: utf-8
from __future__ import unicode_literals

import os
import codecs
from distutils.core import setup
from pip.req import parse_requirements
from pip.download import PipSession

with codecs.open(os.path.join(os.path.dirname(__file__), 'README.txt'), 'r') as readme:
    README = readme.read()

requirements = parse_requirements(
    os.path.join(os.path.dirname(__file__), 'requirements.txt'),
    session=PipSession()
)

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='bernard',
    version='0.0.1',
    packages=[
    ],
    scripts=[
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
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Development Status :: 1 - Planning',
    ]
)
