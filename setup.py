import os
from setuptools import setup, find_packages

# Read the version from hsa_reimburse_package_radian21/__init__.py
def get_version():
    version = {}
    init_path = os.path.join("src", "hsa_reimburse_package_radian21", "__init__.py")
    with open(init_path, "r", encoding="utf-8") as f:
        exec(f.read(), version)
    return version["__version__"]

setup(
    name="hsa-reimburse",
    version=get_version(),
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "hsa=hsa_reimburse_package_radian21.hsa_reimburse:main",
        ],
    },
    install_requires=[],
    python_requires=">=3.8",
)