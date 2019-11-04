# coding: utf-8

from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='shisetsu-scraper',
    version='0.0.1',
    description='spraping tools',
    long_description=readme,
    author='TRFV',
    author_email='trfv@hoge.com',
    url='https://github.com/trfv/shisetsu-scraper',
    license=license,
    packages=find_packages(exclude=('tests'))
)

