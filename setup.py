# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='aptstore-core',
    version='0.1.0',
    description='Package to perform installing/removing software from different sources',
    long_description=readme,
    author='André Gregor-Herrmann',
    author_email='andre.gregor.herrmann@mailbox.org',
    url='https://github.com/liberavia/aptstore-core',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
