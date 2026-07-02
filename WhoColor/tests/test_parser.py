import unittest
import pickle
import os

from WhoColor.parser import WikiMarkupParser


class TestParser(unittest.TestCase):
    def _token(self, value):
        return {
            'conflict_score': 0,
            'str': value,
            'editor': '1',
            'editor_name': 'Editor',
            'class_name': '1',
        }

    def _parse(self, wiki_text, token_values):
        p = WikiMarkupParser(wiki_text, [self._token(value) for value in token_values])
        p.generate_extended_wiki_markup()
        return p.extended_wiki_text

    def test_unmatched_bracket_in_reference_template_does_not_disable_later_spans(self):
        wiki_text = 'Lead.<ref>{{Cite web |first=John [R-TX |title=Foo}}</ref> After text.'
        token_values = [
            'lead', '.', '<', 'ref', '>', '{{', 'cite', 'web', '|', 'first', '=',
            'john', '[', 'r', '-', 'tx', '|', 'title', '=', 'foo', '}}', '<',
            '/', 'ref', '>', 'after', 'text', '.',
        ]

        extended_wiki_text = self._parse(wiki_text, token_values)

        self.assertIn('id="token-25"', extended_wiki_text)
        self.assertIn('id="token-26"', extended_wiki_text)
        self.assertIn('After', extended_wiki_text)

    def test_real_external_link_still_parses_as_single_markup_block(self):
        cases = [
            ('Lead [https://example.org label] tail.',
             ['lead', '[', 'https', ':', '/', '/', 'example', '.', 'org',
              'label', ']', 'tail', '.']),
            ('Lead [mailto:user@example.org label] tail.',
             ['lead', '[', 'mailto', ':', 'user', '@', 'example', '.', 'org',
              'label', ']', 'tail', '.']),
            ('Lead [//example.org label] tail.',
             ['lead', '[', '/', '/', 'example', '.', 'org', 'label', ']', 'tail', '.']),
        ]

        for wiki_text, token_values in cases:
            extended_wiki_text = self._parse(wiki_text, token_values)

            self.assertIn('id="token-1"', extended_wiki_text)
            self.assertNotIn('id="token-2"', extended_wiki_text)
            self.assertIn('id="token-{}"'.format(len(token_values) - 2), extended_wiki_text)

    def test_unclosed_external_link_start_does_not_disable_later_spans(self):
        wiki_text = 'Lead [https://example.org tail after.'
        token_values = [
            'lead', '[', 'https', ':', '/', '/', 'example', '.', 'org',
            'tail', 'after', '.',
        ]

        extended_wiki_text = self._parse(wiki_text, token_values)

        self.assertIn('id="token-9"', extended_wiki_text)
        self.assertIn('id="token-10"', extended_wiki_text)

    def test_parser(self):
        test_data_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_data.p')
        if not os.path.exists(test_data_file_path):
            self.skipTest('optional parser golden fixture is not present')
        with open(test_data_file_path, 'rb') as f:
            test_data = pickle.load(f)

        for article, data in test_data.items():
            p = WikiMarkupParser(data['rev_text'], data['tokens'])
            p.generate_extended_wiki_markup()

            # Some of the entries in tuple are out of order. Not sure why and hence sorting both based on author id
            p.present_editors = tuple(sorted(list(p.present_editors), key=lambda x: x[0]))
            data['present_editors'] = tuple(sorted(list(data['present_editors']), key=lambda x: x[0]))

            assert p.extended_wiki_text == data['extended_wiki_text'], article
            assert p.present_editors == data['present_editors'], article
