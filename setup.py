from setuptools import setup

setup(name = 'reflectrpc',
      packages = ['reflectrpc'],
      version = '0.7',
      description = 'JSON-RPC library for creating self-describing RPC services',
      author = 'Andreas Heck',
      author_email = 'aheck@gmx.de',
      license='MIT',
      url = 'https://github.com/aheck/reflectrpc',
      download_url = 'https://github.com/aheck/reflectrpc/archive/v0.7.tar.gz',
      keywords = ['json-rpc', 'json', 'rpc', 'webservice'],
      scripts=['rpcsh'],
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
