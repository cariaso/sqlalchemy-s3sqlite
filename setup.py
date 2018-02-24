from setuptools import setup

setup(name='sqlalchemy-s3sqlite',
      version='0.1',
      description='persist a sqlite database in s3, for use with lambda',
      url='http://github.com/cariaso/sqlalchemy-s3sqlite',
      author='cariaso',
      author_email='cariaso@gmail.com',
      license='MIT',
      packages=['sqlalchemy-s3sqlite'],
      zip_safe=False)
