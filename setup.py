from setuptools import setup
from setuptools import find_packages


with open("README.md") as stream:
    long_description = stream.read()

setup(name='flowpipe',
      version='0.4.5',
      author='Paul Schweizer',
      author_email='paulschweizer@gmx.net',
      description='Lightweight flow-based programming framework.',
      long_description=long_description,
      url='https://github.com/PaulSchweizer/flowpipe',
      packages=find_packages(),
      classifiers=[
              'Programming Language :: Python',
              'Programming Language :: Python :: 2.6',
              'Programming Language :: Python :: 2.7',
              'Programming Language :: Python :: 3.3',
              'Programming Language :: Python :: 3.4',
              'Programming Language :: Python :: 3.5',
              'Programming Language :: Python :: 3.6'
        ])
