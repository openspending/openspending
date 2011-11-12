
Summary and Conventions
=======================

Authentication
''''''''''''''

Some actions in OpenSpending require authentication, particularly those 
that write to the system or aim to access protected data (e.g. 
pre-publication datasets). For this purpose, each user is provided an 
API key. The key is displayed in the *Settings* mask and can be used to
perform HTTP Basic-style authentication::

  Authorization: ApiKey f47ac10b-58cc-4372-a567-0e02b2c3d479


JSON-P Callbacks
''''''''''''''''

All API calls that return JSON support JSON-P (JSON with padding). You can 
add a ``?callback=foo`` parameter to any query to wrap the output in a 
function call. This is used to include JSON data in other sites that do not
support CORS::

  $ curl http://openspending.org/cra.json?callback=foo

  foo({
    "description": "Data published by HM Treasury.", 
    "name": "cra", 
    "label": "Country Regional Analysis v2009", 
    "currency": "GBP"
  });

This can be used in remote web pages to include data as a simple ``script``
tag:

.. code-block:: html

    <script>
      function foo(data) { 
        alert(data.label); 
      }
    </script>
    <script src="http://openspending.org/cra.json?callback=foo"></script>


Cross Origin Resource Sharing
'''''''''''''''''''''''''''''

The API does not yet support `CORS <http://code.google.com/p/html5security/wiki/CrossOriginRequestSecurity>`_ 
but support will be added in the near future.
