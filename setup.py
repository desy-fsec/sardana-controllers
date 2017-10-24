#!/usr/bin/env python

import os
import imp
from setuptools import setup

release = "1.0.0"

package_dir = {"PoolControllers": "python"}

packages = ["PoolControllers"]

provides = [
    'python',
]


setup(name='PoolControllers',
      version=1.0,
#      description=release.description,
#      long_description=release.long_description,
      author="Sardana Controller Developers",
      author_email="fs-ec@desy.de",
      maintainer="DESY",
      maintainer_email="fs-ec@desy.de",
      url="https://stash.desy.de/projects/JMK/repos/sardana-controllers/browse",
#      download_url=release.download_url,
#      platforms=release.platforms,
#      license=release.license,
#      keywords=release.keywords,
      packages=packages,
      package_dir=package_dir,
      include_package_data=True,
#      classifiers=classifiers,
#      entry_points=entry_points,
      provides=provides,
#      requires=requires,
#      install_requires=install_requires,
#      test_suite='sardana.test.testsuite.get_sardana_unitsuite',
      )
