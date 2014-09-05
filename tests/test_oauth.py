import datetime
import unittest
from provider import scope as oauth2_provider_scope
from rest_framework.test import APIClient
from rest_framework_oauth.authentication import oauth2_provider
from rest_framework import status
from django.utils.http import urlencode
from django.test import TestCase
from django.contrib.auth.models import User


class OAuth2Tests(TestCase):
    """OAuth 2.0 authentication"""
    urls = 'tests.test_authentication'

    def setUp(self):
        self.csrf_client = APIClient(enforce_csrf_checks=True)
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(self.username, self.email, self.password)

        self.CLIENT_ID = 'client_key'
        self.CLIENT_SECRET = 'client_secret'
        self.ACCESS_TOKEN = "access_token"
        self.REFRESH_TOKEN = "refresh_token"

        self.oauth2_client = oauth2_provider.oauth2.models.Client.objects.create(
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            redirect_uri='',
            client_type=0,
            name='example',
            user=None,
        )

        self.access_token = oauth2_provider.oauth2.models.AccessToken.objects.create(
            token=self.ACCESS_TOKEN,
            client=self.oauth2_client,
            user=self.user,
        )
        self.refresh_token = oauth2_provider.oauth2.models.RefreshToken.objects.create(
            user=self.user,
            access_token=self.access_token,
            client=self.oauth2_client
        )

    def _create_authorization_header(self, token=None):
        return "Bearer {0}".format(token or self.access_token.token)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_get_form_with_wrong_authorization_header_token_type_failing(self):
        """Ensure that a wrong token type lead to the correct HTTP error status code"""
        auth = "Wrong token-type-obsviously"
        response = self.csrf_client.get('/oauth2-test/', {}, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)
        response = self.csrf_client.get('/oauth2-test/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_get_form_with_wrong_authorization_header_token_format_failing(self):
        """Ensure that a wrong token format lead to the correct HTTP error status code"""
        auth = "Bearer wrong token format"
        response = self.csrf_client.get('/oauth2-test/', {}, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)
        response = self.csrf_client.get('/oauth2-test/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_get_form_with_wrong_authorization_header_token_failing(self):
        """Ensure that a wrong token lead to the correct HTTP error status code"""
        auth = "Bearer wrong-token"
        response = self.csrf_client.get('/oauth2-test/', {}, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)
        response = self.csrf_client.get('/oauth2-test/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_get_form_with_wrong_authorization_header_token_missing(self):
        """Ensure that a missing token lead to the correct HTTP error status code"""
        auth = "Bearer"
        response = self.csrf_client.get('/oauth2-test/', {}, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)
        response = self.csrf_client.get('/oauth2-test/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_get_form_passing_auth(self):
        """Ensure GETing form over OAuth with correct client credentials succeed"""
        auth = self._create_authorization_header()
        response = self.csrf_client.get('/oauth2-test/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_passing_auth_url_transport(self):
        """Ensure GETing form over OAuth with correct client credentials in form data succeed"""
        response = self.csrf_client.post(
            '/oauth2-test/',
            data={'access_token': self.access_token.token}
        )
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_get_form_passing_auth_url_transport(self):
        """Ensure GETing form over OAuth with correct client credentials in query succeed when DEBUG is True"""
        query = urlencode({'access_token': self.access_token.token})
        response = self.csrf_client.get('/oauth2-test-debug/?%s' % query)
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_get_form_failing_auth_url_transport(self):
        """Ensure GETing form over OAuth with correct client credentials in query fails when DEBUG is False"""
        query = urlencode({'access_token': self.access_token.token})
        response = self.csrf_client.get('/oauth2-test/?%s' % query)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_passing_auth(self):
        """Ensure POSTing form over OAuth with correct credentials passes and does not require CSRF"""
        auth = self._create_authorization_header()
        response = self.csrf_client.post('/oauth2-test/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_token_removed_failing_auth(self):
        """Ensure POSTing when there is no OAuth access token in db fails"""
        self.access_token.delete()
        auth = self._create_authorization_header()
        response = self.csrf_client.post('/oauth2-test/', HTTP_AUTHORIZATION=auth)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_with_refresh_token_failing_auth(self):
        """Ensure POSTing with refresh token instead of access token fails"""
        auth = self._create_authorization_header(token=self.refresh_token.token)
        response = self.csrf_client.post('/oauth2-test/', HTTP_AUTHORIZATION=auth)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_with_expired_access_token_failing_auth(self):
        """Ensure POSTing with expired access token fails with an 'Invalid token' error"""
        self.access_token.expires = datetime.datetime.now() - datetime.timedelta(seconds=10)  # 10 seconds late
        self.access_token.save()
        auth = self._create_authorization_header()
        response = self.csrf_client.post('/oauth2-test/', HTTP_AUTHORIZATION=auth)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
        self.assertIn('Invalid token', response.content)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_with_invalid_scope_failing_auth(self):
        """Ensure POSTing with a readonly scope instead of a write scope fails"""
        read_only_access_token = self.access_token
        read_only_access_token.scope = oauth2_provider_scope.SCOPE_NAME_DICT['read']
        read_only_access_token.save()
        auth = self._create_authorization_header(token=read_only_access_token.token)
        response = self.csrf_client.get('/oauth2-with-scope-test/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)
        response = self.csrf_client.post('/oauth2-with-scope-test/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_with_valid_scope_passing_auth(self):
        """Ensure POSTing with a write scope succeed"""
        read_write_access_token = self.access_token
        read_write_access_token.scope = oauth2_provider_scope.SCOPE_NAME_DICT['write']
        read_write_access_token.save()
        auth = self._create_authorization_header(token=read_write_access_token.token)
        response = self.csrf_client.post('/oauth2-with-scope-test/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)