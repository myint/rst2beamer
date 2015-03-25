#!/usr/bin/env python

"""Installer for rst2beamer."""

import ast

from setuptools import setup


def version():
    """Return version string."""
    with open('rst2beamer.py') as input_file:
        for line in input_file:
            if line.startswith('__version__'):
                return ast.parse(line).body[0].value.s

with open('README.rst') as readme:
    with open('HISTORY.rst') as history:
        DESCRIPTION = readme.read() + '\n' + history.read()


setup(
    name='rst2beamer3k',
    version=version(),
    description='A docutils writer and script for converting restructured '
                'text to the Beamer presentation format',
    long_description=DESCRIPTION,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Text Processing :: Markup',
        'Topic :: Utilities',
        'Topic :: Multimedia :: Graphics :: Presentation',
    ],
    keywords='presentation docutils rst restructured-text',
    url='https://github.com/myint/rst2beamer',
    license='GPL',
    py_modules=['rst2beamer'],
    zip_safe=False,
    install_requires=[
        'docutils >= 0.11',
    ],
    entry_points={
        'console_scripts': [
            'rst2beamer = rst2beamer:main',
        ]
    }
)
