import unittest
import transaction

from pyramid import testing
from dbas.strings import text_generator as tg
from dbas.strings.keywords import Keywords as _
from dbas.strings.translator import Translator
from dbas.database import DBDiscussionSession
from dbas.database.discussion_model import Argument, User, MarkedArgument


class TextGeneratorText(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_chameleon')
        self.premise = 'Some premise text'
        self.conclusion = 'Some conclusion text'
        self.confrontation = 'Some confrontation text'
        self.maxDiff = None

        # test every ajax method, which is not used in other classes

    def tearDown(self):
        testing.tearDown()

    def test_get_text_for_add_premise_container_on_support(self):
        _t = Translator('en')

        is_supportive = True

        undermine = _t.get(_.itIsFalseThat) + ' ' + self.premise
        support = _t.get(_.itIsTrueThat) if is_supportive else _t.get(_.itIsFalseThat)
        support += ' ' + self.conclusion + ' '
        support += _t.get(_.hold) if is_supportive else _t.get(_.doesNotHold)
        undercut = self.confrontation + ', ' + _t.get(_.butIDoNotBelieveCounterFor).format(self.conclusion)
        rebut = self.confrontation + ' '
        rebut += _t.get(_.iAcceptCounterThat) if is_supportive else _t.get(_.iAcceptArgumentThat)
        rebut += ' ' + self.conclusion

        results = {
            'undermine': undermine + ' ...',
            'support': support + ' ...',
            'undercut': undercut + ' ...',
            'rebut': rebut + ' ...',
            '': '',
        }

        for r in results:
            self.assertEqual(results[r], tg.get_text_for_add_premise_container('en', self.confrontation, self.premise,
                                                                               r, self.conclusion, is_supportive))

    def test_get_text_for_add_premise_container_on_attack(self):
        _t = Translator('en')

        is_supportive = False

        undermine = _t.get(_.itIsFalseThat) + ' ' + self.premise
        support = _t.get(_.itIsTrueThat) if is_supportive else _t.get(_.itIsFalseThat)
        support += ' ' + self.conclusion + ' '
        support += _t.get(_.hold) if is_supportive else _t.get(_.doesNotHold)
        undercut = self.confrontation + ', ' + _t.get(_.butIDoNotBelieveCounterFor).format(self.conclusion)
        rebut = self.confrontation + ' '
        rebut += _t.get(_.iAcceptCounterThat) if is_supportive else _t.get(_.iAcceptArgumentThat)
        rebut += ' ' + self.conclusion

        results = {
            'undermine': undermine + ' ...',
            'support': support + ' ...',
            'undercut': undercut + ' ...',
            'rebut': rebut + ' ...',
            '': '',
        }

        for r in results:
            self.assertEqual(results[r], tg.get_text_for_add_premise_container('en', self.confrontation, self.premise,
                                                                               r, self.conclusion, is_supportive))

    def test_get_header_for_users_confrontation_response(self):
        arg = DBDiscussionSession.query(Argument).get(2)

        is_supportive = True
        redirect_from_jump = False
        results = {
            'undermine': 'that {}Some premise text{}',
            'support': '{}it is true that Some conclusion text hold{}.',
            'undercut': 'right, Some premise text. {}But I do not believe that this is a argument for Some conclusion text{}',
            'rebut': '{}right, Some premise text, and I do accept that this is a counter-argument for Some conclusion text. However, I have a much stronger argument for reject that Some conclusion text.{}',
            '':  ''
        }
        for r in results:
            user_msg, system_msg = tg.get_header_for_users_confrontation_response(arg, 'en', self.premise, r,
                                                                                  self.conclusion, True, is_supportive,
                                                                                  False, redirect_from_jump)
            self.assertEqual(user_msg, results[r])
            self.assertEqual(system_msg, '')

        is_supportive = False
        results.update({
            'support': '{}it is false that Some conclusion text does not hold{}.',
            'rebut': '{}right, Some premise text, and I do accept that this is an argument for Some conclusion text. However, I have a much stronger argument for accept that Some conclusion text.{}',
        })
        for r in results:
            user_msg, system_msg = tg.get_header_for_users_confrontation_response(arg, 'en', self.premise, r,
                                                                                  self.conclusion, True, is_supportive,
                                                                                  False, redirect_from_jump)
            self.assertEqual(user_msg, results[r])
            self.assertEqual(system_msg, '')

        redirect_from_jump = True
        results.update({
            'undercut': 'Maybe it is true that Some premise text. {}But I do not believe that this is a argument for Some conclusion text{}',
            'rebut': '{}Maybe it is true that Some premise text, and I do accept that this is an argument for Some conclusion text. However, I have a much stronger argument for accept that Some conclusion text.{}',
        })
        for r in results:
            user_msg, system_msg = tg.get_header_for_users_confrontation_response(arg, 'en', self.premise, r,
                                                                                  self.conclusion, True, is_supportive,
                                                                                  False, redirect_from_jump)
            self.assertEqual(user_msg, results[r])
            self.assertEqual(system_msg, '')

        is_supportive = True
        results.update({
            'support': '{}it is true that Some conclusion text hold{}.',
            'rebut': '{}Maybe it is true that Some premise text, and I do accept that this is a counter-argument for Some conclusion text. However, I have a much stronger argument for reject that Some conclusion text.{}',
        })
        for r in results:
            user_msg, system_msg = tg.get_header_for_users_confrontation_response(arg, 'en', self.premise, r,
                                                                                  self.conclusion, True, is_supportive,
                                                                                  False, redirect_from_jump)
            self.assertEqual(user_msg, results[r])
            self.assertEqual(system_msg, '')

    def test_get_relation_text_dict_without_substitution(self):
        with_no_opinion_text = False
        is_dont_know = False
        res = tg.get_relation_text_dict_without_substitution('en', with_no_opinion_text, self.premise, self.conclusion, is_dont_know)

        results = {
            'undermine_text': 'In my opinion, <span data-argumentation-type="attack">Some premise text</span> is wrong and I would like to argue against it.',
            'support_text': 'In my opinion, <span data-argumentation-type="attack">Some premise text</span> is correct and it convinced me.',
            'undercut_text': 'In my opinion, <span data-argumentation-type="attack">Some premise text</span> is correct, but it does not support <span data-argumentation-type="argument">Some conclusion text</span>.',
            'rebut_text': 'In my opinion, <span data-argumentation-type="attack">Some premise text</span> is correct and it supports <span data-argumentation-type="argument">Some conclusion text</span>. However I want to defend <span data-argumentation-type="position">my point of view</span>.'
        }

        self.assertEqual(len(res), 4)
        self.assertTrue({k: self.assertEqual(res[k], v) for k, v in results.items()})

        with_no_opinion_text = True
        res = tg.get_relation_text_dict_without_substitution('en', with_no_opinion_text, self.premise, self.conclusion, is_dont_know)
        self.assertEqual(len(res), 6)
        results.update({
            'step_back_text': 'Go one step back. (The system has no other counter-argument)',
            'no_opinion_text': 'Show me another argument.'
        })
        self.assertTrue({k: self.assertEqual(res[k], v) for k, v in results.items()})

        is_dont_know = True
        res = tg.get_relation_text_dict_without_substitution('en', with_no_opinion_text, self.premise, self.conclusion, is_dont_know)
        self.assertEqual(len(res), 6)
        results.update({
            'undercut_text': 'In my opinion, <span data-argumentation-type="attack">Some premise text</span> is correct, but it is not supported by the <span data-argumentation-type="argument">reason</span>.',
            'rebut_text': 'In my opinion, <span data-argumentation-type="argument">Some conclusion text</span> is wrong and I would like to argue against it.'
        })
        self.assertTrue({k: self.assertEqual(res[k], v) for k, v in results.items()})

    def test_get_relation_text_dict_with_substitution(self):
        with_no_opinion_text = False
        is_dont_know = False
        attack_type = ''
        gender = 'f'

        res = tg.get_relation_text_dict_with_substitution('en', with_no_opinion_text, is_dont_know, attack_type, gender)
        results = {
            'undermine_text': 'In my opinion, <span data-argumentation-type="attack">her statement</span> is wrong and I would like to argue against it.',
            'support_text': 'In my opinion, <span data-argumentation-type="attack">her statement</span> is correct and it convinced me.',
            'undercut_text': 'In my opinion, <span data-argumentation-type="attack">her statement</span> is correct, but it does not support <span data-argumentation-type="argument">my argument</span>.',
            'rebut_text': 'In my opinion, <span data-argumentation-type="attack">her statement</span> is correct and it supports <span data-argumentation-type="argument">my argument</span>. However I want to defend <span data-argumentation-type="position">my point of view</span>.'
        }
        self.assertEqual(len(res), 4)
        self.assertTrue({k: self.assertEqual(res[k], v) for k, v in results.items()})

        with_no_opinion_text = True
        res = tg.get_relation_text_dict_with_substitution('en', with_no_opinion_text, is_dont_know, attack_type, gender)
        self.assertEqual(len(res), 6)
        results.update({
            'step_back_text': 'Go one step back. (The system has no other counter-argument)',
            'no_opinion_text': 'Show me another argument.'
        })
        self.assertTrue({k: self.assertEqual(res[k], v) for k, v in results.items()})

        is_dont_know = True
        res = tg.get_relation_text_dict_with_substitution('en', with_no_opinion_text, is_dont_know, attack_type, gender)
        self.assertEqual(len(res), 6)
        results.update({
            'undermine_text': 'In my opinion, <span data-argumentation-type="attack">her statement</span> is wrong and I would like to argue against it.',
            'support_text': 'In my opinion, <span data-argumentation-type="attack">her statement</span> is correct and it convinced me.',
            'undercut_text': 'In my opinion, <span data-argumentation-type="attack">her statement</span> is correct, but it is not supported by the <span data-argumentation-type="argument">reason</span>.', 'rebut_text': 'In my opinion, <span data-argumentation-type="argument">her opinion</span> is wrong and I would like to argue against it.'
        })
        self.assertTrue({k: self.assertEqual(res[k], v) for k, v in results.items()})

        attack_type = 'undercut'
        res = tg.get_relation_text_dict_with_substitution('en', with_no_opinion_text, is_dont_know, attack_type, gender)
        self.assertEqual(len(res), 6)
        self.assertTrue({k: self.assertEqual(res[k], v) for k, v in results.items()})

        attack_type = 'undermine'
        res = tg.get_relation_text_dict_with_substitution('en', with_no_opinion_text, is_dont_know, attack_type, gender)
        self.assertEqual(len(res), 6)
        self.assertTrue({k: self.assertEqual(res[k], v) for k, v in results.items()})

        attack_type = 'rebut'
        res = tg.get_relation_text_dict_with_substitution('en', with_no_opinion_text, is_dont_know, attack_type, gender)
        self.assertEqual(len(res), 6)
        self.assertTrue({k: self.assertEqual(res[k], v) for k, v in results.items()})

        is_dont_know = False
        attack_type = 'undercut'
        res = tg.get_relation_text_dict_with_substitution('en', with_no_opinion_text, is_dont_know, attack_type, gender)
        self.assertEqual(len(res), 6)
        results.update({
            'undercut_text': 'In my opinion, <span data-argumentation-type="attack">her statement</span> is correct, but it does not support <span data-argumentation-type="argument">my argument</span>.',
            'rebut_text': 'In my opinion, <span data-argumentation-type="attack">her statement</span> is correct and it supports <span data-argumentation-type="argument">my argument</span>. However I want to defend <span data-argumentation-type="position">my point of view</span>.'
        })
        self.assertTrue({k: self.assertEqual(res[k], v) for k, v in results.items()})

        attack_type = 'undermine'
        res = tg.get_relation_text_dict_with_substitution('en', with_no_opinion_text, is_dont_know, attack_type, gender)
        self.assertEqual(len(res), 6)
        results.update({
            'undercut_text': 'In my opinion, <span data-argumentation-type="attack">her statement</span> is correct, but it does not support <span data-argumentation-type="argument">her point of view</span>.',
            'rebut_text': 'In my opinion, <span data-argumentation-type="attack">her statement</span> is correct and it supports <span data-argumentation-type="argument">her point of view</span>. However I want to defend <span data-argumentation-type="position">my point of view</span>.',
        })
        self.assertTrue({k: self.assertEqual(res[k], v) for k, v in results.items()})

        attack_type = 'rebut'
        res = tg.get_relation_text_dict_with_substitution('en', with_no_opinion_text, is_dont_know, attack_type, gender)
        self.assertTrue({k: self.assertEqual(res[k], v) for k, v in results.items()})

    def test_get_jump_to_argument_text_list(self):
        res = tg.get_jump_to_argument_text_list('en')
        self.assertEqual(len(res), 5)
        self.assertEqual(res[0], 'Right, I support the <span data-argumentation-type="argument">assertion</span> and accept the <span data-argumentation-type="attack">reason</span>.')
        self.assertEqual(res[1], 'Right, I support the <span data-argumentation-type="argument">assertion</span>, but I want to add my own <span data-argumentation-type="attack">reason</span>.')
        self.assertEqual(res[2], 'Right, I support the <span data-argumentation-type="argument">assertion</span>, but the <span data-argumentation-type="attack">reason</span> does not support it.')
        self.assertEqual(res[3], 'Wrong, the <span data-argumentation-type="argument">assertion</span> is false.')
        self.assertEqual(res[4], 'Wrong, the <span data-argumentation-type="attack">reason</span> does not hold.')

    def test_get_support_to_argument_text_list(self):
        res = tg.get_support_to_argument_text_list('en')
        self.assertEqual(len(res), 4)
        print(res)
        self.assertEqual(res[0], 'I accept the <span data-argumentation-type="attack">reason</span>.')
        self.assertEqual(res[1], 'The <span data-argumentation-type="attack">reason</span> does not hold.')
        self.assertEqual(res[2], 'I want to add a new <span data-argumentation-type="attack">reason</span>.')
        self.assertEqual(res[3], 'The <span data-argumentation-type="attack">reason</span> does not support the <span data-argumentation-type="argument">assertion</span>.')

    def test_get_text_for_support(self):
        arg = DBDiscussionSession.query(Argument).get(2)
        argument_text = 'some argument text'
        _t = Translator('en')

        res = tg.get_text_for_support(arg, argument_text, 'Tobias', 'main_page', _t)
        self.assertEqual(res, '<span>This is a good point and other participants are interested in your conclusion too. They say, that</span> some argument text.<br><br>What do you think about that?')

    def test_get_name_link_of_arguments_author(self):
        db_arg = DBDiscussionSession.query(Argument).get(2)
        db_user = DBDiscussionSession.query(User).get(db_arg.author_uid)

        with_link = True
        user, text, gender, okay = tg.get_name_link_of_arguments_author('main_page', db_arg, 'Christian', with_link)
        self.assertEqual(user, None)
        self.assertEqual(text, '')
        self.assertEqual(gender, 'n')
        self.assertEqual(okay, False)

        user, text, gender, okay = tg.get_name_link_of_arguments_author('main_page', db_arg, db_user.nickname, with_link)
        self.assertEqual(user, None)
        self.assertEqual(text, '')
        self.assertEqual(gender, 'n')
        self.assertEqual(okay, False)

        with_link = False
        user, text, gender, okay = tg.get_name_link_of_arguments_author('main_page', db_arg, 'Tobias', with_link)
        self.assertEqual(user, None)
        self.assertEqual(text, '')
        self.assertEqual(gender, 'n')
        self.assertEqual(okay, False)

    def test_get_author_or_first_supporter_of_element(self):
        arg, user1, user2 = 1, 2, 3

        self.assertIsNone(tg.get_author_or_first_supporter_of_element(arg, user1, True))

        DBDiscussionSession.add(MarkedArgument(argument=arg, user=user1))
        transaction.commit()
        self.assertIsNone(tg.get_author_or_first_supporter_of_element(arg, user1, True))
        self.assertIsNotNone(tg.get_author_or_first_supporter_of_element(arg, user2, True))

        DBDiscussionSession.add(MarkedArgument(argument=arg, user=user2))
        transaction.commit()
        self.assertIsNotNone(tg.get_author_or_first_supporter_of_element(arg, user1, True))
        self.assertIsNotNone(tg.get_author_or_first_supporter_of_element(arg, user2, True))

        DBDiscussionSession.query(MarkedArgument).filter_by(argument_uid=arg, author_uid=user1).delete()
        DBDiscussionSession.query(MarkedArgument).filter_by(argument_uid=arg, author_uid=user2).delete()
        transaction.commit()

        self.assertIsNone(tg.get_author_or_first_supporter_of_element(arg, user1, True))
        self.assertIsNone(tg.get_author_or_first_supporter_of_element(arg, user2, True))

    def test_get_text_for_edit_text_message(self):
        text = tg.get_text_for_edit_text_message('en', 'Tobias', 'oem', 'edit', 'some_url', True)
        self.assertEqual(text, 'Your original statement was edited by Tobias<br>From: oem<br>To: edit<br>Where: <a href="some_url">some_url</a>')

        text = tg.get_text_for_edit_text_message('en', 'Tobias', 'oem', 'edit', 'some_url', False)
        self.assertEqual(text, '''Your original statement was edited by Tobias\nFrom: oem\nTo: edit\nWhere: some_url''')

    def test_get_text_for_add_text_message(self):
        text = tg.get_text_for_add_text_message('Tobias', 'en', 'some_url', True)
        self.assertEqual(text, 'Hey, someone has added his/her opinion regarding your argument!<br>Where: <a href="some_url">some_url</a>')

        text = tg.get_text_for_add_text_message('Tobias', 'en', 'some_url', False)
        self.assertEqual(text, '''Hey, someone has added his/her opinion regarding your argument!\nWhere: some_url''')

    def test_get_text_for_add_argument_message(self):
        text = tg.get_text_for_add_argument_message('Tobias', 'en', 'some_url', True)
        self.assertEqual(text, 'Hey, someone has added his/her argument regarding your argument!<br>Where: <a href="some_url">some_url</a>')

        text = tg.get_text_for_add_argument_message('Tobias', 'en', 'some_url', False)
        self.assertEqual(text, '''Hey, someone has added his/her argument regarding your argument!\nWhere: some_url''')

    def test_get_text_for_confrontation_without_attack(self):
        user_arg = DBDiscussionSession.query(Argument).get(8)
        sys_arg = DBDiscussionSession.query(Argument).get(10)

        attack = ''
        color_html, supportive, reply_for_argument, user_is_attacking = False, False, False, False
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, '')

    def test_get_text_for_confrontation_with_undermine(self):
        user_arg = DBDiscussionSession.query(Argument).get(8)
        sys_arg = DBDiscussionSession.query(Argument).get(10)
        attack = 'undermine'

        color_html, supportive, reply_for_argument, user_is_attacking = False, False, False, False
        text = '<span class="triangle-content-text">Other participants think that</span> <span>some premise text</span><span data-attitude="con"><span> does not hold</span><span>, because</span> <span>some confrontation text</span><span>.<br><br>What do you think about that?</span>'
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, False, False, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, False, True, False
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, False, True, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, True, False, False
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, True, False, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, True, True, False
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, True, True, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, False, False, False
        text = '<span class="triangle-content-text">Other participants think that</span> <span data-argumentation-type="argument">some premise text</span><span data-attitude="con"><span> <span data-argumentation-type="argument">does not hold</span></span></span><span>, because</span> <span data-argumentation-type="attack">some confrontation text</span><span>.<br><br>What do you think about that?</span>'
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, False, False, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, False, True, False
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, False, True, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, True, False, False
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, True, False, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, True, True, False
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, True, True, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

    def test_get_text_for_confrontation_with_undercut(self):
        user_arg = DBDiscussionSession.query(Argument).get(8)
        sys_arg = DBDiscussionSession.query(Argument).get(10)
        attack = 'undercut'

        color_html, supportive, reply_for_argument, user_is_attacking = False, False, False, False
        text = '<span class="triangle-content-text">Other participants do not have any opinion regarding some premise text. But they do <span data-attitude="con">not</span> believe that this is <span data-attitude="con">a good counter-argument for</span></span> some conclusion text<span>. Other participants think that </span>some confrontation text<span>.<br><br>What do you think about that?</span>'
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, False, False, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, False, True, False
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, False, True, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, True, False, False
        text = '<span class="triangle-content-text">Other participants do not have any opinion regarding some premise text. But they do <span data-attitude="con">not</span> believe that this is <span data-attitude="con">a good argument for</span></span> some conclusion text<span>. Other participants think that </span>some confrontation text<span>.<br><br>What do you think about that?</span>'
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, True, False, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, True, True, False
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, True, True, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, False, False, False
        text = '<span class="triangle-content-text">Other participants do not have any opinion regarding some premise text. But they do <span data-attitude="con">not</span> believe that this is <span data-attitude="con">a good counter-argument for</span></span> <span data-argumentation-type="argument">some conclusion text</span><span>. Other participants think that </span><span data-argumentation-type="attack">some confrontation text</span><span>.<br><br>What do you think about that?</span>'
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, False, False, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, False, True, False
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, False, True, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, True, False, False
        text = '<span class="triangle-content-text">Other participants do not have any opinion regarding some premise text. But they do <span data-attitude="con">not</span> believe that this is <span data-attitude="con">a good argument for</span></span> <span data-argumentation-type="argument">some conclusion text</span><span>. Other participants think that </span><span data-argumentation-type="attack">some confrontation text</span><span>.<br><br>What do you think about that?</span>'
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, True, False, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, True, True, False
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, True, True, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, '')
        self.assertEqual(sys_text, text)

    def test_get_text_for_confrontation_with_rebut(self):
        user_arg = DBDiscussionSession.query(Argument).get(8)
        sys_arg = DBDiscussionSession.query(Argument).get(10)
        attack = 'rebut'

        color_html, supportive, reply_for_argument, user_is_attacking = False, False, False, False
        text = '<span class="triangle-content-text">Other participants do not have any opinion regarding some premise text. But they claim to have a stronger <span data-attitude="con">statement for rejecting </span> some conclusion text. <span>They say: </span>some confrontation text<span>.<br><br>What do you think about that?</span>'
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, 'n')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, True, False, False
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, 'n')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, False, False, True
        text = '<span class="triangle-content-text">Other participants do not have any opinion regarding some premise text. But they claim to have a stronger <span data-attitude="pro">statement for accepting </span> some conclusion text. <span>They say: </span>some confrontation text<span>.<br><br>What do you think about that?</span>'
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, 'n')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, True, False, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, 'n')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, False, True, False
        text = '<span class="triangle-content-text"><span>Other participants claim to have a stronger statement to reject </span> some conclusion text. <span>They say: </span>some confrontation text<span>.<br><br>What do you think about that?</span>'
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, 'n')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, False, True, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, 'n')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, True, True, False
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, 'n')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = False, True, True, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, 'n')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, False, False, False
        text = '<span class="triangle-content-text">Other participants do not have any opinion regarding some premise text. But they claim to have a stronger <span data-attitude="con">statement for <span data-argumentation-type="argument">rejecting</span> </span> <span data-argumentation-type="argument">some conclusion text</span>. <span>They say: </span><span data-argumentation-type="attack">some confrontation text</span><span>.<br><br>What do you think about that?</span>'
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, 'n')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, True, False, False
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, 'n')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, True, False, True
        text = '<span class="triangle-content-text">Other participants do not have any opinion regarding some premise text. But they claim to have a stronger <span data-attitude="pro">statement for <span data-argumentation-type="argument">accepting</span> </span> <span data-argumentation-type="argument">some conclusion text</span>. <span>They say: </span><span data-argumentation-type="attack">some confrontation text</span><span>.<br><br>What do you think about that?</span>'
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, 'n')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, False, False, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, 'n')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, False, True, False
        text = '<span class="triangle-content-text"><span>Other participants claim to have a stronger statement to <span data-argumentation-type="argument">reject </span></span> <span data-argumentation-type="argument">some conclusion text</span>. <span>They say: </span><span data-argumentation-type="attack">some confrontation text</span><span>.<br><br>What do you think about that?</span>'
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, 'n')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, False, True, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, 'n')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, True, True, False
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, 'n')
        self.assertEqual(sys_text, text)

        color_html, supportive, reply_for_argument, user_is_attacking = True, True, True, True
        sys_text, gender = tg.get_text_for_confrontation('main_page', 'en', 'Tobias', self.premise, self.conclusion,
                                                         'another conlcusion', supportive, attack, self.confrontation,
                                                         reply_for_argument, user_is_attacking, user_arg, sys_arg,
                                                         color_html)
        self.assertEqual(gender, 'n')
        self.assertEqual(sys_text, text)