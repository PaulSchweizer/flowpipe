"""The setup file only exists to be able to build the docs on readthedocs!"""
from setuptools import find_packages, setup

with open("README.md") as stream:
    long_description = stream.read()

REQUIREMENTS = [
    "ascii-canvas>=2.0.0",
]

setup(
    name="flowpipe",
    version="1.0.4",
    author="Paul Schweizer",
    author_email="paulschweizer@gmx.net",
    description="Lightweight flow-based programming framework.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PaulSchweizer/flowpipe",
    packages=find_packages(),
    install_requires=REQUIREMENTS,
    classifiers=[
        "Programming Language :: Python",
    ],
)
