#!/usr/bin/env python3
import re

from setuptools import setup, find_packages

with open('jprm/__init__.py', 'r') as fh:
    version = re.search(r'__version__ *= *["\'](.*?)["\']', fh.read()).group(1)

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    requirements = []
    for line in fh.readlines():
        line = line.strip()
        if line:
            requirements.append(line)

setup(
    name='jprm',
    version=version,
    author='Odd Stråbø',
    author_email='oddstr13@openshell.no',
    description='Jellyfin Plugin Repository Manager',
    keywords='Jellyfin plugin repository compile publish developement',
    url='https://github.com/oddstr13/jellyfin-plugin-repository-manager',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'jprm=jprm.__main__:cli',
        ]
    },
    zip_safe=True,
    classifiers=[
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Software Distribution',
    ],
    python_requires='>=3.6',
)
