"""
Helper for D-BAS Views

.. codeauthor:: Tobias Krauthoff <krauthoff@cs.uni-duesseldorf.de
"""

from pyramid.httpexceptions import HTTPNotFound

import dbas.handler.issue as issue_helper
import dbas.handler.voting as voting_helper
from dbas.database import DBDiscussionSession
from dbas.database.discussion_model import User
from dbas.handler import user
from dbas.helper.dictionary.discussion import DiscussionDictHelper
from dbas.helper.dictionary.items import ItemDictHelper
from dbas.helper.dictionary.main import DictionaryHelper
from dbas.input_validator import is_integer, check_belonging_of_argument, check_belonging_of_statement
from dbas.lib import get_text_for_statement_uid, get_discussion_language
from dbas.logger import logger
from dbas.review.helper.reputation import add_reputation_for
from dbas.review.helper.reputation import rep_reason_first_confrontation
from dbas.strings.keywords import Keywords as _
from dbas.strings.translator import Translator
from websocket.lib import send_request_for_info_popup_to_socketio, get_port


def get_nickname(request_authenticated_userid, for_api=None, api_data=None):
    """
    Given data from api, return nickname and session_id.

    :param request_authenticated_userid:
    :param for_api: Boolean
    :param api_data:
    :return:
    """
    nickname = api_data.get("nickname") if api_data and for_api else request_authenticated_userid
    return nickname


def preparation_for_view(for_api, api_data, request):
    """
    Does some elementary things like: getting nickname, session id and history.
    Additionally boolean, if the session is expired

    :param for_api: True, if the values are for the api
    :param api_data: Array with api data
    :param request: Current request
    :return: nickname, session_id, session_expired, history
    """
    nickname = get_nickname(request.authenticated_userid, for_api, api_data)
    session_expired = user.update_last_action(nickname)
    return nickname, session_expired


def prepare_parameter_for_justification(request, for_api):
    """
    Prepares some paramater for the justification step

    :param request: webservers request
    :param for_api: Boolean
    :return: String, Statement.uid/Argument.uid, String, Boolean, String, Issue.uid, Language.ui_locales, dict()
    """
    slug = request.matchdict['slug'] if 'slug' in request.matchdict else ''
    statement_or_arg_id = request.matchdict['statement_or_arg_id'] if 'statement_or_arg_id' in request.matchdict else ''
    mode = request.matchdict['mode'] if 'mode' in request.matchdict else ''
    supportive = mode == 't' or mode == 'd'  # supportive = t or do not know mode
    relation = request.matchdict['relation'][0] if len(request.matchdict['relation']) > 0 else ''
    issue = issue_helper.get_id_of_slug(slug, request, True) if len(slug) > 0 else issue_helper.get_issue_id(request)
    disc_ui_locales = get_discussion_language(request.matchdict, request.params, request.session, issue)
    issue_dict = issue_helper.prepare_json_of_issue(issue, request.application_url, disc_ui_locales, for_api, request.authenticated_userid)

    return slug, statement_or_arg_id, mode, supportive, relation, issue, disc_ui_locales, issue_dict


def handle_justification_step(request, for_api, ui_locales, nickname, history):
    """
    Handles the justification step

    :param request: webserver's request
    :param for_api: Boolean
    :param ui_locales: Language.ui_locales
    :param nickname: User.nickname
    :param history: string
    :return: dict(), dict(), dict()
    """
    slug, statement_or_arg_id, mode, supportive, relation, issue, disc_ui_locales, issue_dict = prepare_parameter_for_justification(
        request, for_api)
    main_page = request.application_url

    if not is_integer(statement_or_arg_id, True):
        return None, None, None

    if [c for c in ('t', 'f') if c in mode] and relation == '':
        logger('ViewHelper', 'handle_justification_step', 'justify statement')
        if not get_text_for_statement_uid(statement_or_arg_id) or not check_belonging_of_statement(issue,
                                                                                                   statement_or_arg_id):
            raise HTTPNotFound()
        item_dict, discussion_dict, extras_dict = preparation_for_justify_statement(request, for_api, main_page, slug,
                                                                                    statement_or_arg_id, supportive,
                                                                                    ui_locales, nickname, history)

    elif 'd' in mode and relation == '':
        logger('ViewHelper', 'handle_justification_step', 'do not know for {}'.format(statement_or_arg_id))
        if int(statement_or_arg_id) != 0 and \
                not check_belonging_of_argument(issue, statement_or_arg_id) and \
                not check_belonging_of_statement(issue, statement_or_arg_id):
            raise HTTPNotFound()
        item_dict, discussion_dict, extras_dict = preparation_for_dont_know_statement(request, for_api, main_page,
                                                                                      slug, statement_or_arg_id,
                                                                                      supportive, ui_locales,
                                                                                      nickname, history)

    elif [c for c in ('undermine', 'rebut', 'undercut', 'support') if c in relation]:
        logger('ViewHelper', 'handle_justification_step', 'justify argument')
        if not check_belonging_of_argument(issue, statement_or_arg_id):
            raise HTTPNotFound()
        item_dict, discussion_dict, extras_dict = preparation_for_justify_argument(request, for_api, main_page, slug,
                                                                                   statement_or_arg_id, supportive,
                                                                                   ui_locales, relation, nickname,
                                                                                   history)
        # add reputation
        add_rep, broke_limit = add_reputation_for(nickname, rep_reason_first_confrontation)
        # send message if the user is now able to review
        if broke_limit:
            _t = Translator(ui_locales)
            nickname = request.authenticated_userid
            port = get_port(request)
            send_request_for_info_popup_to_socketio(nickname, port, _t.get(_.youAreAbleToReviewNow),
                                                    request.application_url + '/review')

    else:
        logger('ViewHelper', 'handle_justification_step', '404')
        return None, None, None

    return item_dict, discussion_dict, extras_dict


def preparation_for_justify_statement(request, for_api, main_page, slug, statement_uid, supportive, ui_locales,
                                      nickname, history):
    """
    Prepares some paramater for the justification step for an statement

    :param request: webserver's request
    :param for_api: Boolean
    :param main_page: string
    :param slug: String
    :param statement_uid: Statement.uid
    :param supportive: Boolean
    :param ui_locales: Language.ui_locales
    :param nickname: string
    :param history: string
    :return: dict(), dict(), dict()
    """
    logger('ViewHelper', 'preparation_for_justify_statement', 'main')

    logged_in = DBDiscussionSession.query(User).filter_by(nickname=nickname).first() is not None
    _ddh, _idh, _dh = __prepare_helper(ui_locales, nickname, history, main_page, slug, for_api, request)

    voting_helper.add_click_for_statement(statement_uid, nickname, supportive)

    item_dict = _idh.get_array_for_justify_statement(statement_uid, nickname, supportive, history)
    discussion_dict = _ddh.get_dict_for_justify_statement(statement_uid, main_page, slug, supportive,
                                                          len(item_dict['elements']), nickname)
    extras_dict = _dh.prepare_extras_dict(slug, False, True, True, request.registry, request.application_url, request.path, nickname, for_api=for_api)
    # is the discussion at the end?
    if len(item_dict['elements']) == 0 or len(item_dict['elements']) == 1 and logged_in:
        _dh.add_discussion_end_text(discussion_dict, extras_dict, nickname, at_justify=True,
                                    current_premise=get_text_for_statement_uid(statement_uid),
                                    supportive=supportive)
    return item_dict, discussion_dict, extras_dict


def preparation_for_dont_know_statement(request, for_api, main_page, slug, argument_uid, supportive, ui_locales,
                                        nickname, history):
    """
    Prepares some paramater for the "don't know" step

    :param request: webserver's request
    :param for_api: Boolean
    :param main_page: string
    :param slug: String
    :param argument_uid: Argument.uid
    :param supportive: Boolean
    :param ui_locales: Language.ui_locales
    :param nickname: User.nickname
    :param history: string
    :return: dict(), dict(), dict()
    """
    logger('ViewHelper', 'preparation_for_dont_know_statement', 'main')

    issue = issue_helper.get_id_of_slug(slug, request, True) if len(slug) > 0 else issue_helper.get_issue_id(request)
    disc_ui_locales = get_discussion_language(request.matchdict, request.params, request.session, issue)
    _ddh = DiscussionDictHelper(disc_ui_locales, nickname, history, main_page=main_page, slug=slug)
    _idh = ItemDictHelper(disc_ui_locales, issue, main_page, for_api, path=request.path, history=history)
    _dh = DictionaryHelper(ui_locales, disc_ui_locales)

    discussion_dict = _ddh.get_dict_for_dont_know_reaction(argument_uid, main_page, nickname)
    item_dict = _idh.get_array_for_dont_know_reaction(argument_uid, supportive, nickname, discussion_dict['gender'])
    extras_dict = _dh.prepare_extras_dict(slug, True, True, True, request.registry, request.application_url, request.path, for_api=for_api,
                                          nickname=nickname)
    # is the discussion at the end?
    if len(item_dict['elements']) == 0:
        if int(argument_uid) == 0:
            argument_uid = history.split('/')[-1]
            if not is_integer(argument_uid):
                argument_uid = 0

        text = ''
        if int(argument_uid) != 0:
            text = get_text_for_statement_uid(argument_uid)

        _dh.add_discussion_end_text(discussion_dict, extras_dict, nickname, at_dont_know=True, current_premise=text)
    return item_dict, discussion_dict, extras_dict


def preparation_for_justify_argument(request, for_api, main_page, slug, statement_or_arg_id, supportive, ui_locales,
                                     relation, nickname, history):
    """
    Prepares some paramater for the justification step for an argument

    :param request: webserver's request
    :param for_api: Boolean
    :param main_page: string
    :param slug: String
    :param statement_or_arg_id: Argument.uid / Statement.uid
    :param supportive: Boolean
    :param relation: String
    :param ui_locales: Language.ui_locales
    :param nickname: string
    :param history: String
    :return: dict(), dict(), dict()
    """
    logger('ViewHelper', 'preparation_for_justify_argument', 'main')

    db_user = DBDiscussionSession.query(User).filter_by(nickname=nickname).first()
    logged_in = db_user is not None
    _ddh, _idh, _dh = __prepare_helper(ui_locales, nickname, history, main_page, slug, for_api, request)

    # justifying argument
    # is_attack = True if [c for c in ('undermine', 'rebut', 'undercut') if c in relation] else False
    item_dict = _idh.get_array_for_justify_argument(statement_or_arg_id, relation, logged_in, nickname, history)
    discussion_dict = _ddh.get_dict_for_justify_argument(statement_or_arg_id, supportive, relation)
    extras_dict = _dh.prepare_extras_dict(slug, False, True, False, request.registry, request.application_url, request.path, for_api=for_api, nickname=nickname)
    # is the discussion at the end?
    if not logged_in and len(item_dict['elements']) == 1 or logged_in and len(item_dict['elements']) == 1:
        _dh.add_discussion_end_text(discussion_dict, extras_dict, nickname, at_justify_argumentation=True)

    return item_dict, discussion_dict, extras_dict


def __prepare_helper(ui_locales, nickname, history, main_page, slug, for_api, request):
    """
    Prepares helper objects

    :param ui_locales: Language.ui_locales
    :param nickname: User.nickname
    :param history: string
    :param main_page: string
    :param slug: String
    :param for_api: Boolean
    :param request: webserver's request
    :return: dict(), dict(), dict()
    """
    issue = issue_helper.get_id_of_slug(slug, request, True) if len(slug) > 0 else issue_helper.get_issue_id(request)
    disc_ui_locales = get_discussion_language(request.matchdict, request.params, request.session, issue)
    ddh = DiscussionDictHelper(disc_ui_locales, nickname, history, main_page=main_page, slug=slug)
    idh = ItemDictHelper(disc_ui_locales, issue, main_page, for_api, path=request.path, history=history)
    dh = DictionaryHelper(ui_locales, disc_ui_locales)
    return ddh, idh, dh
