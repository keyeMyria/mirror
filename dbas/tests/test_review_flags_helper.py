import unittest
from dbas.views import transaction

import dbas.review.helper.flags as ReviewFlagHelper
from dbas.database import DBDiscussionSession
from dbas.helper.tests import add_settings_to_appconfig
from dbas.strings.translator import Translator
from sqlalchemy import engine_from_config

settings = add_settings_to_appconfig()

DBDiscussionSession.configure(bind=engine_from_config(settings, 'sqlalchemy-discussion.'))


class TestReviewFlagHelper(unittest.TestCase):

    def test_flag_argument(self):
        translator = Translator('en')

        success, info, error = ReviewFlagHelper.flag_argument(0, 'reason', 'some_nick', translator, transaction)
        self.__assert_equal_text([[success, ''], [info, ''], [error, translator.get(translator.internalKeyError)]])

        success, info, error = ReviewFlagHelper.flag_argument(4, 'reason', 'some_nick', translator, transaction)
        self.__assert_equal_text([[success, ''], [info, ''], [error, translator.get(translator.internalKeyError)]])

        success, info, error = ReviewFlagHelper.flag_argument(4, 'reason', 'Tobias', translator, transaction)
        self.__assert_equal_text([[success, ''], [info, ''], [error, translator.get(translator.internalKeyError)]])

        success, info, error = ReviewFlagHelper.flag_argument(0, 'reason', 'Tobias', translator, transaction)
        self.__assert_equal_text([[success, ''], [info, ''], [error, translator.get(translator.internalKeyError)]])

        success, info, error = ReviewFlagHelper.flag_argument(4, 'optimization', 'Tobias', translator, transaction)
        self.__assert_equal_text([[success, translator.get(translator.thxForFlagText)], [info, ''], [error, '']])

        success, info, error = ReviewFlagHelper.flag_argument(4, 'optimization', 'Tobias', translator, transaction)
        self.__assert_equal_text([[success, ''], [info, translator.get(translator.alreadyFlaggedByYou)], [error, '']])

        success, info, error = ReviewFlagHelper.flag_argument(4, 'optimization', 'Christian', translator, transaction)
        self.__assert_equal_text([[success, ''], [info, translator.get(translator.alreadyFlaggedByOthers)], [error, '']])

    def __assert_equal_text(self, values):
        for pair in values:
            self.assertEqual(pair[0], pair[1])