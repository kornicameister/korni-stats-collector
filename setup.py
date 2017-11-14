#!/usr/bin/env python
from distutils.core import setup
from setuptools import find_packages

setup(
    name='ksc',
    description='korni-stats-collector',
    packages=find_packages(exclude=['tests']),
    exclude_package_data={
        '': ['.git', '.gitignore', '.vscode']
    }
)
