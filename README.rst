.. You should enable this project on travis-ci.org and coveralls.io to make
   these badges work. The necessary Travis and Coverage config files have been
   generated for you.

.. image:: https://travis-ci.org/CivityNL/ckanext-scorewater.svg?branch=master
    :target: https://travis-ci.org/CivityNL/ckanext-scorewater

.. image:: https://coveralls.io/repos/CivityNL/ckanext-scorewater/badge.svg
  :target: https://coveralls.io/r/CivityNL/ckanext-scorewater

.. image:: https://pypip.in/download/ckanext-scorewater/badge.svg
    :target: https://pypi.python.org/pypi//ckanext-scorewater/
    :alt: Downloads

.. image:: https://pypip.in/version/ckanext-scorewater/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-scorewater/
    :alt: Latest Version

.. image:: https://pypip.in/py_versions/ckanext-scorewater/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-scorewater/
    :alt: Supported Python versions

.. image:: https://pypip.in/status/ckanext-scorewater/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-scorewater/
    :alt: Development Status

.. image:: https://pypip.in/license/ckanext-scorewater/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-scorewater/
    :alt: License

=============
ckanext-scorewater
=============

With this plugin, you extend the dataset schema with multiple new `dataset type` schemas to comply with the scorewater/portal metadata structure.
Every schema serves a different purpose in the SCOREwater portal UI.

------------
Requirements
------------

This plugin includes schemas and thus the ckanext-scheming is a requirement for it to function properly.

------------
Installation
------------

.. Add any additional install steps to the list below.
   For example installing any non-Python dependencies or adding any required
   config settings.

To install ckanext-scorewater:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-scorewater Python package into your virtual environment::

     pip install ckanext-scorewater

3. Add ``scorewater`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


---------------
Config settings
---------------
Enable the plugin by including it in the configuration options::

   ckan.plugins = ... scorewater ...

Enable all scorewater schemas in the configuration options, to get a dropdown menu with several dataset schemas when creating a new dataset::

   #   For scorewater dataset multi-schemas:
   scheming.dataset_multi_schemas = ckanext.scorewater:scheming/multi_schemas/ckan-scorewater.json


.. image:: /images/multi_schema_ckan_dropdown.png

------------------
SCOREwater schemas
------------------

These schemas are built to comply with the SCOREwater portal structure. There are 4 new dataset types declared, extending the default dataset:

- sensor
- service
- source
- supplier

and each of them have its own metadata structure, to take advantage of the SCOREwater portal's UI logic.


.. image:: /images/multi_schema_header.png


------------------------
Development Installation
------------------------

To install ckanext-scorewater for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/CivityNL/ckanext-scorewater.git
    cd ckanext-scorewater
    python setup.py develop
    pip install -r dev-requirements.txt


-----------------
Running the Tests
-----------------

To run the tests, do::

    nosetests --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (``pip install coverage``) then run::

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.scorewater --cover-inclusive --cover-erase --cover-tests


