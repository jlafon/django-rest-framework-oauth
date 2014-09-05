django-rest-framework-oauth
===========================

OAuth Support for the Django REST Framework

This project is an attempt to address issue [1767](https://github.com/tomchristie/django-rest-framework/issues/1767) of
the Django REST Framework, separating OAuth support into a third party package.

# The plan
* Step one is to pull out the appropriate bits into this package, with tests, and get the tests to pass.
* Step two is to tackle [1765](https://github.com/tomchristie/django-rest-framework/issues/1765) by moving on to oauthlib.
