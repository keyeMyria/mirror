import unittest

import transaction
from pyramid import testing

import dbas.handler.issue as ih
from dbas.database import DBDiscussionSession
from dbas.database.discussion_model import Issue, User, Language
from dbas.lib import nick_of_anonymous_user
from dbas.strings.translator import Translator


class IssueHandlerTests(unittest.TestCase):

    def test_set_issue(self):
        db_user = DBDiscussionSession.query(User).filter_by(nickname='Tobias').first()
        db_lang = DBDiscussionSession.query(Language).filter_by(ui_locales='en').first()
        info = 'infoinfoinfo'
        long_info = 'long_infolong_infolong_info'
        title = 'titletitletitle'
        response = ih.set_issue(db_user, info, long_info, title, db_lang, False, False)
        self.assertTrue(len(response['issue']) >= 0)

        DBDiscussionSession.query(Issue).filter_by(title=title).delete()
        DBDiscussionSession.flush()
        transaction.commit()

    def test_prepare_json_of_issue(self):
        uid = 1

        db_user = DBDiscussionSession.query(User).filter_by(nickname=nick_of_anonymous_user).first()
        db_issue = DBDiscussionSession.query(Issue).get(uid)
        response = ih.prepare_json_of_issue(db_issue, db_user)
        self.assertTrue(len(response) > 0)

    def test_get_number_of_arguments(self):
        response = ih.get_number_of_arguments(0)
        self.assertTrue(response == 0)
        response = ih.get_number_of_arguments(1)
        self.assertTrue(response > 0)

    def test_get_number_of_statements(self):
        response = ih.get_number_of_statements(0)
        self.assertTrue(response == 0)
        response = ih.get_number_of_statements(1)
        self.assertTrue(response > 0)

    def test_get_issue_dict_for(self):
        issue = DBDiscussionSession.query(Issue).first()
        uid = issue.uid
        lang = 'en'
        response = ih.get_issue_dict_for(issue, uid, lang)
        self.assertTrue(len(response) > 0)
        self.assertTrue(len(response['error']) == 0)

    def test_get_id_of_slug(self):
        issue = DBDiscussionSession.query(Issue).filter_by(is_disabled=False).first()
        slug = issue.slug
        response = ih.get_id_of_slug(slug)
        self.assertEqual(response.uid, issue.uid)

    def test_get_issue_id(self):
        request = testing.DummyRequest(matchdict={'issue': 1})
        response = ih.get_issue_id(request)
        self.assertEqual(1, response)

        request = testing.DummyRequest(params={'issue': 2})
        response = ih.get_issue_id(request)
        self.assertEqual(2, response)

        request = testing.DummyRequest(session={'issue': 3})
        response = ih.get_issue_id(request)
        self.assertEqual(3, response)

        request = testing.DummyRequest(json_body={'issue': 4})
        response = ih.get_issue_id(request)
        self.assertEqual(4, response)

    def test_get_title_for_slug(self):
        issue = DBDiscussionSession.query(Issue).first()
        slug = issue.slug
        response = ih.get_title_for_slug(slug)
        self.assertEqual(issue.title, response)

    def test_get_issues_overiew(self):
        db_user = DBDiscussionSession.query(User).get(2)
        response = ih.get_issues_overiew(db_user, 'http://test.url')
        self.assertIn('user', response)
        self.assertIn('other', response)
        self.assertTrue(len(response['user']) > 0)
        self.assertTrue(len(response['other']) == 0)

        db_user = DBDiscussionSession.query(User).get(3)
        response = ih.get_issues_overiew(db_user, 'http://test.url')
        self.assertIn('user', response)
        self.assertIn('other', response)
        self.assertTrue(len(response['user']) == 0)
        self.assertTrue(len(response['other']) > 0)

    def test_get_issues_overview_on_start(self):
        db_user = DBDiscussionSession.query(User).get(2)
        response = ih.get_issues_overview_on_start(db_user)
        self.assertIn('issues', response)
        self.assertIn('data', response)

    def test_set_discussions_properties(self):
        db_walter = DBDiscussionSession.query(User).filter_by(nickname='Walter').one_or_none()
        issue_slug = 'cat-or-dog'
        db_issue = DBDiscussionSession.query(Issue).filter_by(slug=issue_slug).one()
        translator = Translator('en')

        enable = True
        response = ih.set_discussions_properties(db_walter, db_issue, enable, 'somekeywhichdoesnotexist', translator)
        self.assertTrue(len(response['error']) > 0)

        db_christian = DBDiscussionSession.query(User).filter_by(nickname='Christian').one_or_none()
        response = ih.set_discussions_properties(db_christian, db_issue, enable, 'somekeywhichdoesnotexist', translator)
        self.assertTrue(len(response['error']) > 0)

        response = ih.set_discussions_properties(db_christian, db_issue, enable, 'somekeywhichdoesnotexist', translator)
        self.assertTrue(len(response['error']) > 0)

        db_tobias = DBDiscussionSession.query(User).filter_by(nickname='Tobias').one_or_none()
        response = ih.set_discussions_properties(db_tobias, db_issue, enable, 'enable', translator)
        transaction.commit()
        self.assertTrue(len(response['error']) == 0)
        self.assertTrue(DBDiscussionSession.query(Issue).filter_by(slug=issue_slug).one().is_disabled is False)

        enable = False
        response = ih.set_discussions_properties(db_tobias, db_issue, enable, 'enable', translator)
        transaction.commit()
        self.assertTrue(len(response['error']) == 0)
        self.assertTrue(DBDiscussionSession.query(Issue).filter_by(slug=issue_slug).one().is_disabled is True)

        enable = True
        response = ih.set_discussions_properties(db_tobias, db_issue, enable, 'enable', translator)
        transaction.commit()
        self.assertTrue(len(response['error']) == 0)
        self.assertTrue(DBDiscussionSession.query(Issue).filter_by(slug=issue_slug).one().is_disabled is False)
