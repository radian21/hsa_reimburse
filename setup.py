import os
from setuptools import setup, find_packages

# Read the version from hsa_reimburse/__init__.py
def get_version():
    version = {}
    with open(os.path.join("src", "__init__.py")) as f:
        exec(f.read(), version)
    return version["__version__"]

setup(
    name="hsa-reimburse",
    version=get_version(),  # Use the version dynamically
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "hsa_reimburse=hsa_reimburse.cli:main",
        ],
    },
    install_requires=[],
    python_requires=">=3.6",
)