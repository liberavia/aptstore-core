# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

data_files = []

for directory, _, filenames in os.walk(u'share'):
    dest = directory[6:]
    if filenames:
        files = []
        for filename in filenames:
            filename = os.path.join(directory, filename)
            files.append(filename)
        data_files.append((os.path.join('share', dest), files))

setup(
    name='aptstore_core',
    version='0.1.0',
    description='Package to perform installing/removing software from different sources/platforms',
    long_description=readme,
    author='André Gregor-Herrmann',
    author_email='andre.gregor.herrmann@mailbox.org',
    url='https://github.com/liberavia/aptstore-core',
    license=license,
    packages=find_packages(exclude=('tests', 'docs', 'config', 'share', 'bin')),
    scripts=['bin/aptstore-core'],
    data_files=data_files,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'requests',
        'pexpect',
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console'
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python',
        'Operating System :: Linux',
        'Topic :: System :: Installation/Setup'
    ],

)
