"""Keep unresolved legacy Python/license declarations pending maintainer guidance.

All other packaging configuration lives in pyproject.toml. See
docs/packaging.md before changing these remaining declarations.
"""

from setuptools import setup


CLASSIFIERS = [
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Scientific/Engineering :: Information Analysis",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Development Status :: 4 - Beta",
]

setup(
    license="GPL",
    classifiers=CLASSIFIERS,
    python_requires=">=3.6",
)
