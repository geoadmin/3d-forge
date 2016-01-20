# -*- coding: utf-8 -*-

from setuptools import setup

requires = [
        'autopep8',
        'flake8',
        'ipython==4.0.0',
        'nose',
        'mako',
        'awscli>=1.7.31',
        'boto>=2.38',
        'psycopg2',
        'numpy',
        'sqlalchemy',
        'shapely',
        'geoalchemy2==0.3.0.dev1',
        'requests',
        'pyproj',
    ]

setup(name='3d-forge',
      version='0.0',
      description='QMesh reader/writer',
      url='',
      author='',
      author_email='',
      license='MIT',
      packages=['forge'],
      zip_safe=False,
      install_requires=requires,
      )
