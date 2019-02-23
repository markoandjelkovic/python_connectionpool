from setuptools import find_packages
from setuptools import setup

setup(
	name="connectionpool",
	version="0.1",
	description="Simple connection pool framework",
	license="MIT",
	packages=find_packages(exclude=["test"]),
	test_suite="test"
)
