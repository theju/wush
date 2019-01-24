import configparser

from setuptools import setup, find_packages

VERSION = '0.0.2'

def packages_from_pipfile():
    cfg = configparser.ConfigParser()
    cfg.read('Pipfile')
    return [ii for ii in cfg['packages'].keys()]

setup(name='wush',
      version=VERSION,
      description='A django app to send web and mobile push notifications',
      long_description=open('README.md').read(),
      author='Thejaswi Puthraya',
      author_email='thejaswi.puthraya@gmail.com',
      url='https://github.com/theju/wush',
      license="MIT",
      packages=find_packages(),
      install_requires=packages_from_pipfile()
     )
