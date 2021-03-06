import unittest

from pyramid import testing

from dbas.helper.test import verify_dictionary_of_view


class DiscussionFinishViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_chameleon')

    def tearDown(self):
        testing.tearDown()

    def test_page(self):
        from dbas.views import discussion_exit as d

        request = testing.DummyRequest()
        response = d(request)
        verify_dictionary_of_view(response)
