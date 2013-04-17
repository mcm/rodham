from distutils.core import setup
from setuptools import find_packages

setup(
    name='Rodham',
    version='1.0.0',
    author='Steve McMaster',
    author_email='mcmaster@hurricanelabs.com',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    url='https://code.hurricanelabs.com/hg/rodham',
    description='Rodham Python XMPP Bot',
    install_requires=[
        "configobj",
        "dnspython",
        "mechanize",
        "peewee",
        "pyst",
        "python-daemon==1.4.5",
        "python-ldap",
        "requests",
        "sleekxmpp",
    ],
    dependency_links=[
        "svn+https://pyst.svn.sourceforge.net/svnroot/pyst/pyst/trunk#egg=pyst-0.4.38",
    ],
    entry_points={
        'console_scripts': [
            'rodham = rodham.daemon:main',
        ]
    },
)
