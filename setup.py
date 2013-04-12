try:
    from setuptools import setup
except:
    from distutils.core import setup

setup(
    name='appscope-analyzer',
    version='1.0.0',
    author='Thanasis Petsas',
    author_email='petsas@ics.forth.gr',
    #url='http://bitbucket.org/username/appscope-analyzer',
    py_modules=['appscope-analyzer'],
    entry_points={
        'console_scripts': [
            'appscope-analyzer = appscope-analyzer:_main',
        ],
    },
)
