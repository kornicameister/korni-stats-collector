#!/usr/bin/env python
from distutils.core import setup
from setuptools import find_packages

setup(
    name='ksc',
    description='korni-stats-collector',
    packages=find_packages(exclude=['tests']),
    author='kornicameister@gmail.com',
    license='Apache 2.0',
    long_description=open('README.md').read(),
    exclude_package_data={'': ['.git', '.gitignore', '.vscode']}
)
