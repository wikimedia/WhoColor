import unittest
from unittest import mock

import requests

from WhoColor import __version__
from WhoColor import utils
from WhoColor.utils import USER_AGENT, WikiWhoRevContent, _request_json


class _FakeResponse(object):
    def __init__(self, status_code=200, json_body=None):
        self.status_code = status_code
        self._json_body = json_body if json_body is not None else {}

    def json(self):
        return self._json_body

    def raise_for_status(self):
        if 400 <= self.status_code < 600:
            error = requests.HTTPError('{} error'.format(self.status_code))
            error.response = self
            raise error


class _FakeMethod(object):
    """Callable stand-in for requests.get/post that yields queued responses."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def __call__(self, **kwargs):
        self.calls += 1
        response = self._responses[min(self.calls - 1, len(self._responses) - 1)]
        if isinstance(response, Exception):
            raise response
        return response


class TestRequestJson(unittest.TestCase):
    """Offline coverage for _request_json's status handling and retry policy."""

    def setUp(self):
        # Don't actually wait during retry backoff.
        patcher = mock.patch.object(utils.time, 'sleep')
        self.sleep = patcher.start()
        self.addCleanup(patcher.stop)

    def test_success_returns_json_body(self):
        method = _FakeMethod([_FakeResponse(200, {'revisions': [1]})])
        self.assertEqual({'revisions': [1]}, _request_json(method))
        self.assertEqual(1, method.calls)

    def test_ok_body_with_mediawiki_error_key_is_returned_not_raised(self):
        # The Wikipedia API returns logical errors as HTTP 200 with an 'error'
        # key; that must still reach the caller, which handles it itself.
        method = _FakeMethod([_FakeResponse(200, {'error': {'code': 'nosuchpage'}})])
        self.assertEqual({'error': {'code': 'nosuchpage'}}, _request_json(method))
        self.assertEqual(1, method.calls)

    def test_client_error_fails_fast_without_retrying(self):
        method = _FakeMethod([_FakeResponse(404, {'Error': 'not found'})])
        with self.assertRaises(requests.HTTPError):
            _request_json(method)
        self.assertEqual(1, method.calls)
        self.assertFalse(self.sleep.called)

    def test_server_error_is_retried_then_raised(self):
        method = _FakeMethod([_FakeResponse(500, {'Error': 'boom'})])
        with self.assertRaises(requests.HTTPError):
            _request_json(method)
        self.assertEqual(utils.REQUEST_ATTEMPTS, method.calls)
        self.assertEqual(utils.REQUEST_ATTEMPTS - 1, self.sleep.call_count)

    def test_rate_limit_is_retried(self):
        method = _FakeMethod([_FakeResponse(429, {}), _FakeResponse(200, {'ok': True})])
        self.assertEqual({'ok': True}, _request_json(method))
        self.assertEqual(2, method.calls)


class TestUtils(unittest.TestCase):
    def test_user_agent_uses_package_version(self):
        self.assertEqual('WhoColor/{} (https://github.com/wikimedia/WhoColor)'.format(__version__), USER_AGENT)

    def test_wikiwho_from_page_id(self):
        # Page ID of 'Selfie'
        page_id = 38956275
        language = 'en'
        ww_rev_content = WikiWhoRevContent(page_id=page_id, language=language)
        # test if request data is correct
        request_data = ww_rev_content._prepare_request()
        data = {'url': 'https://wikiwho-api.wmcloud.org/{}/api/v1.0.0-beta/rev_content/page_id/{}/'.format(language, page_id),
                'params': {'o_rev_id': 'true', 'editor': 'true', 'token_id': 'false', 'out': 'true', 'in': 'true'}}
        assert request_data == data
        # check if no errors
        ww_rev_content.get_revisions_and_tokens()

    def test_wikiwho_from_page_title(self):
        page_title = 'Selfie'
        language = 'en'
        ww_rev_content = WikiWhoRevContent(page_title=page_title, language=language)
        # test if request data is correct
        request_data = ww_rev_content._prepare_request()
        data = {'url': 'https://wikiwho-api.wmcloud.org/{}/api/v1.0.0-beta/rev_content/{}/'.format(language, page_title),
                'params': {'o_rev_id': 'true', 'editor': 'true', 'token_id': 'false', 'out': 'true', 'in': 'true'}}
        assert request_data == data
        # check if no errors
        ww_rev_content.get_revisions_and_tokens()

    def test_wikiwho_from_rev_id(self):
        # First revision of 'Selfie'
        page_title = 'Selfie'
        rev_id = 547645475
        language = 'en'
        ww_rev_content = WikiWhoRevContent(page_title=page_title, rev_id=rev_id, language=language)
        # test if request data is correct
        request_data = ww_rev_content._prepare_request()
        data = {'url': 'https://wikiwho-api.wmcloud.org/{}/api/v1.0.0-beta/rev_content/{}/{}/'.format(language, page_title, rev_id),
                'params': {'o_rev_id': 'true', 'editor': 'true', 'token_id': 'false', 'out': 'true', 'in': 'true'}}
        assert request_data == data
        # check if no errors
        ww_rev_content.get_revisions_and_tokens()
