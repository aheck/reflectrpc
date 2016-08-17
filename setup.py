import os

from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name = 'reflectrpc',
      packages = ['reflectrpc'],
      version = '0.7.5',
      description = 'Self-describing JSON-RPC services made easy',
      long_description=read('CHANGELOG.rst'),
      author = 'Andreas Heck',
      author_email = 'aheck@gmx.de',
      license = 'MIT',
      url = 'https://github.com/aheck/reflectrpc',
      download_url = 'https://github.com/aheck/reflectrpc/archive/v0.7.5.tar.gz',
      include_package_data=True,
      keywords = 'json-rpc jsonrpc rpc webservice',
      scripts = ['rpcsh', 'rpcdoc', 'rpcgencode'],
      install_requires = ['future', 'service_identity', 'twisted', 'pyOpenSSL'],
      classifiers = [
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5'
      ]
)
