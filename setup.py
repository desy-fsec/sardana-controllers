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
#      author=release.authors['Tiago_et_al'][0],
#      maintainer=release.authors['Community'][0],
#      maintainer_email=release.authors['Community'][1],
#      url=release.url,
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
