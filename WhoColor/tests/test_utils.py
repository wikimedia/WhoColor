import unittest
from WhoColor import __version__
from WhoColor.utils import USER_AGENT, WikiWhoRevContent


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
