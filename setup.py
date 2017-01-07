#!/usr/bin/env python

from distutils.core import setup
import pylcd

with open("README.md") as file:
	long_description = file.read()

setup(
		name=pylcd.NAME,
		version=pylcd.VERSION,
		description=pylcd.DESCRIPTION,
		long_description=long_description,
		author=pylcd.AUTHOR,
		author_email=pylcd.AUTHOR_EMAIL,
		url=pylcd.URL,
		license=pylcd.LICENSE,

		py_modules=["pylcd"],
		)
