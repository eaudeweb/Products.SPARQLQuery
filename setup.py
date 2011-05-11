from setuptools import setup, find_packages
import sys

install_requires = []
if sys.version_info < (2, 6):
    install_requires += ['simplejson']

setup(
    name='Products.SPARQLQuery',
    version='0.1',
    description="Zope product for making SPARQL queries, simiar to ZSQLMethod",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
)
