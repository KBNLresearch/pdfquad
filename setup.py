#!/usr/bin/env python
"""Setup script for pdfbatchqa"""
import codecs
import os
import re
from setuptools import setup, find_packages

def read(*parts):
    """Read file and return contents"""
    path = os.path.join(os.path.dirname(__file__), *parts)
    with codecs.open(path, encoding='utf-8') as fobj:
        return fobj.read()

def find_version(*file_paths):
    """Find and return version number"""
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

INSTALL_REQUIRES = ['setuptools', 'lxml']
PYTHON_REQUIRES = '>=3.2, <4'

README = open('README.md', 'r')
README_TEXT = README.read()
README.close()

setup(name='pdfbatchqa',
      packages=find_packages(),
      version=find_version('pdfbatchqa', 'pdfbatchqa.py'),
      license='LGPL',
      install_requires=INSTALL_REQUIRES,
      python_requires=PYTHON_REQUIRES,
      platforms=['POSIX', 'Windows'],
      description='Automated PDF profiling for digitisation batches',
      long_description=README_TEXT,
      long_description_content_type='text/markdown',
      author='Johan van der Knijff',
      author_email='johan.vanderknijff@kb.nl',
      maintainer='Johan van der Knijff',
      maintainer_email='johan.vanderknijff@kb.nl',
      url='https://github.com/KBNLresearch/pdfbatchqa',
      download_url='https://github.com/KBNLresearch/pdfbatchqa/archive/' \
        + find_version('pdfbatchqa', 'pdfbatchqa.py') + '.tar.gz',
      package_data={'pdfbatchqa': ['*.*',
                                'profiles/*.*',
                                'schemas/*.*']},
      entry_points={'console_scripts': [
          'pdfbatchqa = pdfbatchqa.pdfbatchqa:main',
      ]},
      classifiers=[
          'Environment :: Console',
          'Programming Language :: Python :: 3',
      ]
     )
