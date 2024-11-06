#!/usr/bin/env python
"""Setup script for pdfquad"""
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

INSTALL_REQUIRES = ['setuptools',
                    'lxml', 
                    'pillow>=9.0.0',
                    'pymupdf>=1.24.3']
PYTHON_REQUIRES = '>=3.8, <4'

README = open('README.md', 'r')
README_TEXT = README.read()
README.close()

setup(name='pdfquad',
      packages=find_packages(),
      version=find_version('pdfquad', 'pdfquad.py'),
      license='Apache License (https://www.apache.org/licenses/LICENSE-2.0)',
      install_requires=INSTALL_REQUIRES,
      python_requires=PYTHON_REQUIRES,
      platforms=['POSIX', 'Windows'],
      description='PDF QUality Assessment for Digitisation batches',
      long_description=README_TEXT,
      long_description_content_type='text/markdown',
      author='Johan van der Knijff',
      author_email='johan.vanderknijff@kb.nl',
      maintainer='Johan van der Knijff',
      maintainer_email='johan.vanderknijff@kb.nl',
      url='https://github.com/KBNLresearch/pdfquad',
      download_url='https://github.com/KBNLresearch/pdfquad/archive/' \
        + find_version('pdfquad', 'pdfquad.py') + '.tar.gz',
      package_data={'pdfquad': ['*.*',
                                'profiles/*.*',
                                'schemas/*.*']},
      entry_points={'console_scripts': [
          'pdfquad = pdfquad.pdfquad:main',
      ]},
      classifiers=[
          'Environment :: Console',
          'Programming Language :: Python :: 3',
      ]
     )
