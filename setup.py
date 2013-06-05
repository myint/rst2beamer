from setuptools import setup
import os

from rst2beamer import __version__

setup(
    name='rst2beamer',
    version=__version__,
    description='A docutils writer and script for converting restructured '
                'text to the Beamer presentation format',
    long_description=open('README.rst').read() + '\n' +
                open(os.path.join('docs', 'HISTORY.txt')).read(),
    classifiers=[
                'Development Status :: 5 - Production/Stable',
                'License :: OSI Approved :: GNU General Public License (GPL)',
                'Programming Language :: Python',
                'Topic :: Text Processing :: Markup',
                'Topic :: Utilities',
                'Topic :: Multimedia :: Graphics :: Presentation',
    ],
    keywords='presentation docutils rst restructured-text',
    author='Ryan Krauss & Paul-Michael Agapow',
    author_email='ryanwkrauss@gmail.com, agapow@bbsrc.ac.uk',
    url='http://www.agapow.net/software/rst2beamer',
        license='GPL',
        py_modules=['rst2beamer'],
        zip_safe=False,
        install_requires=[
                'docutils',
        ],
    entry_points={
        'console_scripts': [
            'rst2beamer = rst2beamer:main',
        ],
    },
)
