import pickle
from os.path import exists

from WhoColor.utils import WikipediaRevText, WikiWhoRevContent
from WhoColor.parser import WikiMarkupParser


def prepare_test_data(save_to_file, test_articles=None):
    if not test_articles:
        test_articles = ['Amstrad CPC', 'Antarctica', 'Apollo 11', 'Armenian Genocide', 'Barack_Obama',
                         'Bioglass', 'Bothrops_jararaca', 'Chlorine', 'Circumcision', 'Communist Party of China',
                         'Democritus', 'Diana,_Princess_of_Wales', 'Encryption', 'Eritrean Defence Forces',
                         'European Free Trade Association', 'Evolution', 'Geography of El Salvador', 'Germany',
                         'Home and Away', 'Homeopathy', 'Iraq War', 'Islamophobia', 'Jack the Ripper', 'Jesus',
                         'KLM destinations', 'Lemur', 'Macedonians_(ethnic_group)', 'Muhammad', 'Newberg, Oregon',
                         'Race_and_intelligence', 'Rhapsody_on_a_Theme_of_Paganini', 'Robert Hues', "Saturn's_moons_in_fiction",
                         'Sergei Korolev', 'South_Western_main_line', 'Special Air Service', 'The_Holocaust', 'Toshitsugu_Takamatsu',
                         'Vladimir_Putin', 'Wernher_von_Braun']

    if exists(save_to_file):
        with open(save_to_file, 'rb') as f:
            test_data = pickle.load(f)
    else:
        test_data = {}

    for title in test_articles:
        print(title, ' started ...')
        if title not in test_data:
            # get rev wiki text from wp
            wp_rev_text_obj = WikipediaRevText(page_title=title, language='en')
            # {'page_id': , 'namespace': , 'rev_id': , 'rev_text': }
            rev_data = wp_rev_text_obj.get_rev_wiki_text()

            # get revision content (authorship data)
            ww_rev_content_obj = WikiWhoRevContent(page_id=rev_data['page_id'],
                                                   rev_id=rev_data['rev_id'],
                                                   language='en')
            # revisions {rev_id: [timestamp, parent_id, class_name/editor, editor_name]}
            # tokens [[conflict_score, str, o_rev_id, in, out, editor/class_name, age]]
            # biggest conflict score (int)

            revisions = ww_rev_content_obj.get_revisions_data()
            editor_names_dict = ww_rev_content_obj.get_editor_names(revisions)
            tokens, biggest_conflict_score = ww_rev_content_obj.get_tokens_data(revisions, editor_names_dict)

            # annotate authorship data to wiki text
            # if registered user, class name is editor id
            p = WikiMarkupParser(rev_data['rev_text'], tokens)
            p.generate_extended_wiki_markup()
            extended_html = wp_rev_text_obj.convert_wiki_text_to_html(p.extended_wiki_text)

            test_data[title] = {'extended_html': extended_html,
                                'extended_wiki_text': p.extended_wiki_text,
                                'present_editors': p.present_editors,
                                'revisions': revisions,
                                'tokens': tokens,
                                'biggest_conflict_score': biggest_conflict_score,
                                'rev_text': rev_data['rev_text']}
            with open(save_to_file, 'wb') as f:
                pickle.dump(test_data, f)
        print(title, ' ended ...')
    with open(save_to_file, 'wb') as f:
        pickle.dump(test_data, f)


def shrink_test_data(from_file, to_file):
    with open(from_file, 'rb') as f:
        test_data = pickle.load(f)

    test_data_shrink = {}
    i = 0
    limit = 10
    for title, data in test_data.items():
        test_data_shrink[title] = data
        i += 1
        if i >= limit:
            break

    with open(to_file, 'wb') as f:
        pickle.dump(test_data_shrink, f)
