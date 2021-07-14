#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

requires = [
    'tornado',
    'tornado-sqlalchemy',
    #'psycopg2',
]

setup(
    name='tornado_time_clock',
    version='0.0',
    description='Placeholder',
    author='FelixTheC',
    author_email='',
    keywords='web tornado',
    packages=find_packages(),
    install_requires=requires,
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    entry_points={
        'console_scripts': [
            'serve_app = src:runserver',
        ],
    },
)
