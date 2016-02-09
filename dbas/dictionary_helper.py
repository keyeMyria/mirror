import random
import json
import datetime
import locale
import collections

from sqlalchemy import and_
from slugify import slugify

from .database import DBDiscussionSession
from .database.discussion_model import Argument, Statement, User, TextVersion, Premise, PremiseGroup, History, Issue
from .logger import logger
from .recommender_system import RecommenderHelper
from .query_helper import QueryHelper
from .strings import Translator, TextGenerator
from .url_manager import UrlManager
from .user_management import UserHandler

# @author Tobias Krauthoff
# @email krauthoff@cs.uni-duesseldorf.de
# @copyright Krauthoff 2015

class DictionaryHelper(object):

	def get_random_subdict_out_of_orderer_dict(self, ordered_dict, count):
		"""
		Creates a random subdictionary with given count out of the given ordered_dict.
		With a count of <2 the dictionary itself will be returned.
		:param ordered_dict: dictionary for the function
		:param count: count of entries for the new dictionary
		:return: dictionary
		"""
		return_dict = dict()
		logger('DictionaryHelper', 'get_subdictionary_out_of_orderer_dict', 'count: ' + str(count))
		items = list(ordered_dict.items())
		for item in items:
			logger('DictionaryHelper', 'get_subdictionary_out_of_orderer_dict', 'all items: ' + ''.join(str(item)))
		if count < 0:
			return ordered_dict
		elif count == 1:
			if len(items) > 1:
				rnd = random.randint(0, len(items)-1)
				logger('DictionaryHelper', 'get_subdictionary_out_of_orderer_dict', 'return item at ' + str(rnd))
				return_dict[items[rnd][0]] = items[rnd][1]
			else:
				return ordered_dict
		else:

			for i in range(0, count):
				rnd = random.randint(0, len(items)-1)
				logger('DictionaryHelper', 'get_subdictionary_out_of_orderer_dict', 'for loop ' + str(i) + '. add element at ' + str(rnd))
				return_dict[items[rnd][0]] = items[rnd][1]
				items.pop(rnd)

		return return_dict

	def dictionary_to_json_array(self, raw_dict, ensure_ascii):
		"""
		Dumps given dictionary into json
		:param raw_dict: dictionary for dumping
		:param ensure_ascii: if true, ascii will be checked
		:return: json data
		"""
		return_dict = json.dumps(raw_dict, ensure_ascii)
		return return_dict

	def save_statement_row_in_dictionary(self, statement_row):
		"""
		Saved a row in dictionary
		:param statement_row: for saving
		:param issue:
		:return: dictionary
		"""
		logger('DictionaryHelper', 'save_statement_row_in_dictionary', 'statement uid ' + str(statement_row.uid))
		db_statement = DBDiscussionSession.query(Statement).filter(and_(Statement.uid == statement_row.uid,
		                                                                Statement.issue_uid == issue)).first()
		db_premise = DBDiscussionSession.query(Premise).filter(and_(Premise.statement_uid == db_statement.uid,
		                                                            Premise.issue_uid == issue)).first()
		logger('DictionaryHelper', 'save_statement_row_in_dictionary', 'premise uid ' +
			       ((str(db_premise.premisesgroup_uid) + '.' + str(db_premise.statement_uid)) if db_premise else 'null'))
		db_textversion = DBDiscussionSession.query(TextVersion).filter_by(uid=db_statement.textversion_uid).join(User).first()

		uid    = str(db_statement.uid)
		text   = db_textversion.content
		date   = str(db_textversion.timestamp)
		author = db_textversion.users.nickname
		pgroup = str(db_premise.premisesgroup_uid) if db_premise else '0'

		while text.endswith('.'):
			text = text[:-1]

		logger('DictionaryHelper', 'save_statement_row_in_dictionary', uid + ', ' + text + ', ' + date + ', ' + author +
		       ', ' + pgroup)
		return {'uid':uid, 'text':text, 'date':date, 'author':author, 'premisegroup_uid':pgroup}

	def prepare_discussion_dict(self, uid, lang, at_start=False, at_attitude=False, at_justify=False,
	                            is_supportive=False, at_dont_know=False, at_argumentation=False,
	                            at_justify_argumentation=False, additional_id=0, attack='', logged_in=False):
		"""

		:param uid:
		:param lang:
		:param at_start:
		:param at_attitude:
		:param at_justify:
		:param is_supportive:
		:param at_dont_know:
		:param at_argumentation:
		:param at_justify_argumentation:
		:param additional_id:
		:param attack:
		:param logged_in:
		:return:
		"""
		_tn              = Translator(lang)
		_qh              = QueryHelper()
		heading          = ''
		add_premise_text = ''
		if at_start:
			logger('DictionaryHelper', 'prepare_discussion_dict', 'at_start')
			heading             = _tn.get(_tn.initialPositionInterest)

		elif at_attitude:
			logger('DictionaryHelper', 'prepare_discussion_dict', 'at_attitude')
			text                = _qh.get_text_for_statement_uid(uid)
			if not text:
				return None
			heading             = _tn.get(_tn.whatDoYouThinkAbout) + ' <strong>' + text[0:1].lower() + text[1:] + '</strong>?'

		elif at_justify:
			logger('DictionaryHelper', 'prepare_discussion_dict', 'at_justify')
			text                = _qh.get_text_for_statement_uid(uid)
			if not text:
				return None
			heading             = _tn.get(_tn.whyDoYouThinkThat) + ' <strong>' + text[0:1].lower() + text[1:] + '</strong> ' \
			                        + _tn.get(_tn.isTrue if is_supportive else _tn.isFalse) + '?<br><br>'
			because             = _tn.get(_tn.because)[0:1].upper() + _tn.get(_tn.because)[1:].lower() + '...'
			heading             += because
			add_premise_text    = text

		elif at_justify_argumentation:
			logger('DictionaryHelper', 'prepare_discussion_dict', 'at_justify_argumentation')
			_tg = TextGenerator(lang)
			db_argument         = DBDiscussionSession.query(Argument).filter_by(uid=uid).first()
			confrontation       = _qh.get_text_for_argument_uid(uid, lang, True)
			premise, tmp        = _qh.get_text_for_premisesgroup_uid(uid)
			conclusion          = _qh.get_text_for_statement_uid(db_argument.conclusion_uid) if db_argument.conclusion_uid != 0 \
									else _qh.get_text_for_argument_uid(db_argument.argument_uid, lang, True)
			heading             = _tg.get_header_for_confrontation_response(confrontation, premise, attack, conclusion, False, is_supportive, logged_in)
			add_premise_text    = _tg.get_text_for_add_premise_container(confrontation, premise, attack, conclusion,
			                                                             db_argument.is_supportive)
			because             = ' ' + _tn.get(_tn.because)[0:1].upper() + _tn.get(_tn.because)[1:].lower() + '...'
			heading             += because
		elif at_dont_know:
			logger('DictionaryHelper', 'prepare_discussion_dict', 'at_dont_know')
			text                = _qh.get_text_for_argument_uid(uid, lang)
			if text:
				heading         = _tn.get(_tn.otherParticipantsThinkThat) + ' <strong>' + text[0:1].lower() + text[1:] \
			                     + '</strong>. ' + '<br><br>' + _tn.get(_tn.whatDoYouThinkAboutThat) + '?'
			else:
				heading         = _tn.get(_tn.firstOneText) + ' <strong>' + _qh.get_text_for_statement_uid(additional_id) + '</strong>.'

		elif at_argumentation:
			logger('DictionaryHelper', 'prepare_discussion_dict', 'at_argumentation')
			_tg                 = TextGenerator(lang)
			db_argument         = DBDiscussionSession.query(Argument).filter_by(uid=uid).first()
			if attack == 'end':
				heading             = _tn.get(_tn.sentencesOpenersForArguments[0])\
				                      + ': <strong>' + _qh.get_text_for_argument_uid(uid, lang, True) + '</strong>.'\
				                      + '<br><br>' + _tn.get(_tn.otherParticipantsDontHaveCounterForThat)\
				                      + '.<br><br>' + _tn.get(_tn.discussionEnd) + ' ' + _tn.get(_tn.discussionEndLinkText)
			else:
				premise, tmp        = _qh.get_text_for_premisesgroup_uid(db_argument.premisesgroup_uid)
				conclusion          = _qh.get_text_for_statement_uid(db_argument.conclusion_uid) if db_argument.conclusion_uid != 0 \
										else _qh.get_text_for_argument_uid(db_argument.argument_uid, lang, True)
				db_confrontation    = DBDiscussionSession.query(Argument).filter_by(uid=additional_id).first()
				confrontation, tmp  = _qh.get_text_for_premisesgroup_uid(db_confrontation.premisesgroup_uid)
				# confrontation       = _qh.get_text_for_argument_uid(additional_id, lang)
				logger('DictionaryHelper', 'prepare_discussion_dict', 'additional_id ' + str(additional_id) + ', confrontation '
				       + str(confrontation) + ', attack ' + str(attack))

				reply_for_argument  = True
				current_argument    = _qh.get_text_for_argument_uid(uid, lang, True)
				user_is_attacking   = not db_argument.is_supportive
				heading             = _tg.get_text_for_confrontation(premise, conclusion, is_supportive, attack,
				                                                     confrontation, reply_for_argument, user_is_attacking,
			                                                         current_argument)

		return {'heading': heading, 'add_premise_text': add_premise_text}

	def prepare_item_dict_for_start(self, issue_uid, logged_in, lang, application_url, for_api):
		"""

		:param issue_uid:
		:param logged_in:
		:param lang:
		:param application_url:
		:param for_api:
		:return:
		"""
		db_statements = DBDiscussionSession.query(Statement)\
			.filter(and_(Statement.is_startpoint == True, Statement.issue_uid == issue_uid))\
			.join(TextVersion, TextVersion.uid == Statement.textversion_uid).all()
		slug = DBDiscussionSession.query(Issue).filter_by(uid=issue_uid).first().get_slug()

		statements_array = []
		_um = UrlManager(application_url, slug, for_api)
		_qh = QueryHelper()

		if db_statements:
			for statement in db_statements:
				statements_array.append(_qh.get_statement_dict(statement.uid,
				                                                _qh.get_text_for_statement_uid(statement.uid),
				                                                [{'title': _qh.get_text_for_statement_uid(statement.uid), 'id': statement.uid}],
				                                                '',
				                                                _um.get_url_for_statement_attitude(True, statement.uid)))

			if logged_in:
				_tn = Translator(lang)
				statements_array.append(_qh.get_statement_dict('start_statement',
				                                                _tn.get(_tn.newConclusionRadioButtonText),
				                                                [{'title': _tn.get(_tn.newConclusionRadioButtonText), 'id': 0}],
				                                                'null',
				                                                'null'))

		return statements_array

	def prepare_item_dict_for_attitude(self, statement_uid, issue_uid, lang, application_url, for_api):
		"""

		:param statement_uid:
		:param issue_uid:
		:param url:
		:param lang:
		:return:
		"""
		_qh = QueryHelper()
		_tn = Translator(lang)

		slug = DBDiscussionSession.query(Issue).filter_by(uid=issue_uid).first().get_slug()
		text = _qh.get_text_for_statement_uid(statement_uid)
		statements_array = []

		_um = UrlManager(application_url, slug, for_api)

		statements_array.append(_qh.get_statement_dict('agree',
		                                                _tn.get(_tn.iAgreeWithInColor) + ': ' + text,
		                                                [{'title': _tn.get(_tn.iAgreeWithInColor) + ': ' + text, 'id': 'agree'}],
		                                                'agree', _um.get_url_for_justifying_statement(True, statement_uid, 't')))
		statements_array.append(_qh.get_statement_dict('disagree',
		                                                _tn.get(_tn.iDisagreeWithInColor) + ': ' + text,
		                                                [{'title': _tn.get(_tn.iDisagreeWithInColor) + ': ' + text, 'id': 'disagree'}],
		                                                'disagree', _um.get_url_for_justifying_statement(True, statement_uid, 'f')))
		statements_array.append(_qh.get_statement_dict('dontknow',
		                                                _tn.get(_tn.iHaveNoOpinionYetInColor) + ': ' + text,
		                                                [{'title': _tn.get(_tn.iHaveNoOpinionYetInColor) + ': ' + text, 'id': 'dontknow'}],
		                                                'dontknow', _um.get_url_for_justifying_statement(True, statement_uid, 'd')))

		return statements_array

	def prepare_item_dict_for_justify_statement(self, statement_uid, issue_uid, is_supportive, lang, application_url, for_api):
		"""

		:param statement_uid:
		:param issue_uid:
		:param is_supportive:
		:param lang:
		:return:
		"""
		statements_array = []
		_tn = Translator(lang)
		_qh = QueryHelper()
		slug = DBDiscussionSession.query(Issue).filter_by(uid=issue_uid).first().get_slug()
		db_arguments = DBDiscussionSession.query(Argument).filter(and_(Argument.is_supportive == is_supportive,
                                                                       Argument.conclusion_uid == statement_uid)).all()

		_um = UrlManager(application_url, slug, for_api)

		if db_arguments:
			for argument in db_arguments:
				# get all premises in the premisegroup of this argument
				db_premises = DBDiscussionSession.query(Premise).filter_by(premisesgroup_uid=argument.premisesgroup_uid).all()
				premise_array = []
				for premise in db_premises:
					text = _qh.get_text_for_statement_uid(premise.statement_uid)
					premise_array.append({'title': text, 'id': premise.statement_uid})

				text, uid = _qh.get_text_for_premisesgroup_uid(argument.premisesgroup_uid)

				# get attack for each premise, so the urls will be unique
				arg_id_sys, attack = RecommenderHelper().get_attack_for_argument(argument.uid, issue_uid)
				statements_array.append(_qh.get_statement_dict(str(argument.uid),
				                                                text,
				                                                premise_array, 'justify',
				                                                _um.get_url_for_reaction_on_argument(True, argument.uid, attack, arg_id_sys)))

			statements_array.append(_qh.get_statement_dict('start_premise',
			                                                _tn.get(_tn.newPremiseRadioButtonText),
			                                                [{'title': _tn.get(_tn.newPremiseRadioButtonText), 'id':0}],
			                                                'null',
			                                                'null'))

		return statements_array

	def prepare_item_dict_for_justify_argument(self, argument_uid, attack_type, issue_uid, is_supportive, lang, application_url, for_api):
		"""

		:param argument_uid:
		:param attack_type:
		:param issue_uid:
		:param lang:
		:return:
		"""
		statements_array = []
		_tn = Translator(lang)
		_qh = QueryHelper()
		slug = DBDiscussionSession.query(Issue).filter_by(uid=issue_uid).first().get_slug()
		db_argument = DBDiscussionSession.query(Argument).filter_by(uid=argument_uid).first()

		db_arguments = []
		if attack_type == 'undermine':
			db_premisses = DBDiscussionSession.query(Premise).filter_by(premisesgroup_uid=db_argument.premisesgroup_uid).all()
			for premise in db_premisses:
				arguments = DBDiscussionSession.query(Argument).filter(and_(Argument.conclusion_uid == premise.statement_uid, Argument.is_supportive == False)).all()
				db_arguments = db_arguments + arguments

		elif attack_type == 'undercut':
			db_arguments = DBDiscussionSession.query(Argument).filter(and_(Argument.argument_uid == argument_uid, Argument.is_supportive == False)).all()

		elif attack_type == 'overbid':
			db_arguments = DBDiscussionSession.query(Argument).filter(and_(Argument.argument_uid == argument_uid, Argument.is_supportive == True)).all()

		elif attack_type == 'rebut':
			db_arguments = DBDiscussionSession.query(Argument).filter(and_(Argument.conclusion_uid == db_argument.conclusion_uid,
                                                                           Argument.argument_uid == db_argument.argument_uid,
                                                                           Argument.is_supportive == (not db_argument.is_supportive))).all()

		_um = UrlManager(application_url, slug, for_api)

		if db_arguments:
			for argument in db_arguments:
				text, tmp = _qh.get_text_for_premisesgroup_uid(argument.premisesgroup_uid)

				# get alles premises in this group
				db_premises = DBDiscussionSession.query(Premise).filter_by(premisesgroup_uid=argument.premisesgroup_uid).all()
				premises_array = []
				for premise in db_premises:
					premise_dict = dict()
					premise_dict['id'] = premise.statement_uid
					premise_dict['title'] = _qh.get_text_for_statement_uid(premise.statement_uid)
					premises_array.append(premise_dict)

				# for each justifying premise, we need a new confrontation:
				arg_id_sys, attack = RecommenderHelper().get_attack_for_argument(argument_uid, issue_uid)

				statements_array.append(_qh.get_statement_dict(argument.uid,
				                                                text,
				                                                premises_array,
				                                                'justify',
				                                                _um.get_url_for_reaction_on_argument(True, argument.uid, attack, arg_id_sys)))

			statements_array.append(_qh.get_statement_dict('justify_premise',
			                                                _tn.get(_tn.newPremiseRadioButtonText),
			                                                [{'id': '0', 'title': _tn.get(_tn.newPremiseRadioButtonText)}],
			                                                'null',
			                                                'null'))


		return statements_array

	def prepare_item_dict_for_reaction(self, argument_uid, is_supportive, issue_uid, lang, application_url, for_api):
		"""

		:param argument_uid:
		:param is_supportive:
		:param issue_uid:
		:param lang:
		:return:
		"""
		_tg  = TextGenerator(lang)
		_qh = QueryHelper()
		slug = DBDiscussionSession.query(Issue).filter_by(uid=issue_uid).first().get_slug()

		db_argument = DBDiscussionSession.query(Argument).filter_by(uid=argument_uid).first()
		statements_array = []

		if db_argument:
			if db_argument.argument_uid == 0:
				conclusion = _qh.get_text_for_statement_uid(db_argument.conclusion_uid)
			else:
				conclusion = _qh.get_text_for_argument_uid(db_argument.argument_uid, lang)

			premise, tmp     = _qh.get_text_for_premisesgroup_uid(db_argument.premisesgroup_uid)
			conclusion       = conclusion[0:1].lower() + conclusion[1:]
			premise          = premise[0:1].lower() + premise[1:]

			ret_dict         = _tg.get_relation_text_dict_without_confrontation(premise, conclusion, False, True, not db_argument.is_supportive)
			mode             = 't' if is_supportive else 't'
			_um              = UrlManager(application_url, slug, for_api)

			types = ['undermine', 'support', 'undercut', 'overbid', 'rebut', 'no_opinion']
			for t in types:
				# special case, when the user selectes the support, because this does not need to be justified!
				if t == 'support':
					arg_id_sys, attack = RecommenderHelper().get_attack_for_argument(argument_uid, issue_uid)
					url = _um.get_url_for_reaction_on_argument(True, argument_uid, attack, arg_id_sys)
				else:
					url = _um.get_url_for_justifying_argument(True, argument_uid, mode, t) if t != 'no_opinion' else 'window.history.go(-1)'
				statements_array.append(_qh.get_statement_dict(t, ret_dict[t + '_text'], [{'title': ret_dict[t + '_text'], 'id':t}], t, url))

		return statements_array

	def prepare_extras_dict(self, current_slug, is_editable, is_reportable, show_bar_icon, show_display_styles, lang,
	                        authenticated_userid, add_premise_supportive=False, argument_id=0, breadcrumbs='',
	                        application_url='', for_api=False):
		"""

		:param current_slug:
		:param is_editable:
		:param is_reportable:
		:param show_bar_icon:
		:param show_display_styles:
		:param lang:
		:param authenticated_userid:
		:param add_premise_supportive:
		:param argument_id:
		:param breadcrumbs:
		:return:
		"""
		_uh = UserHandler()
		_tn = Translator(lang)
		_qh = QueryHelper()
		is_logged_in = _uh.is_user_logged_in(authenticated_userid)

		return_dict = dict()
		return_dict['restart_url']                   = UrlManager(application_url, current_slug, for_api).get_slug_url(True)
		return_dict['is_editable']                   = is_editable and is_logged_in
		return_dict['is_reportable']                 = is_reportable
		return_dict['is_admin']                      = _uh.is_user_admin(authenticated_userid)
		return_dict['logged_in']                     = is_logged_in
		return_dict['show_bar_icon']                 = show_bar_icon
		return_dict['show_display_style']            = show_display_styles
		return_dict['users_name']                    = str(authenticated_userid)
		return_dict['add_premise_supportive']        = add_premise_supportive
		return_dict['add_premise_container_style']   = 'display: none'
		return_dict['add_statement_container_style'] = 'display: none'
		return_dict['title']                         = {'barometer': _tn.get(_tn.opinionBarometer),
													 	 'guided_view': _tn.get(_tn.displayControlDialogGuidedBody),
													 	 'island_view': _tn.get(_tn.displayControlDialogIslandBody),
													 	 'expert_view': _tn.get(_tn.displayControlDialogExpertBody),
		                                                 'add_statement_row_title': _tn.get(_tn.addStatementRow),
		                                                 'rem_statement_row_title': _tn.get(_tn.remStatementRow),
		                                                 'save_my_statement': _tn.get(_tn.saveMyStatement),
		                                                 'previous':  _tn.get(_tn.previous),
		                                                 'next':  _tn.get(_tn.next),
		                                                }
		if not for_api:
			return_dict['breadcrumbs']               = breadcrumbs
		self.add_language_options_for_extra_dict(return_dict, lang)

		# add everything for the island view
		if show_display_styles:
			# does an argumente exists?
			db_argument = DBDiscussionSession.query(Argument).filter_by(uid=argument_id).first()
			if db_argument:
				island_dict = _qh.get_everything_for_island_view(argument_id, lang)
				island_dict['premise'] = island_dict['premise'][0:1].lower() + island_dict['premise'][1:]
				island_dict['conclusion'] = island_dict['conclusion'][0:1].lower() + island_dict['conclusion'][1:]
				island_dict.update(TextGenerator(lang).get_relation_text_dict_without_confrontation(island_dict['premise'],
				                                                                                    island_dict['conclusion'],
				                                                                                    False, False, not db_argument.is_supportive))
				return_dict['island'] = island_dict
			else:
				return_dict['is_editable']            =  False
				return_dict['is_reportable']          =  False
				return_dict['show_bar_icon']          =  False
				return_dict['show_display_style']     =  False
				return_dict['title']                  = {'barometer': _tn.get(_tn.opinionBarometer),
												        'guided_view': _tn.get(_tn.displayControlDialogGuidedBody),
												        'island_view': _tn.get(_tn.displayControlDialogIslandBody),
												        'expert_view': _tn.get(_tn.displayControlDialogExpertBody),
		                                                'edit_statement': _tn.get(_tn.editTitle),
		                                                'report_statement': _tn.get(_tn.reportTitle)}
		return return_dict

	def add_language_options_for_extra_dict(self, extras_dict, lang):
		"""

		:param extras_dict:
		:param lang:
		:return:
		"""
		lang_is_en = (lang != 'de')
		lang_is_de = (lang == 'de')
		_t = Translator(lang)
		extras_dict.update({
			'lang_is_de': lang_is_de,
			'lang_is_en': lang_is_en,
			'link_de_class': ('active' if lang_is_de else ''),
			'link_en_class': ('active' if lang_is_en else ''),
			'button':{
				'report' : _t.get(_t.report),
				'report_title': _t.get(_t.reportTitle),
				'acceptIt' : _t.get(_t.acceptIt),
				'showAllArguments' : _t.get(_t.showAllArguments),
				'showAllUsers' : _t.get(_t.showAllUsers),
				'deleteTrack' : _t.get(_t.deleteTrack),
				'requestTrack' : _t.get(_t.requestTrack),
				'deleteHistory' : _t.get(_t.deleteHistory),
				'requestHistory' : _t.get(_t.requestHistory),
				'passwordSubmit' : _t.get(_t.passwordSubmit),
				'contactSubmit' : _t.get(_t.contactSubmit),
				'letsGo' : _t.get(_t.letsGo),
				'opinionBarometer' : _t.get(_t.opinionBarometer),
				'edit_statement': _t.get(_t.editTitle)
			}
		})

	