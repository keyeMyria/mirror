"""
Provides helping function for dictionaries, which are used for the radio buttons.

.. codeauthor: Tobias Krauthoff <krauthoff@cs.uni-duesseldorf.de
"""

from sqlalchemy import and_

from dbas.database import DBDiscussionSession
from dbas.database.discussion_model import Argument, Statement, TextVersion, Premise, Issue
from dbas.lib import get_text_for_statement_uid, get_text_for_premisesgroup_uid, get_text_for_conclusion
from dbas.logger import logger
from dbas.recommender_system import RecommenderHelper
from dbas.strings import Translator, TextGenerator
from dbas.url_manager import UrlManager


class ItemDictHelper(object):
	"""
	Provides all functions for creating the radio buttons.
	"""

	def __init__(self, lang, issue_uid, application_url, for_api=False):
		"""
		Initialize default values

		:param lang: ui_locales
		:param issue_uid: Issue.uid
		:param application_url: application_url
		:param for_api: boolean
		:return:
		"""
		self.lang = lang
		self.issue_uid = issue_uid
		self.application_url = application_url
		self.for_api = for_api

	def prepare_item_dict_for_start(self, logged_in):
		"""
		Prepares the dict with all items for the first step in discussion, where the user chooses a position.

		:param logged_in: Boolean or String
		:return:
		"""
		db_statements = DBDiscussionSession.query(Statement)\
			.filter(and_(Statement.is_startpoint == True, Statement.issue_uid == self.issue_uid))\
			.join(TextVersion, TextVersion.uid == Statement.textversion_uid).all()
		slug = DBDiscussionSession.query(Issue).filter_by(uid=self.issue_uid).first().get_slug()

		statements_array = []
		_um = UrlManager(self.application_url, slug, self.for_api)

		if db_statements:
			for statement in db_statements:
				statements_array.append(self.__create_statement_dict(statement.uid,
				                                                     [{'title': get_text_for_statement_uid(statement.uid), 'id': statement.uid}],
																     'start',
																     _um.get_url_for_statement_attitude(True, statement.uid)))
			_tn = Translator(self.lang)
			if logged_in:
				statements_array.append(self.__create_statement_dict('start_statement',
				                                                     [{'title': _tn.get(_tn.newConclusionRadioButtonText), 'id': 0}],
																	 'start',
																	 'add'))
			else:
				statements_array.append(self.__create_statement_dict('login', [{'id': '0', 'title': _tn.get(_tn.wantToStateNewPosition)}], 'justify', 'login'))

		return statements_array

	def prepare_item_dict_for_attitude(self, statement_uid):
		"""
		Prepares the dict with all items for the second step in discussion, where the user chooses her attitude.

		:param statement_uid: Statement.uid
		:return:
		"""
		logger('DictionaryHelper', 'prepare_item_dict_for_attitude', 'def')
		_tn = Translator(self.lang)

		slug = DBDiscussionSession.query(Issue).filter_by(uid=self.issue_uid).first().get_slug()
		text = get_text_for_statement_uid(statement_uid)
		statements_array = []

		_um = UrlManager(self.application_url, slug, self.for_api)

		statements_array.append(self.__create_statement_dict('agree',
		                                                     [{'title': _tn.get(_tn.iAgreeWithInColor) + ': ' + text, 'id': 'agree'}],
															 'agree', _um.get_url_for_justifying_statement(True, statement_uid, 't')))
		statements_array.append(self.__create_statement_dict('disagree',
		                                                     [{'title': _tn.get(_tn.iDisagreeWithInColor) + ': ' + text, 'id': 'disagree'}],
															 'disagree', _um.get_url_for_justifying_statement(True, statement_uid, 'f')))
		statements_array.append(self.__create_statement_dict('dontknow',
		                                                     [{'title': _tn.get(_tn.iHaveNoOpinionYetInColor) + ': ' + text, 'id': 'dontknow'}],
															 'dontknow', _um.get_url_for_justifying_statement(True, statement_uid, 'd')))

		return statements_array

	def prepare_item_dict_for_justify_statement(self, statement_uid, nickname, is_supportive):
		"""
		Prepares the dict with all items for the third step in discussion, where the user justifies his position.

		:param statement_uid: Statement.uid
		:param nickname: User.nickname
		:param is_supportive: Boolean
		:return:
		"""
		logger('DictionaryHelper', 'prepare_item_dict_for_justify_statement', 'def')
		statements_array = []
		_tn = Translator(self.lang)
		_rh = RecommenderHelper
		slug = DBDiscussionSession.query(Issue).filter_by(uid=self.issue_uid).first().get_slug()
		db_arguments = RecommenderHelper.get_arguments_by_conclusion(statement_uid, is_supportive)

		_um = UrlManager(self.application_url, slug, self.for_api)

		if db_arguments:
			for argument in db_arguments:
				# get all premises in the premisegroup of this argument
				db_premises = DBDiscussionSession.query(Premise).filter_by(premisesgroup_uid=argument.premisesgroup_uid).all()
				premise_array = []
				for premise in db_premises:
					text = get_text_for_statement_uid(premise.statement_uid)
					text = text[0:1].upper() + text[1:]
					premise_array.append({'title': text, 'id': premise.statement_uid})

				# get attack for each premise, so the urls will be unique
				arg_id_sys, attack = _rh.get_attack_for_argument(argument.uid, self.issue_uid, self.lang)
				statements_array.append(self.__create_statement_dict(str(argument.uid),
				                                                     premise_array,
				                                                     'justify',
																     _um.get_url_for_reaction_on_argument(True, argument.uid, attack, arg_id_sys)))

		if nickname:
			statements_array.append(self.__create_statement_dict('start_premise',
			                                                     [{'title': _tn.get(_tn.newPremiseRadioButtonText), 'id': 0}],
																  'justify',
																  'add'))
		else:
			# elif len(statements_array) == 1:
			statements_array.append(self.__create_statement_dict('login', [{'id': '0', 'title': _tn.get(_tn.onlyOneItem)}], 'justify', 'login'))

		return statements_array

	def prepare_item_dict_for_justify_argument(self, argument_uid, attack_type, logged_in):
		"""
		Prepares the dict with all items for a step in discussion, where the user justifies his attack she has done.

		:param argument_uid: Argument.uid
		:param attack_type: String
		:param logged_in: Boolean or String
		:return:
		"""
		logger('DictionaryHelper', 'prepare_item_dict_for_justify_argument', 'def')
		statements_array = []
		_tn = Translator(self.lang)
		slug = DBDiscussionSession.query(Issue).filter_by(uid=self.issue_uid).first().get_slug()
		db_argument = DBDiscussionSession.query(Argument).filter_by(uid=argument_uid).first()

		db_arguments = []
		# description in docs: dbas/logic
		if attack_type == 'undermine':
			db_premises = DBDiscussionSession.query(Premise).filter_by(premisesgroup_uid=db_argument.premisesgroup_uid).all()
			for premise in db_premises:
				arguments = DBDiscussionSession.query(Argument).filter(and_(Argument.conclusion_uid == premise.statement_uid,
																			Argument.is_supportive == False,
				                                                            Argument.issue_uid == self.issue_uid)).all()
				db_arguments = db_arguments + arguments

		elif attack_type == 'undercut':
			db_arguments = DBDiscussionSession.query(Argument).filter(and_(Argument.argument_uid == argument_uid,
																		   Argument.is_supportive == False,
				                                                           Argument.issue_uid == self.issue_uid)).all()

		elif attack_type == 'overbid':
			db_arguments = DBDiscussionSession.query(Argument).filter(and_(Argument.argument_uid == argument_uid,
																		   Argument.is_supportive == True,
				                                                           Argument.issue_uid == self.issue_uid)).all()

		elif attack_type == 'rebut':
			db_arguments = DBDiscussionSession.query(Argument).filter(and_(Argument.conclusion_uid == db_argument.conclusion_uid,
																		   Argument.argument_uid == db_argument.argument_uid,
																		   Argument.is_supportive == False,
				                                                           Argument.issue_uid == self.issue_uid)).all()
		elif attack_type == 'support':
			db_arguments = DBDiscussionSession.query(Argument).filter(and_(Argument.conclusion_uid == db_argument.conclusion_uid,
																		   Argument.argument_uid == db_argument.argument_uid,
																		   Argument.is_supportive == db_argument.is_supportive,
				                                                           Argument.issue_uid == self.issue_uid)).all()

		_um = UrlManager(self.application_url, slug, self.for_api)

		if db_arguments:
			for argument in db_arguments:
				# get alles premises in this group
				db_premises = DBDiscussionSession.query(Premise).filter_by(premisesgroup_uid=argument.premisesgroup_uid).all()
				premises_array = []
				for premise in db_premises:
					premise_dict = dict()
					premise_dict['id'] = premise.statement_uid
					text = get_text_for_statement_uid(premise.statement_uid)
					text = text[0:1].upper() + text[1:]
					premise_dict['title'] = text
					premises_array.append(premise_dict)

				# for each justifying premise, we need a new confrontation:
				arg_id_sys, attack = RecommenderHelper.get_attack_for_argument(argument_uid, self.issue_uid, self.lang)

				url = _um.get_url_for_reaction_on_argument(True, argument.uid, attack, arg_id_sys)
				statements_array.append(self.__create_statement_dict(argument.uid, premises_array, 'justify', url))

		if logged_in:
			if len(statements_array) == 0:
				text = _tn.get(_tn.newPremisesRadioButtonTextAsFirstOne)
			else:
				text = _tn.get(_tn.newPremiseRadioButtonText)
			statements_array.append(self.__create_statement_dict('justify_premise', [{'id': '0', 'title': text}], 'justify', 'add'))
		else:
			# elif len(statements_array) == 1:
			statements_array.append(self.__create_statement_dict('login', [{'id': '0', 'title': _tn.get(_tn.onlyOneItem)}], 'justify', 'login'))

		return statements_array

	def prepare_item_dict_for_dont_know_reaction(self, argument_uid, is_supportive):
		"""
		Prepares the dict with all items for the third step, where an suppotive argument will be presented.

		:param argument_uid: Argument.uid
		:param is_supportive: Boolean
		:return:
		"""
		logger('DictionaryHelper', 'prepare_item_dict_for_dont_know_reaction', 'def')
		_tg = TextGenerator(self.lang)
		slug = DBDiscussionSession.query(Issue).filter_by(uid=self.issue_uid).first().get_slug()
		_um = UrlManager(self.application_url, slug, self.for_api)
		statements_array = []

		db_argument  = DBDiscussionSession.query(Argument).filter_by(uid=argument_uid).first()
		if not db_argument:
			return statements_array

		conclusion   = get_text_for_conclusion(db_argument, self.lang)
		premise, tmp = get_text_for_premisesgroup_uid(db_argument.premisesgroup_uid, self.lang)
		conclusion   = conclusion[0:1].lower() + conclusion[1:]
		premise	     = premise[0:1].lower() + premise[1:]
		rel_dict	 = _tg.get_relation_text_dict(premise, conclusion, False, False, False, is_dont_know=True)
		mode		 = 't' if is_supportive else 't'
		counter_mode = 'f' if is_supportive else 't'

		# relations = ['undermine', 'support', 'undercut', 'overbid', 'rebut'] # TODO 'overbid'
		relations = ['undermine', 'support', 'undercut', 'rebut']
		for relation in relations:
			if relation == 'support':
				arg_id_sys, sys_attack = RecommenderHelper.get_attack_for_argument(argument_uid, self.issue_uid, self.lang)
				url = _um.get_url_for_reaction_on_argument(True, argument_uid, sys_attack, arg_id_sys)

			else:
				current_mode = mode if relation == 'overbid' else counter_mode
				url = _um.get_url_for_justifying_argument(True, argument_uid, current_mode, relation)

			statements_array.append(self.__create_statement_dict(relation, [{'title': rel_dict[relation + '_text'], 'id':relation}], relation, url))

		return statements_array

	def prepare_item_dict_for_reaction(self, argument_uid_sys, argument_uid_user, is_supportive, attack):
		"""
		Prepares the dict with all items for the argumentation window.

		:param argument_uid_sys: Argument.uid
		:param argument_uid_user: Argument.uid
		:param is_supportive: Boolean
		:param attack: String
		:return:
		"""
		logger('DictionaryHelper', 'prepare_item_dict_for_reaction', 'def')
		_tg  = TextGenerator(self.lang)
		slug = DBDiscussionSession.query(Issue).filter_by(uid=self.issue_uid).first().get_slug()

		db_sys_argument = DBDiscussionSession.query(Argument).filter_by(uid=argument_uid_sys).first()
		db_user_argument = DBDiscussionSession.query(Argument).filter_by(uid=argument_uid_user).first()
		statements_array = []
		if not db_sys_argument or not db_user_argument:
			return statements_array

		conclusion   = get_text_for_conclusion(db_sys_argument, self.lang)
		premise, tmp = get_text_for_premisesgroup_uid(db_sys_argument.premisesgroup_uid, self.lang)
		conclusion	 = conclusion[0:1].lower() + conclusion[1:]
		premise		 = premise[0:1].lower() + premise[1:]

		rel_dict	 = _tg.get_relation_text_dict(premise, conclusion, False, True, not db_sys_argument.is_supportive)
		mode		 = 't' if is_supportive else 'f'
		_um			 = UrlManager(self.application_url, slug, self.for_api)
		_rh          = RecommenderHelper

		# based in the relation, we will fetch different url's for the items
		# relations = ['undermine', 'support', 'undercut', 'overbid', 'rebut'] # TODO overbid
		# TODO COMMA16 Special Case (forbid: undercuts of undercuts)
		# if attack == 'undercut':
		# 	relations = ['undermine', 'support', 'rebut']
		# else:
		relations = ['undermine', 'support', 'undercut', 'rebut']
		for relation in relations:
			url = ''

			# special case, when the user selectes the support, because this does not need to be justified!
			if relation == 'support':
				arg_id_sys, sys_attack = _rh.get_attack_for_argument(argument_uid_sys, self.issue_uid, self.lang)
				if sys_attack == 'rebut' and attack == 'undercut':
					# case: system makes an undercut and the user supports this
					# new attack can be an rebut, so another undercut for the users argument
					# therefore now the users opininion is the new undercut (e.g. rebut)
					# because he supported it!
					url = _um.get_url_for_reaction_on_argument(True, arg_id_sys, sys_attack, db_sys_argument.argument_uid)
				else:
					url = _um.get_url_for_reaction_on_argument(True, argument_uid_sys, sys_attack, arg_id_sys)

			# easy cases
			elif relation == 'undermine' or relation == 'undercut':

				url = _um.get_url_for_justifying_argument(True, argument_uid_sys, mode, relation)

			elif relation == 'overbid':
				# if overbid is the 'overbid', it's easy
				#  url = _um.get_url_for_justifying_argument(True, argument_uid_sys, mode, relation)
				# otherwise it will be the attack again
				url = _um.get_url_for_justifying_argument(True, argument_uid_user, mode, attack)

			elif relation == 'rebut':  # if we are having an rebut, everything seems different
				if attack == 'undermine':  # rebutting an undermine will be a support for the initial argument
					url = _um.get_url_for_justifying_statement(True, db_sys_argument.conclusion_uid, mode)
				# rebutting an undercut will be a overbid for the initial argument
				elif attack == 'undercut':
					url = _um.get_url_for_justifying_argument(True, argument_uid_user, mode, 'overbid')
				# rebutting an rebut will be a justify for the initial argument
				elif attack == 'rebut':
					url = _um.get_url_for_justifying_statement(True, db_user_argument.conclusion_uid, mode)

			else:
				url = _um.get_url_for_justifying_argument(True, argument_uid_sys, mode, relation)

			statements_array.append(self.__create_statement_dict(relation, [{'title': rel_dict[relation + '_text'], 'id':relation}], relation, url))

		# last item is the change attack button or step back, if we have bno other attack
		arg_id_sys, new_attack = _rh.get_attack_for_argument(argument_uid_user, self.issue_uid, self.lang, restriction_on_attacks=attack, restriction_on_arg_uid=argument_uid_sys)
		if new_attack == 'no_other_attack' or new_attack == 'end':
			relation = 'step_back'
			url = 'back' if self.for_api else 'window.history.go(-1)'
		else:
			relation = 'no_opinion'
			url = _um.get_url_for_reaction_on_argument(True, argument_uid_user, new_attack, arg_id_sys)
			url = url[0:len(url) - 1] + '?rm_bubble=' + str(argument_uid_user) + '/' + attack + '/' + str(argument_uid_sys) + '"'
		statements_array.append(self.__create_statement_dict(relation, [{'title': rel_dict[relation + '_text'], 'id':relation}], relation, url))

		return statements_array

	def prepare_item_dict_for_choosing(self, argument_or_statement_id, pgroup_ids, is_argument, is_supportive):
		"""
		Prepares the dict with all items for the choosing an premise, when the user inserted more than one new premise.

		:param argument_or_statement_id: Argument.uid or Statement.uid
		:param pgroup_ids: PremiseGroups.uid
		:param is_argument: Boolean
		:param is_supportive: Boolean
		:return: dict()
		"""
		logger('DictionaryHelper', 'prepare_item_dict_for_choosing', 'def')
		statements_array = []
		slug = DBDiscussionSession.query(Issue).filter_by(uid=self.issue_uid).first().get_slug()
		_um = UrlManager(self.application_url, slug, self.for_api)
		conclusion = argument_or_statement_id if not is_argument else None
		argument = argument_or_statement_id if is_argument else None

		for group_id in pgroup_ids:
			db_premises = DBDiscussionSession.query(Premise).filter_by(premisesgroup_uid=group_id).all()
			premise_array = []
			for premise in db_premises:
				text = get_text_for_statement_uid(premise.statement_uid)
				premise_array.append({'title': text, 'id': premise.statement_uid})

			# get attack for each premise, so the urls will be unique
			logger('DictionaryHelper', 'prepare_item_dict_for_choosing', 'premisesgroup_uid: ' + str(group_id) +
			       ', conclusion_uid: ' + str(conclusion) +
			       ', argument_uid: ' + str(argument) +
			       ', is_supportive: ' + str(is_supportive))
			db_argument = DBDiscussionSession.query(Argument).filter(and_(Argument.premisesgroup_uid == group_id,
																		  Argument.conclusion_uid == conclusion,
																		  Argument.argument_uid == argument,
																		  Argument.is_supportive == is_supportive)).first()
			arg_id_sys, attack = RecommenderHelper.get_attack_for_argument(db_argument.uid, self.issue_uid, self.lang)
			url = _um.get_url_for_reaction_on_argument(True, db_argument.uid, attack, arg_id_sys)

			statements_array.append(self.__create_statement_dict(str(db_argument.uid), premise_array, 'choose', url))
		# url = 'back' if self.for_api else 'window.history.go(-1)'
		# text = _t.get(_t.iHaveNoOpinion) + '. ' + _t.get(_t.goStepBack) + '.'
		# statements_array.append(self.__create_statement_dict('no_opinion', text, [{'title': text, 'id': 'no_opinion'}], 'no_opinion', url))
		return statements_array

	@staticmethod
	def __create_statement_dict(uid, premises, attitude, url):
		"""
		Return dictionary
		
		:param uid: Integer
		:param premises: String
		:param attitude: String
		:param url: String
		:return: dict()
		"""
		return {
			'id': 'item_' + str(uid),
			'premises': premises,
			'attitude': attitude,
			'url': url}