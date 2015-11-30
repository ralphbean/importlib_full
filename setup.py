from distutils.core import setup
import sys


version_classifiers = ['Programming Language :: Python :: %s' % version
                       for version in [
                           '2', '2.4', '2.5', '2.6', '2.7',
                           '3', '3.0', '3.1', '3.2',
                       ]]
other_classifiers = [
    'Development Status :: 3 - Alpha',
    'License :: OSI Approved :: Python Software Foundation License',
]

readme_file = open('README', 'r')
try:
    detailed_description = readme_file.read()
finally:
    readme_file.close()


setup(
    name='importlib_full',
    version='0.0.2',
    description="Abandoned.  Do not use.",
    long_description=detailed_description,
    author='Ralph Bean',
    author_email='rbean@redhat.com',
    url='http://github.com/ralphbean/importlib_full',
    packages=[
        'importlib_full',
        'importlib_full.test',
        'importlib_full.test.import_',
    ],
    classifiers=version_classifiers + other_classifiers,
)
