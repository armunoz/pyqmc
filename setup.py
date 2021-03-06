'''
Implementation of various machine learning representations for molecules
'''
import setuptools
from distutils.core import setup


def setup_pyqmc():
    setup(
        name='pyqmc',
        maintainer='Lucas Wagner',
        maintainer_email='lkwagner@illinois.edu',
        version=open("VERSION").read().strip(),
        packages=['pyqmc'],
        package_data={'pyqmc': ['data/*.pkl']},
        license='MIT License',
        url='https://github.com/WagnerGroup/pyqmc',
        description='Python library for real space quantum Monte Carlo',
        long_description=open('README.md').read(),
        long_description_content_type='text/markdown',
        install_requires=[
            "scipy",
            "pandas",
            "pyscf",
            "pyblock"
        ],
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Science/Research',
            'Programming Language :: Python',
            'License :: OSI Approved :: MIT License',
            'Topic :: Scientific/Engineering :: Chemistry :: Physics',
        ],
    )


if __name__ == '__main__':
    setup_pyqmc()
