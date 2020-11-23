from setuptools import setup

version = "0.0.1"

with open("README.md", "r") as fh:
    long_description = fh.read()

# packages are organized according to PEP-420:
#    https://www.python.org/dev/peps/pep-0420/
setup(
    version=version,
    long_description=long_description,
    long_description_content_type="text/markdown",
)
