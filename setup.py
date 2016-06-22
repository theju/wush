from setuptools import setup, find_packages

VERSION = '0.0.1'

setup(name='wush',
      version=VERSION,
      description='A django app to send web and mobile push notifications',
      author='Thejaswi Puthraya',
      author_email='thejaswi.puthraya@gmail.com',
      url='https://github.com/theju/wush',
      license="MIT",
      packages=find_packages(),
      requires=open("requirements.txt").readlines()
     )
