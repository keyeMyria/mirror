"""
Common, pure functions used by the D-BAS.


.. codeauthor:: Tobias Krauthoff <krauthoff@cs.uni-duesseldorf.de
"""
import hashlib
import locale
import time
import os
import re

from collections import defaultdict
from datetime import datetime
from html import escape
from urllib import parse

from dbas.database import DBDiscussionSession
from dbas.database.discussion_model import Argument, Premise, Statement, TextVersion, Issue, Language, User, Settings, \
    ClickedArgument, ClickedStatement, Group, MarkedArgument, MarkedStatement, PremiseGroup
from dbas.strings.keywords import Keywords as _
from dbas.strings.translator import Translator
from sqlalchemy import and_, func
from dbas.logger import logger

fallback_lang = 'en'
tag_type = 'span'


def get_global_url():
    """
    Returns the global url of the project.
    Important: the global url has to be in setup.py like "url='http://foo.bar'"

    :return: String
    """
    path = str(os.path.realpath(__file__ + '/../../setup.py'))
    lines = [line.rstrip('\n').strip() for line in open(path)]

    return str([l[l.index('htt'):-2] for l in lines if 'url=' in l][0])


def get_changelog(no):
    """
    Returns the 'no' last entries from the changelog

    :param no: int
    :return: list
    """
    path = str(os.path.realpath(__file__ + '/../../CHANGELOG.md'))
    lines = [line.rstrip('\n').strip() for line in open(path) if len(line.rstrip('\n').strip()) > 0]
    changelog = []
    title = ''
    body = []
    for l in lines:
        if l.startswith('#'):
            if len(title) > 0:
                changelog.append({'title': title, 'body': body})
                body = []
            title = l.replace('## ', '')
        else:
            body.append(l.replace('- ', ''))

    return changelog[0:no]


def is_usage_with_ldap(request):
    """
    Returns true, if ldap usage is set to true in current ini file.

    :param request:Request
    :return: Boolean
    """
    if 'settings:ldap:usage' in request.registry.settings:
        return True if request.registry.settings['settings:ldap:usage'] == 'true' else False
    return False


def is_development_mode(request):
    """
    Returns true, if mode is set to development in current ini file.

    :param request:Request
    :return: Boolean
    """
    if 'mode' in request.registry.settings:
        return True if request.registry.settings['mode'] == 'development' else False
    return False


def escape_string(text):
    """
    Escapes all html special chars.

    :param text: string
    :return: html.escape(text)
    """
    return escape(text)


def get_language(request):
    """
    Returns current ui locales code which is saved in current cookie or the registry.

    :param request: request
    :return: ui_locales
    """
    try:
        lang = request.cookies['_LOCALE_']
    except (KeyError, AttributeError):
        lang = request.registry.settings['pyramid.default_locale_name']
    request._LOCALE_ = lang
    # we have to set 'ui_locales = get_language(request)' in each view again, because D-BAS is no object
    return str(lang)


def get_discussion_language(request, current_issue_uid=1):
    """
    Returns Language.ui_locales
    CALL AFTER issue_helper.get_id_of_slug(..)!

    :param request: self.request
    :param current_issue_uid: uid
    :return:
    """
    # first matchdict, then params, then session, afterwards fallback
    issue = request.matchdict['issue'] if 'issue' in request.matchdict \
        else request.params['issue'] if 'issue' in request.params \
        else request.session['issue'] if 'issue' in request.session \
        else current_issue_uid

    db_lang = DBDiscussionSession.query(Issue).filter_by(uid=issue).join(Language).first()

    return db_lang.languages.ui_locales if db_lang else 'en'


def python_datetime_pretty_print(ts, lang):
    """
    Pretty print of a locale

    :param ts:  Timestamp
    :param lang: ui_locales
    :return: String
    """
    formatter = '%d. %b.'
    if lang == 'de':
        try:
            locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
            formatter = '%b. %Y'
        except locale.Error:
            locale.setlocale(locale.LC_TIME, 'en_US.UTF8')

    return datetime.strptime(str(ts), '%Y-%m-%d').strftime(formatter)


def get_all_arguments_by_statement(statement_uid, include_disabled=False):
    """
    Returns a list of all arguments where the statement is a conclusion or member of the premisegroup

    :param statement_uid: Statement.uid
    :param include_disabled: Boolean
    :return: [Arguments]
    """
    logger('DBAS.LIB', 'get_all_arguments_by_statement', 'main {}, include_disabled {}'.format(statement_uid, include_disabled))
    db_arguments = __get_arguments_of_conclusion(statement_uid, include_disabled)
    return_array = [arg for arg in db_arguments] if db_arguments else []

    if include_disabled:
        premises = DBDiscussionSession.query(Premise).filter_by(statement_uid=statement_uid).all()
    else:
        premises = DBDiscussionSession.query(Premise).filter_by(
            is_disabled=False,
            statement_uid=statement_uid
        ).all()

    for premise in premises:
        return_array = return_array + __get_argument_of_premisegroup(premise.premisesgroup_uid, include_disabled)

    # undercuts
    db_all_undercuts = []
    for arg in return_array:
        db_all_undercuts = db_all_undercuts + __get_undercuts_of_argument(arg.uid, include_disabled)

    # undercutted undercuts
    db_all_undercutted_undercuts = []
    for arg in db_all_undercuts:
        db_all_undercutted_undercuts = db_all_undercuts + __get_undercuts_of_argument(arg.uid, include_disabled)

    return_array = list(set(return_array + db_all_undercuts + db_all_undercutted_undercuts))

    logger('DBAS.LIB', 'get_all_arguments_by_statement', 'returning arguments ' + str([arg.uid for arg in return_array]))
    return return_array if len(return_array) > 0 else None


def __get_argument_of_premisegroup(premisesgroup_uid, include_disabled):
    """
    Returns all arguments with the given premisegroup

    :param premisesgroup_uid: PremisgGroup.uid
    :param include_disabled: Boolean
    :return: list of Arguments
    """
    if include_disabled:
        db_arguments = DBDiscussionSession.query(Argument).filter_by(premisesgroup_uid=premisesgroup_uid).all()
    else:
        db_arguments = DBDiscussionSession.query(Argument).filter_by(
            is_disabled=False,
            premisesgroup_uid=premisesgroup_uid).all()
    return db_arguments if db_arguments else []


def __get_undercuts_of_argument(argument_uid, include_disabled):
    """
    Returns all undercuts fo the given argument

    :param argument_uid: Argument.uid
    :param include_disabled: boolean
    :return: list of Arguments
    """
    if include_disabled:
        db_undercuts = DBDiscussionSession.query(Argument).filter_by(argument_uid=argument_uid).all()
    else:
        db_undercuts = DBDiscussionSession.query(Argument).filter_by(
            is_disabled=False,
            argument_uid=argument_uid
        ).all()
    return db_undercuts if db_undercuts else []


def __get_arguments_of_conclusion(statement_uid, include_disabled):
    """
    Returns all arguments, where the statement is set as conclusion

    :param statement_uid: Statement.uid
    :param include_disabled: Boolean
    :return: list of arguments
    """
    if include_disabled:
        db_arguments = DBDiscussionSession.query(Argument).filter_by(conclusion_uid=statement_uid).all()
    else:
        db_arguments = DBDiscussionSession.query(Argument).filter_by(is_disabled=False,
                                                                     conclusion_uid=statement_uid).all()
    return db_arguments if db_arguments else []


def get_text_for_argument_uid(uid, nickname=None, with_html_tag=False, start_with_intro=False, first_arg_by_user=False,
                              user_changed_opinion=False, rearrange_intro=False, colored_position=False,
                              attack_type=None, minimize_on_undercut=False, is_users_opinion=True, anonymous_style=False,
                              support_counter_argument=False):
    """
    Returns current argument as string like "conclusion, because premise1 and premise2"

    Please, do not touch this!

    :param uid: Integer
    :param with_html_tag: Boolean
    :param start_with_intro: Boolean
    :param first_arg_by_user: Boolean
    :param user_changed_opinion: Boolean
    :param rearrange_intro: Boolean
    :param colored_position: Boolean
    :param attack_type: String
    :param minimize_on_undercut: Boolean
    :param anonymous_style: Boolean
    :param support_counter_argument: Boolean
    :return: String
    """
    logger('DBAS.LIB', 'get_text_for_argument_uid', 'main ' + str(uid))
    db_argument = DBDiscussionSession.query(Argument).get(uid)
    if not db_argument:
        return None

    lang = db_argument.lang
    # catch error

    _t = Translator(lang)
    premisegroup_by_user = False
    author_uid = None
    if nickname is not None:

        db_user = DBDiscussionSession.query(User).filter_by(nickname=str(nickname)).first()
        if db_user:
            author_uid = db_user.uid
            pgroup = DBDiscussionSession.query(PremiseGroup).get(db_argument.premisesgroup_uid)
            marked_argument = DBDiscussionSession.query(MarkedArgument).filter(and_(MarkedArgument.argument_uid == uid,
                                                                                    MarkedArgument.author_uid == db_user.uid)).first()
            premisegroup_by_user = pgroup.author_uid == db_user.uid or marked_argument is not None

    # getting all argument id
    arg_array = [db_argument.uid]
    while db_argument.argument_uid:
        db_argument = DBDiscussionSession.query(Argument).get(db_argument.argument_uid)
        arg_array.append(db_argument.uid)

    if attack_type == 'jump':
        return __build_argument_for_jump(arg_array, with_html_tag)

    if len(arg_array) == 1:
        # build one argument only
        return __build_single_argument(arg_array[0], rearrange_intro, with_html_tag, colored_position, attack_type, _t,
                                       start_with_intro, is_users_opinion, anonymous_style, support_counter_argument, author_uid)

    else:
        # get all pgroups and at last, the conclusion
        return __build_nested_argument(arg_array, first_arg_by_user, user_changed_opinion, with_html_tag,
                                       start_with_intro, minimize_on_undercut, anonymous_style, premisegroup_by_user, _t)


def get_all_arguments_with_text_by_statement_id(statement_uid):
    """
    Given a statement_uid, it returns all arguments, which use this statement and adds
    the corresponding text to it, which normally appears in the bubbles. The resulting
    text depends on the provided language.

    :param statement_uid: uid to a statement, which should be analyzed
    :return: list of dictionaries containing some properties of these arguments
    :rtype: list
    """
    logger('DBAS.LIB', 'get_all_arguments_with_text_by_statement_id', 'main ' + str(statement_uid))
    arguments = get_all_arguments_by_statement(statement_uid)
    results = list()
    if arguments:
        for argument in arguments:
            results.append({'uid': argument.uid,
                            'text': get_text_for_argument_uid(argument.uid)})
        return results


def get_all_arguments_with_text_and_url_by_statement_id(statement_uid, urlmanager, color_statement=False, is_jump=False):
    """
    Given a statement_uid, it returns all arguments, which use this statement and adds
    the corresponding text to it, which normally appears in the bubbles. The resulting
    text depends on the provided language.

    :param statement_uid: Id to a statement, which should be analyzed
    :param color_statement: True, if the statement (specified by the ID) should be colored
    :return: list of dictionaries containing some properties of these arguments
    :rtype: list
    """
    logger('DBAS.LIB', 'get_all_arguments_with_text_by_statement_id', 'main ' + str(statement_uid))
    arguments = get_all_arguments_by_statement(statement_uid)
    uids = [arg.uid for arg in arguments] if arguments else None
    results = list()
    sb = '<{} data-argumentation-type="position">'.format(tag_type) if color_statement else ''
    se = '</{}>'.format(tag_type) if color_statement else ''

    if not uids:
        return []

    uids.sort()
    for uid in uids:
        statement_text = get_text_for_statement_uid(statement_uid)
        attack_type = 'jump' if is_jump else ''
        argument_text = get_text_for_argument_uid(uid, anonymous_style=True, attack_type=attack_type)
        pos = argument_text.lower().find(statement_text.lower())
        argument_text = argument_text[0:pos] + sb + argument_text[pos:pos + len(statement_text)] + se + argument_text[pos + len(statement_text):]
        results.append({'uid': uid,
                        'text': argument_text,
                        'url': urlmanager.get_url_for_jump(False, uid)})
    return results


def get_slug_by_statement_uid(uid):
    """
    Returns slug for the given Issue.uid

    :param uid: Issue.uid
    :return: String
    """
    db_statement = DBDiscussionSession.query(Statement).get(uid)
    return resolve_issue_uid_to_slug(db_statement.issue_uid)


def __build_argument_for_jump(arg_array, with_html_tag):
    """
    Build tet for an argument, if we jump to this argument

    :param arg_array: [Argument]
    :param with_html_tag: Boolean
    :return: String
    """
    tag_premise = ('<' + tag_type + ' data-argumentation-type="attack">') if with_html_tag else ''
    tag_conclusion = ('<' + tag_type + ' data-argumentation-type="argument">') if with_html_tag else ''

    pro_tag = '<{} data-attitude="pro">'.format(tag_type)
    con_tag = '<{} data-attitude="con">'.format(tag_type)
    end_tag = '</{}>'.format(tag_type)
    tag_end = ('</' + tag_type + '>') if with_html_tag else ''
    lang = DBDiscussionSession.query(Argument).get(arg_array[0]).lang
    _t = Translator(lang)

    if len(arg_array) == 1:
        db_argument = DBDiscussionSession.query(Argument).get(arg_array[0])
        premises, uids = get_text_for_premisesgroup_uid(db_argument.premisesgroup_uid)
        if premises[-1] != '.':
            premises += '.'
        conclusion = get_text_for_statement_uid(db_argument.conclusion_uid)

        if lang == 'de':
            intro = _t.get(_.itIsTrueThatAnonymous) if db_argument.is_supportive else _t.get(_.itIsFalseThatAnonymous)
            intro = intro[0:1].upper() + intro[1:]
            intro = (pro_tag if db_argument.is_supportive else con_tag) + intro + end_tag
            ret_value = intro + ' ' + tag_conclusion + conclusion + tag_end
            ret_value += ', ' + _t.get(_.because).lower() + ' ' + tag_premise + premises + tag_end
        else:
            ret_value = tag_conclusion + conclusion + ' ' + tag_end
            ret_value += (con_tag + _t.get(_.isNotRight).lower() + end_tag) if not db_argument.is_supportive else ''
            ret_value += ' ' + _t.get(_.because).lower() + ' '
            ret_value += tag_premise + premises + tag_end

    elif len(arg_array) == 2:
        db_undercut = DBDiscussionSession.query(Argument).get(arg_array[0])
        db_conclusion_argument = DBDiscussionSession.query(Argument).get(arg_array[1])
        premise, uids = get_text_for_premisesgroup_uid(db_undercut.premisesgroup_uid)
        conclusion_premise, uids = get_text_for_premisesgroup_uid(db_conclusion_argument.premisesgroup_uid)
        conclusion_conclusion = get_text_for_statement_uid(db_conclusion_argument.conclusion_uid)

        premise = tag_premise + premise + tag_end
        conclusion_premise = tag_conclusion + conclusion_premise + tag_end
        conclusion_conclusion = tag_conclusion + conclusion_conclusion + tag_end

        intro = (_t.get(_.statementAbout) + ' ') if lang == 'de' else ''
        bind = con_tag + _t.get(_.isNotAGoodReasonFor) + end_tag
        because = _t.get(_.because)
        ret_value = '{}{} {} {}. {} {}.'.format(intro, conclusion_premise, bind, conclusion_conclusion, because, premise)
    else:
        db_undercut1 = DBDiscussionSession.query(Argument).get(arg_array[0])
        db_undercut2 = DBDiscussionSession.query(Argument).get(arg_array[1])
        db_argument = DBDiscussionSession.query(Argument).get(arg_array[2])
        premise1, uids = get_text_for_premisesgroup_uid(db_undercut1.premisesgroup_uid)
        premise2, uids = get_text_for_premisesgroup_uid(db_undercut2.premisesgroup_uid)
        premise3, uids = get_text_for_premisesgroup_uid(db_argument.premisesgroup_uid)
        conclusion = get_text_for_statement_uid(db_argument.conclusion_uid)

        # intro = (_t.get(_.statementAbout) + ' ') if lang == 'de' else ''
        bind = con_tag + _t.get(_.isNotAGoodReasonAgainstArgument) + end_tag
        because = _t.get(_.because)
        seperator = ',' if lang == 'de' else ''

        premise1 = tag_premise + premise1 + tag_end
        premise2 = tag_conclusion + premise2 + tag_end
        argument = '{}{} {} {}'.format(conclusion, seperator, because.lower(), premise3)
        argument = tag_conclusion + argument + tag_end

        # P2 ist kein guter Grund gegen das Argument, dass C weil P3. Weil P1
        ret_value = '{} {} {}. {} {}'.format(premise2, bind, argument, because, premise1)

    return ret_value


def __build_single_argument(uid, rearrange_intro, with_html_tag, colored_position, attack_type, _t, start_with_intro,
                            is_users_opinion, anonymous_style, support_counter_argument=False, author_uid=None):
    """
    Build up argument text for a single argument

    Please, do not touch this!

    :param uid: Argument.uid
    :param rearrange_intro: Boolean
    :param with_html_tag: Boolean
    :param colored_position: Boolean
    :param attack_type: String
    :param _t: Translator
    :param start_with_intro: Boolean
    :param is_users_opinion: Boolean
    :param anonymous_style: Boolean
    :param support_counter_argument: Boolean
    :param author_uid: User.uid
    :return: String
    """
    logger('DBAS.LIB', '__build_single_argument', 'main ' + str(uid))
    db_argument = DBDiscussionSession.query(Argument).get(uid)
    premises, uids = get_text_for_premisesgroup_uid(db_argument.premisesgroup_uid)
    conclusion = get_text_for_statement_uid(db_argument.conclusion_uid)
    lang = DBDiscussionSession.query(Argument).get(uid).lang

    if lang != 'de':
        # conclusion = conclusion[0:1].lower() + conclusion[1:]  # pretty print
        premises = premises[0:1].lower() + premises[1:]  # pretty print

    sb_none = '<' + tag_type + '>' if with_html_tag else ''
    se = '</' + tag_type + '>' if with_html_tag else ''
    if attack_type not in ['dont_know', 'jump']:
        sb = '<' + tag_type + '>' if with_html_tag else ''
        if colored_position:
            sb = '<' + tag_type + ' data-argumentation-type="position">' if with_html_tag else ''
        if attack_type == 'undermine':
            premises = sb + premises + se
        else:
            conclusion = sb + conclusion + se
    else:
        sb = '<' + tag_type + ' data-argumentation-type="argument">' if with_html_tag else ''
        sb_tmp = '<' + tag_type + ' data-argumentation-type="attack">' if with_html_tag else ''
        premises = sb + premises + se
        conclusion = sb_tmp + conclusion + se

    marked_element = False
    if author_uid:
        db_marked = DBDiscussionSession.query(MarkedArgument).filter(MarkedArgument.argument_uid == uid,
                                                                     MarkedArgument.author_uid == author_uid).first()
        marked_element = db_marked is not None
    youHaveTheOpinionThat = _t.get(_.youHaveTheOpinionThat).format('').strip()

    if lang == 'de':
        if start_with_intro and not anonymous_style:
            if rearrange_intro:
                intro = _t.get(_.itTrueIsThat) if db_argument.is_supportive else _t.get(_.itFalseIsThat)
            else:
                intro = _t.get(_.itIsTrueThat) if db_argument.is_supportive else _t.get(_.itIsFalseThat)

            ret_value = (sb_none if attack_type in ['dont_know'] else sb) + intro + se + ' '
        elif is_users_opinion and not anonymous_style:
            ret_value = sb_none
            ret_value += _t.get(_.youAgreeWithThecounterargument) if support_counter_argument else (youHaveTheOpinionThat if marked_element else _t.get(_.youArgue))
            ret_value += se + ' '
        else:
            ret_value = sb_none + _t.get(_.itIsTrueThatAnonymous if db_argument.is_supportive else _.itIsFalseThatAnonymous) + se + ' '
        ret_value += ' {}{}{} '.format(sb, _t.get(_.itIsNotRight), se) if not db_argument.is_supportive else ''
        ret_value += conclusion
        ret_value += ', ' if lang == 'de' else ' '
        ret_value += sb_none + _t.get(_.because).lower() + se + ' ' + premises
    else:
        tmp = sb + ' ' + _t.get(_.isNotRight).lower() + se + ', ' + _t.get(_.because).lower() + ' '
        ret_value = (youHaveTheOpinionThat + ' ' if marked_element else '') + conclusion + ' '
        ret_value += _t.get(_.because).lower() if db_argument.is_supportive else tmp
        ret_value += ' ' + premises

    return ret_value


def __build_nested_argument(arg_array, first_arg_by_user, user_changed_opinion, with_html_tag, start_with_intro,
                            minimize_on_undercut, anonymous_style, premisegroup_by_user, _t):
    """

    :param arg_array:
    :param first_arg_by_user:
    :param user_changed_opinion:
    :param with_html_tag:
    :param start_with_intro:
    :param minimize_on_undercut:
    :param anonymous_style:
    :param premisegroup_by_user:
    :param _t:
    :return:
    """
    logger('DBAS.LIB', '__build_nested_argument', 'main ' + str(arg_array))

    # get all pgroups and at last, the conclusion
    pgroups = []
    supportive = []
    arg_array = arg_array[::-1]
    local_lang = DBDiscussionSession.query(Argument).get(arg_array[0]).lang

    # grepping all arguments in the chain
    for uid in arg_array:
        db_argument = DBDiscussionSession.query(Argument).get(uid)
        text, tmp = get_text_for_premisesgroup_uid(db_argument.premisesgroup_uid)

        pgroups.append(text)
        supportive.append(db_argument.is_supportive)

    uid = DBDiscussionSession.query(Argument).get(arg_array[0]).conclusion_uid
    conclusion = get_text_for_statement_uid(uid)

    # html tags for framing
    sb = '<{} data-argumentation-type="position">'.format(tag_type) if with_html_tag else ''
    se = '</{}>'.format(tag_type) if with_html_tag else ''

    because = (', ' if local_lang == 'de' else ' ') + _t.get(_.because).lower() + ' '

    if len(arg_array) % 2 is 0 and not first_arg_by_user and not anonymous_style:  # system starts
        ret_value = _t.get(_.earlierYouArguedThat if user_changed_opinion else _.otherUsersSaidThat) + ' '
        tmp_users_opinion = True  # user after system

    elif not anonymous_style:  # user starts
        ret_value = (_t.get(_.soYourOpinionIsThat) + ': ') if start_with_intro else ''
        tmp_users_opinion = False  # system after user
        conclusion = se + conclusion[0:1].upper() + conclusion[1:]  # pretty print
    else:
        ret_value = _t.get(_.someoneArgued) + ' '
        tmp_users_opinion = False

    tmp = _t.get(_.itFalseIsThat) + ' ' if not supportive[0] else ''
    ret_value += tmp + conclusion + because + pgroups[0] + '.'
    del pgroups[0]

    # just display the last premise group on undercuts, because the story is always saved in all bubbles

    if minimize_on_undercut and not user_changed_opinion and len(pgroups) > 2:
        if premisegroup_by_user:
            return _t.get(_.butYouCounteredWith).strip() + ' ' + sb + pgroups[len(pgroups) - 1] + se + '.'
        else:
            return _t.get(_.butYouCounteredWith).strip() + ' ' + sb + pgroups[len(pgroups) - 1] + se + '.'

    for i, pgroup in enumerate(pgroups):
        ret_value += ' '
        if tmp_users_opinion and not anonymous_style:
            tmp = _.butYouCounteredWithArgument if premisegroup_by_user else _.butYouCounteredWithInterest
            ret_value += _t.get(_.otherParticipantsConvincedYouThat if user_changed_opinion else tmp)
        elif not anonymous_style:
            ret_value += _t.get(_.youAgreeWithThatNow)
        else:
            ret_value += _t.get(_.otherUsersSaidThat) if i == 0 else _t.get(_.thenOtherUsersSaidThat)

        ret_value += sb + ' ' + pgroups[i] + '.'
        tmp_users_opinion = not tmp_users_opinion

    return ret_value


def get_text_for_premisesgroup_uid(uid):
    """
    Returns joined text of the premise group and the premise ids

    :param uid: premisesgroup_uid
    :return: text, uids
    """
    db_premises = DBDiscussionSession.query(Premise).filter_by(premisesgroup_uid=uid).join(Statement).all()
    uids = []
    texts = []
    if len(db_premises) > 0:
        lang = DBDiscussionSession.query(Statement).get(db_premises[0].statements.uid).lang
    else:
        return '', uids

    _t = Translator(lang)

    for premise in db_premises:
        tmp = get_text_for_statement_uid(premise.statements.uid)
        uids.append(str(premise.statements.uid))
        texts.append(str(tmp))

    return ' {} '.format(_t.get(_.aand)).join(texts), uids


def get_text_for_statement_uid(uid, colored_position=False):
    """
    Returns text of statement with given uid

    :param uid: Statement.uid
    :param colored_position: Boolean
    :return: String
    """
    try:
        if isinstance(int(uid), int):
            db_statement = DBDiscussionSession.query(Statement).get(uid)
            if not db_statement:
                return None

            db_textversion = DBDiscussionSession.query(TextVersion).order_by(TextVersion.uid.desc()).filter_by(
                uid=db_statement.textversion_uid).first()
            content = db_textversion.content

            while content.endswith(('.', '?', '!')):
                content = content[:-1]

            sb = '<' + tag_type + ' data-argumentation-type="position">' if colored_position else ''
            se = '</' + tag_type + '>' if colored_position else ''

            return sb + content + se

    except (ValueError, TypeError):
        return None


def get_text_for_premise(uid, colored_position=False):
    """
    Returns text of premise with given uid

    :param uid: Statement.uid
    :param colored_position: Boolean
    :return: String
    """
    db_premise = DBDiscussionSession.query(Premise).filter_by(uid).first()
    if db_premise:
        return get_text_for_statement_uid(db_premise.statement_uid, colored_position)
    else:
        return None


def get_text_for_conclusion(argument, start_with_intro=False, rearrange_intro=False, is_users_opinion=True):
    """
    Check the arguments conclusion whether it is an statement or an argument and returns the text

    :param argument: Argument
    :param start_with_intro: Boolean
    :param rearrange_intro: Boolean
    :return: String
    """
    if argument.argument_uid:
        return get_text_for_argument_uid(argument.argument_uid, start_with_intro, rearrange_intro=rearrange_intro, is_users_opinion=is_users_opinion)
    else:
        return get_text_for_statement_uid(argument.conclusion_uid)


def resolve_issue_uid_to_slug(uid):
    """
    Given the issue uid query database and return the correct slug of the issue.

    :param uid: issue_uid
    :type uid: int
    :return: Slug of issue
    :rtype: str
    """
    issue = DBDiscussionSession.query(Issue).get(uid)
    return issue.get_slug() if issue else None


def get_all_attacking_arg_uids_from_history(history):
    """
    Returns all arguments of the history, which attacked the user

    :param history: String
    :return: [Arguments.uid]
    :rtype: list
    """
    try:
        splitted_history = history.split('-')
        uids = []
        for part in splitted_history:
            if 'reaction' in part:
                parts = part.split('/')
                pos = parts.index('reaction')
                uids.append(part.split('/')[pos + 3])
        return uids
    except AttributeError:
        return []


def get_user_by_private_or_public_nickname(nickname):
    """
    Gets the user by his (public) nickname, based on the option, whether his nickname is public or not

    :param nickname: Nickname of the user
    :return: Current user or None
    """
    db_user = get_user_by_case_insensitive_nickname(nickname)
    db_public_user = get_user_by_case_insensitive_public_nickname(nickname)

    db_settings = None
    current_user = None

    if db_user:
        db_settings = DBDiscussionSession.query(Settings).get(db_user.uid)
    elif db_public_user:
        db_settings = DBDiscussionSession.query(Settings).get(db_public_user.uid)

    if db_settings:
        if db_settings.should_show_public_nickname and db_user:
            current_user = db_user
        elif not db_settings.should_show_public_nickname and db_public_user:
            current_user = db_public_user

    return current_user


def get_user_by_case_insensitive_nickname(nickname):
    """
    Returns user with given nickname

    :param nickname: String
    :return: User or None
    """
    return DBDiscussionSession.query(User).filter(func.lower(User.nickname) == func.lower(nickname)).first()


def get_user_by_case_insensitive_public_nickname(public_nickname):
    """
    Returns user with given public nickname

    :param public_nickname: String
    :return: User or None
    """
    return DBDiscussionSession.query(User).filter(
        func.lower(User.public_nickname) == func.lower(public_nickname)).first()


def pretty_print_options(message):
    """
    Some modifications for pretty printing

    :param message: String
    :return:  String
    """

    # check for html
    if message[0:1] == '<':
        pos = message.index('>')
        message = message[0:pos + 1] + message[pos + 1:pos + 2].upper() + message[pos + 2:]
    else:
        message = message[0:1].upper() + message[1:]

    # check for html
    if message[-1] == '>':
        pos = message.rfind('<')
        if message[pos - 1:pos] not in ['.', '?', '!']:
            message = message[0:pos] + '.' + message[pos:]
    else:
        if not message.endswith(tuple(['.', '?', '!'])) and id is not 'now':
            message += '.'

    return message


def create_speechbubble_dict(is_user=False, is_system=False, is_status=False, is_info=False, is_flagable=False,
                             is_author=False, id='', url='', message='', omit_url=False, argument_uid=None,
                             statement_uid=None, is_supportive=None, nickname='anonymous', lang='en',
                             is_users_opinion=False):
    """
    Creates an dictionary which includes every information needed for a bubble.

    :param is_user: Boolean
    :param is_system: Boolean
    :param is_status: Boolean
    :param is_info: Boolean
    :param is_flagable: Boolean
    :param id: id of bubble
    :param url: URL
    :param message: String
    :param omit_url: Boolean
    :param argument_uid: Argument.uid
    :param statement_uid: Statement.uid
    :param is_supportive: Boolean
    :param nickname: String
    :param lang: String
    :return: dict()
    """
    message = pretty_print_options(message)

    # check for users opinion
    if is_user and nickname != 'anonymous':
        db_user = DBDiscussionSession.query(User).filter_by(nickname=nickname).first()
        db_marked = None
        if argument_uid is not None and db_user is not None:
            db_marked = DBDiscussionSession.query(MarkedArgument).filter(and_(MarkedArgument.argument_uid == argument_uid,
                                                                              MarkedArgument.author_uid == db_user.uid)).first()

        if statement_uid is not None and db_user is not None:
            db_marked = DBDiscussionSession.query(MarkedStatement).filter(and_(MarkedStatement.statement_uid == statement_uid,
                                                                               MarkedStatement.author_uid == db_user.uid)).first()

        is_users_opinion = db_marked is not None

    speech = {
        'is_user': is_user,
        'is_system': is_system,
        'is_status': is_status,
        'is_info': is_info,
        'is_flagable': is_flagable,
        'is_author': is_author,
        'id': id if len(str(id)) > 0 else str(time.time()),
        'url': url if len(str(url)) > 0 else 'None',
        'message': message,
        'omit_url': omit_url,
        'data_type': 'argument' if argument_uid else 'statement' if statement_uid else 'None',
        'data_argument_uid': str(argument_uid),
        'data_statement_uid': str(statement_uid),
        'data_is_supportive': str(is_supportive),
        'is_users_opinion': str(is_users_opinion),
    }

    votecount_keys = __get_text_for_click_count(nickname, is_user, is_supportive, argument_uid, statement_uid, speech, lang)

    speech['votecounts_message'] = votecount_keys[speech['votecounts']]

    return speech


def __get_text_for_click_count(nickname, is_user, is_supportive, argument_uid, statement_uid, speech, lang):
    """
    Build text for a bubble, how many other participants have the same interest?

    :param nickname: User.nickname
    :param is_user: boolean
    :param is_supportive: boolean
    :param argument_uid: Argument.uid
    :param statement_uid: Statement.uid
    :param speech: dict()
    :param lang: ui_locales
    :return: [String]
    """
    db_votecounts = None

    if is_supportive is None:
        is_supportive = False

    if not nickname:
        nickname = 'anonymous'
    db_user = DBDiscussionSession.query(User).filter_by(nickname=nickname).first()
    if not db_user:
        db_user = DBDiscussionSession.query(User).filter_by(nickname='anonymous').first()

    if argument_uid:
        db_votecounts = DBDiscussionSession.query(ClickedArgument). \
            filter(and_(ClickedArgument.argument_uid == argument_uid,
                        ClickedArgument.is_up_vote == is_supportive,
                        ClickedArgument.is_valid,
                        ClickedArgument.author_uid != db_user.uid)). \
            all()

    elif statement_uid:
        db_votecounts = DBDiscussionSession.query(ClickedStatement). \
            filter(and_(ClickedStatement.statement_uid == statement_uid,
                        ClickedStatement.is_up_vote == is_supportive,
                        ClickedStatement.is_valid,
                        ClickedStatement.author_uid != db_user.uid)). \
            all()
    _t = Translator(lang)
    speech['votecounts'] = len(db_votecounts) if db_votecounts else 0

    votecount_keys = defaultdict(lambda: "{} {}.".format(speech['votecounts'], _t.get(_.voteCountTextMore)))
    if is_user and db_user.gender == 'm':
        votecount_keys[0] = _t.get(_.voteCountTextFirstM) + '.'
    elif is_user and db_user.gender == 'f':
        votecount_keys[0] = _t.get(_.voteCountTextFirstF) + '.'
    else:
        votecount_keys[0] = _t.get(_.voteCountTextFirst) + '.'
    votecount_keys[1] = _t.get(_.voteCountTextOneOther) + '.'

    return votecount_keys


def is_user_author_or_admin(nickname):
    """
    Check, if the given uid has admin rights or is admin

    :param nickname: current user name
    :return: true, if user is admin, false otherwise
    """
    db_user = DBDiscussionSession.query(User).filter_by(nickname=str(nickname)).first()
    db_admin_group = DBDiscussionSession.query(Group).filter_by(name='admins').first()
    db_author_group = DBDiscussionSession.query(Group).filter_by(name='authors').first()
    #  logger('Lib', 'is_user_author_or_admin', 'main')
    if db_user:
        if db_user.group_uid == db_author_group.uid or db_user.group_uid == db_admin_group.uid:
            return True

    return False


def is_user_admin(nickname):
    """
    Check, if the given uid has admin rights or is admin

    :param nickname: current user name
    :return: true, if user is admin, false otherwise
    """
    db_user = DBDiscussionSession.query(User).filter_by(nickname=str(nickname)).first()
    db_admin_group = DBDiscussionSession.query(Group).filter_by(name='admins').first()
    #  logger('Lib', 'is_user_author_or_admin', 'main')
    return db_user and db_user.group_uid == db_admin_group.uid


def is_argument_disabled_due_to_disabled_statements(argument):
    """
    Returns true if any involved statement is disabled.

    :param argument: Argument
    :return: Boolean
    """
    if argument.conclusion_uid is None:
        # check conclusion of given arguments conclusion
        db_argument = DBDiscussionSession.query(Argument).get(argument.argument_uid)
        conclusion = DBDiscussionSession(Statement).get(db_argument.conclusion_uid)
        if conclusion.is_disabled:
            return True
        # check premisegroup of given arguments conclusion
        premises = __get_all_premises_of_argument(db_argument)
        for premise in premises:
            if premise.statements.is_disabled:
                return True
    else:
        # check conclusion of given argument
        conclusion = DBDiscussionSession(Statement).get(argument.conclusion_uid)
        if conclusion.is_disabled:
            return True

    # check premisegroup of given argument
    premises = __get_all_premises_of_argument(argument)
    for premise in premises:
        if premise.statements.is_disabled:
            return True

    return False


def is_author_of_statement(nickname, statement_uid):
    """
    Is the user with given nickname author of the statement?

    :param nickname: User.nickname
    :param statement_uid: Statement.uid
    :return: Boolean
    """
    db_user = DBDiscussionSession.query(User).filter_by(nickname=str(nickname)).first()
    if not db_user:
        return False
    db_textversion = DBDiscussionSession.query(TextVersion).filter_by(statement_uid=statement_uid).order_by(
        TextVersion.uid.asc()).first()
    if not db_textversion:
        return False
    return db_textversion.author_uid == db_user.uid


def is_author_of_argument(nickname, argument_uid):
    """
    Is the user with given nickname author of the argument?

    :param nickname: User.nickname
    :param argument_uid: Argument.uid
    :return: Boolean
    """
    db_user = DBDiscussionSession.query(User).filter_by(nickname=str(nickname)).first()
    if not db_user:
        return False
    db_argument = DBDiscussionSession.query(Argument).filter(and_(Argument.uid == argument_uid,
                                                                  Argument.author_uid == db_user.uid)).first()
    return True if db_argument else False


def __get_all_premises_of_argument(argument):
    """
    Returns list with all premises of the argument.

    :param argument: Argument
    :return: list()
    """
    ret_list = []
    db_premises = DBDiscussionSession.query(Premise).filter_by(premisesgroup_uid=argument.premisesgroup_uid).join(
        Statement).all()
    for premise in db_premises:
        ret_list.append(premise)
    return ret_list


def get_profile_picture(user, size=80, ignore_privacy_settings=False):
    """
    Returns the url to a https://secure.gravatar.com picture, with the option wavatar and size of 80px

    :param user: User
    :param size: Integer, default 80
    :param ignore_privacy_settings:
    :return: String
    """
    db_settings = DBDiscussionSession.query(Settings).get(user.uid)
    additional_id = '' if db_settings.should_show_public_nickname or ignore_privacy_settings else 'x'
    url = get_global_url()
    url = url[url.index('//') + 2:]
    unknown = 'unknown@' + url
    email = (user.email + additional_id).encode('utf-8') if user else unknown.encode('utf-8')

    gravatar_url = 'https://secure.gravatar.com/avatar/' + hashlib.md5(email.lower()).hexdigest() + "?"
    gravatar_url += parse.urlencode({'d': 'wavatar', 's': str(size)})
    return gravatar_url


def get_public_profile_picture(user, size=80):
    """
    Returns the url to a https://secure.gravatar.com picture, with the option wavatar and size of 80px
    If the user doesn want an public profile, an anoynmous image will be returned

    :param user: User
    :param size: Integer, default 80
    :return: String
    """
    if user:
        additional_id = '' if DBDiscussionSession.query(Settings).get(user.uid).should_show_public_nickname else 'x'
    else:
        additional_id = 'y'
    url = get_global_url()
    url = url[url.index('//') + 2:]
    email = (user.email + additional_id).encode('utf-8') if user else ('unknown@' + url).encode('utf-8')
    gravatar_url = 'https://secure.gravatar.com/avatar/' + hashlib.md5(email.lower()).hexdigest() + "?"
    gravatar_url += parse.urlencode({'d': 'wavatar', 's': str(size)})
    return gravatar_url


def get_author_data(main_page, uid, gravatar_on_right_side=True, linked_with_users_page=True, profile_picture_size=20):
    """
    Returns a-tag with gravatar of current author and users page as href

    :param main_page: Current mainpage
    :param uid: Uid of the author
    :param gravatar_on_right_side: True, if the gravatar is on the right of authors name
    :param linked_with_users_page: True, if the text is a link to the authors site
    :param profile_picture_size: Integer
    :return: HTML-String
    """
    db_user = DBDiscussionSession.query(User).get(int(uid))
    db_settings = DBDiscussionSession.query(Settings).get(int(uid))
    if not db_user:
        return 'Missing author with uid ' + str(uid), False
    if not db_settings:
        return 'Missing settings of author with uid ' + str(uid), False
    img = '<img class="img-circle" src="' + get_profile_picture(db_user, profile_picture_size) + '">'

    nick = db_user.get_global_nickname()
    link_begin = ('<a href="' + main_page + '/user/' + str(db_user.uid) + ' " title="' + nick + '">') if linked_with_users_page else ''
    link_end = '</a>' if linked_with_users_page else ''
    if gravatar_on_right_side:
        return db_user, link_begin + nick + ' ' + img + link_end, True
    else:
        return db_user, link_begin + img + ' ' + nick + link_end, True


def bubbles_already_last_in_list(bubble_list, bubbles):
    """
    Are the given bubbles already at the end of the bubble list

    :param bubble_list: list of Bubbles
    :param bubbles:  list of bubbles
    :return: Boolean
    """
    if isinstance(bubbles, list):
        length = len(bubbles)
    else:
        length = 1
        bubbles = [bubbles]

    if len(bubble_list) < length:
        return False

    for bubble in bubbles:
        if 'message' not in bubble:
            return False

    start_index = - length
    is_already_in = False
    for bubble in bubbles:

        last = bubble_list[start_index]
        if 'message' not in last or 'message' not in bubble:
            return False

        text1 = __cleanhtml(last['message'].lower()).strip()
        text2 = __cleanhtml(bubble['message'].lower()).strip()
        is_already_in = is_already_in or (text1 == text2)
        start_index += 1

    return is_already_in


def __cleanhtml(raw_html):
    """
    Strip out html code

    :param raw_html: String
    :return: String
    """
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext
