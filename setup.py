#!/usr/bin/env python

from distutils.core import setup

setup(
  name = 'amznas',
  version='0.1.0',
  py_modules = ['amznas', 'eggdisp'],
  scripts = ['amznas.py', 'eggdisp.py'],
  classifiers = [
    'Intended Audience :: Science/Research',
    'Topic :: Scientific/Engineering',
    'Topic :: Multimedia :: Sound/Audio :: Speech'
  ],
  requires = [
    'numpy',
    'pandas'
  ]

)
