#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import codecs
import unittest
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys


def read(name):
    return codecs.open(os.path.join(os.path.dirname(__file__), name)).read()


class MyTest(TestCommand):
    def run_tests(self):
        tests = unittest.TestLoader().discover('tests', pattern='test_*.py')
        unittest.TextTestRunner(verbosity=1).run(tests)


setup(
    name='peewee-rest-query',
    version='0.1.0',
    license='MIT',
    description='A rest query request args parser for peewee orm.',
    author='dracarysX',
    author_email='huiquanxiong@gmail.com',
    url='https://github.com/dracarysX/peewee-rest-query',
    packages=find_packages(include=['peewee_rest_query']),
    install_requires=[  
        "peewee",
        "rest_query"
    ], 
    test_suite='nose.collector',
    tests_require=['nose'],
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License',
    ],
    keywords='rest, query, no-sql, parser, peewee',
    long_description=read('README.rst')
)
