import unittest
import pickle
import os

from WhoColor.parser import WikiMarkupParser


class TestParser(unittest.TestCase):
    def test_parser(self):
        test_data_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_data.p')
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


class TestReferenceTemplateAttribution(unittest.TestCase):
    """
    Citation templates inside <ref>...</ref> are normally emitted with no span,
    so the rendered reference carries no authorship. The parser wraps such a
    template in a single span (attributed to its first token's editor) so the
    reference stays attributable after MediaWiki rendering.
    """

    def _token(self, value, editor='1'):
        return {
            'conflict_score': 0,
            'str': value,
            'editor': editor,
            'editor_name': 'Editor {}'.format(editor),
            'class_name': editor,
        }

    def _parse(self, wiki_text, token_specs):
        tokens = [self._token(*spec) if isinstance(spec, tuple) else self._token(spec)
                  for spec in token_specs]
        p = WikiMarkupParser(wiki_text, tokens)
        p.generate_extended_wiki_markup()
        return p.extended_wiki_text

    def test_citation_template_in_ref_is_wrapped_in_a_span(self):
        wiki_text = 'Fact.<ref>{{cite web |url=https://x.org |title=Y}}</ref> More.'
        token_specs = [
            'fact', '.', '<', 'ref', '>',
            ('{{', '7'), ('cite', '7'), ('web', '7'), ('|', '7'), ('url', '7'), ('=', '7'),
            ('https', '7'), (':', '7'), ('/', '7'), ('/', '7'), ('x', '7'), ('.', '7'), ('org', '7'),
            ('|', '7'), ('title', '7'), ('=', '7'), ('y', '7'), ('}}', '7'),
            '<', '/', 'ref', '>', 'more', '.',
        ]

        extended_wiki_text = self._parse(wiki_text, token_specs)

        # The whole template is wrapped in one span for editor 7 (its first token).
        self.assertIn('token-editor-7', extended_wiki_text)
        self.assertIn('>{{cite web |url=https://x.org |title=Y}}</span>', extended_wiki_text)

    def test_template_outside_ref_is_not_wrapped(self):
        wiki_text = '{{Infobox thing|name=X}} Body.'
        token_specs = [
            ('{{', '7'), ('infobox', '7'), ('thing', '7'), ('|', '7'), ('name', '7'), ('=', '7'), ('x', '7'), ('}}', '7'),
            'body', '.',
        ]

        extended_wiki_text = self._parse(wiki_text, token_specs)

        # A template outside <ref> stays no_spans (unchanged behavior).
        self.assertNotIn('>{{Infobox thing|name=X}}</span>', extended_wiki_text)
        self.assertNotIn('token-editor-7', extended_wiki_text)

    def test_self_closing_ref_does_not_open_ref_context(self):
        # A named-ref reuse (<ref name="x"/>) wraps no content, so a following
        # template must not be treated as a citation.
        wiki_text = 'A.<ref name="x"/> B {{convert|5|km}} C.'
        token_specs = [
            'a', '.', '<', 'ref', 'name', '=', 'x', '/', '>', 'b',
            ('{{', '7'), ('convert', '7'), ('|', '7'), ('5', '7'), ('|', '7'), ('km', '7'), ('}}', '7'),
            'c', '.',
        ]

        extended_wiki_text = self._parse(wiki_text, token_specs)

        self.assertNotIn('token-editor-7', extended_wiki_text)

    def test_references_tag_does_not_open_ref_context(self):
        wiki_text = 'Body.<references/> {{Navbox thing}} End.'
        token_specs = [
            'body', '.', '<', 'references', '/', '>',
            ('{{', '7'), ('navbox', '7'), ('thing', '7'), ('}}', '7'),
            'end', '.',
        ]

        extended_wiki_text = self._parse(wiki_text, token_specs)

        self.assertNotIn('token-editor-7', extended_wiki_text)

    def test_references_close_tag_does_not_end_ref_context(self):
        # '</references>' shares the '</ref' prefix matched by the general
        # HTML-tag markup. It must not be mistaken for the '</ref>' that closes
        # ref content; otherwise a citation template still inside the ref would
        # lose its span. The template here sits after a stray '</references>'
        # but before the real '</ref>', so it is only wrapped if ref context
        # survived the '</references>'.
        wiki_text = 'A.<ref>text </references> {{cite web |url=x |title=Y}}</ref> B.'
        token_specs = [
            'a', '.', '<', 'ref', '>', 'text', '<', '/', 'references', '>',
            ('{{', '7'), ('cite', '7'), ('web', '7'), ('|', '7'), ('url', '7'), ('=', '7'), ('x', '7'),
            ('|', '7'), ('title', '7'), ('=', '7'), ('y', '7'), ('}}', '7'),
            '<', '/', 'ref', '>', 'b', '.',
        ]

        extended_wiki_text = self._parse(wiki_text, token_specs)

        self.assertIn('token-editor-7', extended_wiki_text)
        self.assertIn('{{cite web |url=x |title=Y}}</span>', extended_wiki_text)

    def test_nested_template_in_citation_is_wrapped_only_once(self):
        wiki_text = 'A<ref>{{cite |date={{dts|2020}}}}</ref>'
        token_specs = [
            'a', '<', 'ref', '>',
            ('{{', '7'), ('cite', '7'), ('|', '7'), ('date', '7'), ('=', '7'),
            ('{{', '7'), ('dts', '7'), ('|', '7'), ('2020', '7'), ('}}', '7'), ('}}', '7'),
            '<', '/', 'ref', '>',
        ]

        extended_wiki_text = self._parse(wiki_text, token_specs)

        # Exactly one wrapping span for the whole citation, no double-wrapping
        # around the inner {{dts}} template.
        self.assertEqual(extended_wiki_text.count('token-editor-7'), 1)

    def test_plain_text_reference_still_gets_per_token_spans(self):
        # Non-templated references keep their existing per-token attribution.
        wiki_text = 'A.<ref>Smith 2010</ref> B.'
        token_specs = [
            'a', '.', '<', 'ref', '>', ('smith', '7'), ('2010', '8'), '<', '/', 'ref', '>', 'b', '.',
        ]

        extended_wiki_text = self._parse(wiki_text, token_specs)

        self.assertIn('token-editor-7', extended_wiki_text)
        self.assertIn('token-editor-8', extended_wiki_text)
