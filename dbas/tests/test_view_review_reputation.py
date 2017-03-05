import unittest

from pyramid import testing

from dbas.database import DBDiscussionSession
from dbas.helper.tests import add_settings_to_appconfig, verify_dictionary_of_view
from sqlalchemy import engine_from_config


class ReviewReputationViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_chameleon')

    def tearDown(self):
        testing.tearDown()

    def test_page(self):
        from dbas.views import review_reputation as d

        request = testing.DummyRequest()
        response = d(request)
        verify_dictionary_of_view(self, response)
        self.assertIn('reputation', response)
        self.assertTrue(len(response['reputation']) == 0)

    def test_page_logged_in(self):
        self.config.testing_securitypolicy(userid='Tobias', permissive=True)
        from dbas.views import review_reputation as d

        request = testing.DummyRequest()
        response = d(request)
        verify_dictionary_of_view(self, response)
        self.assertIn('reputation', response)
        self.assertTrue(len(response['reputation']) != 0)
