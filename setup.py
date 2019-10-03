from setuptools import setup
from setuptools import find_packages

import flowpipe


with open('README.md') as stream:
    long_description = stream.read()

REQUIREMENTS = [
    'ascii-canvas>=1.2.2',
    'ordereddict>=1.1',
    'strip-hints>=0.1.7'
]

setup(name='flowpipe',
      version=flowpipe.__version__,
      author='Paul Schweizer',
      author_email='paulschweizer@gmx.net',
      description='Lightweight flow-based programming framework.',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/PaulSchweizer/flowpipe',
      packages=find_packages(),
      install_requires=REQUIREMENTS,
      classifiers=[
              'Programming Language :: Python',
              'Programming Language :: Python :: 2.6',
              'Programming Language :: Python :: 2.7',
              'Programming Language :: Python :: 3.4',
              'Programming Language :: Python :: 3.5',
              'Programming Language :: Python :: 3.6',
              'Programming Language :: Python :: 3.7',
      ])
