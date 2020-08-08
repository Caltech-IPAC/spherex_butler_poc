from setuptools import setup, find_packages

version = "0.0.1"

with open("README.md", "r") as fh:
    long_description = fh.read()

# packages are organized according to PEP-420: https://www.python.org/dev/peps/pep-0420/
# see https://setuptools.readthedocs.io/en/latest/setuptools.html#find-namespace-packages
setup (
    name="spherex_butler_poc",
    provides="spherex_butler_poc",
    version=version,
    description="Proof-of-concept code for using LSST Gen3 Butler in SPHEREx pipelines",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Caltech-IPAC/spherex_butler_poc",
    packages=find_packages(where="python"),
    package_dir={"": "python"},
    python_requires=">3.6",
    setup_requires=["setuptools >=49.2", ],
    install_requires=["astropy >=4.0", "daf-butler @ https://github.com/lsst/daf_butler/archive/master.tar.gz"],
)