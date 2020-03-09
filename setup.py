#!/usr/bin/env python

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='superimposer',
    version='0.1.0',
    description='Superimpose presentation records onto PDF slides',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/jonhoo/superimposer',
    author='Jon Gjengset',
    author_email='jon@thesquareplanet.com',
    classifiers=[  # Optional
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Multimedia :: Graphics :: Presentation',
        'Topic :: Multimedia :: Video',
        'Natural Language :: English',

        'License :: OSI Approved :: MIT License',

        'Environment :: Console',
        'Operating System :: POSIX',

        'Programming Language :: Python :: 3',
    ],

    keywords='presentation slides video ffmpeg',

    packages=['superimposer'],

    python_requires='>=3.5, <4',

    install_requires=['PyPDF2>=1.26.0,<2'],

    entry_points={
        'console_scripts': [
            'superimposer=superimposer.__main__:main',
        ],
    },

    project_urls={
        'Bug Reports': 'https://github.com/jonhoo/superimposer/issues',
        'Say Thanks!': 'https://twitter.com/jonhoo',
        'Source': 'https://github.com/jonhoo/superimposer',
    },
)
