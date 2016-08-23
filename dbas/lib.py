"""
Common, pure functions used by the D-BAS.


.. codeauthor:: Tobias Krauthoff <krauthoff@cs.uni-duesseldorf.de
"""

import locale
from datetime import datetime
from html import escape

from .database import DBDiscussionSession
from .database.discussion_model import Argument, Premise, Statement, TextVersion, Issue, Language, User, Settings
from dbas.strings.translator import Translator
from dbas.strings.text_generator import TextGenerator


fallback_lang = 'en'


def escape_string(text):
    """
    Escapes all html special chars.

    :param text: string
    :return: html.escape(text)
    """
    return escape(text)


def get_language(request, current_registry):
    """
    Returns current ui locales code which is saved in current cookie or the registry.

    :param request: request
    :param current_registry: get_current_registry()
    :return: language abrreviation
    """
    try:
        lang = request.cookies['_LOCALE_']
    except (KeyError, AttributeError):
        lang = current_registry.settings['pyramid.default_locale_name']
    return str(lang)


def get_discussion_language(request, current_issue_uid=1):
    """
    Returns Language.ui_locales
    CALL AFTER IssueHelper.get_id_of_slug(..)!

    :param request: self.request
    :return:
    """
    # first matchdict, then params, then session, afterwards fallback
    issue = request.matchdict['issue'] if 'issue' in request.matchdict \
        else request.params['issue'] if 'issue' in request.params \
        else request.session['issue'] if 'issue' in request.session \
        else current_issue_uid

    db_lang = DBDiscussionSession.query(Issue).filter_by(uid=issue).join(Language).first()

    return db_lang.languages.ui_locales if db_lang else 'en'


def sql_timestamp_pretty_print(ts, lang, humanize=True, with_exact_time=False):
    """
    Pretty printing for sql timestamp in dependence of the language.

    :param ts: timestamp (arrow) as string
    :param lang: language
    :param humanize: Boolean
    :param with_exact_time: Boolean
    :return:
    """
    ts = ts.replace(hours=-2)
    if humanize:
        # if lang == 'de':
        ts = ts.to('Europe/Berlin')
        # else:
        #    ts = ts.to('US/Pacific')
        return ts.humanize(locale=lang)
    else:
        if lang == 'de':
            return ts.format('DD.MM.YYYY' + (', HH:mm:ss ' if with_exact_time else ''))
        else:
            return ts.format('YYYY-MM-DD' + (', HH:mm:ss ' if with_exact_time else ''))


def python_datetime_pretty_print(ts, lang):
    """


    :param ts:
    :param lang:
    :return:
    """
    formatter = '%d. %b.'
    if lang == 'de':
        try:
            locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
            formatter = '%b. %Y'
        except locale.Error:
            locale.setlocale(locale.LC_TIME, 'en_US.UTF8')

    return datetime.strptime(str(ts), '%Y-%m-%d').strftime(formatter)


def get_all_arguments_by_statement(uid):
    """
    Returns a list of all arguments where the statement is a conclusion or member of the premisegroup

    :param uid: Statement.uid
    :return: [Arguments]
    """
    return_array = []
    db_arguments = DBDiscussionSession.query(Argument).filter_by(conclusion_uid=uid).all()
    if db_arguments:
        return_array = db_arguments

    db_premises = DBDiscussionSession.query(Premise).filter_by(statement_uid=uid).all()

    for premise in db_premises:
        db_arguments = DBDiscussionSession.query(Argument).filter_by(premisesgroup_uid=premise.premisesgroup_uid).first()
        if db_arguments:
            return_array.append(db_arguments)

    return return_array if len(return_array) > 0 else None


def get_text_for_argument_uid(uid, with_html_tag=False, start_with_intro=False, first_arg_by_user=False,
                              user_changed_opinion=False, rearrange_intro=False, colored_position=False,
                              attack_type=None):
    """
    Returns current argument as string like "conclusion, because premise1 and premise2"

    :param uid: Integer
    :param with_html_tag: Boolean
    :param start_with_intro: Boolean
    :param first_arg_by_user: Boolean
    :param user_changed_opinion: Boolean
    :param rearrange_intro: Boolean
    :param colored_position: Boolean
    :param attack_type: Boolean
    :return: String
    """
    db_argument = DBDiscussionSession.query(Argument).filter_by(uid=uid).first()
    lang = get_lang_for_argument(uid)
    # catch error
    if not db_argument:
        return None

    _t = Translator(lang)

    # getting all argument id
    arg_array = [db_argument.uid]
    while db_argument.argument_uid:
        db_argument = DBDiscussionSession.query(Argument).filter_by(uid=db_argument.argument_uid).first()
        arg_array.append(db_argument.uid)

    if attack_type == 'jump':
        return __build_argument_for_jump(arg_array, with_html_tag)

    if len(arg_array) == 1:
        # build one argument only
        return __build_single_argument(arg_array[0], rearrange_intro, with_html_tag, colored_position, attack_type, _t)

    else:
        # get all pgroups and at last, the conclusion
        sb = '<' + TextGenerator.tag_type + '>' if with_html_tag else ''
        se = '</' + TextGenerator.tag_type + '>' if with_html_tag else ''
        doesnt_hold_because = ' ' + se + _t.get(_t.doesNotHold).lower() + ' ' + _t.get(_t.because).lower() + ' ' + sb
        return __build_nested_argument(arg_array, first_arg_by_user, user_changed_opinion, with_html_tag, start_with_intro, doesnt_hold_because, _t)


def get_all_arguments_with_text_by_statement_id(statement_uid):
    """
    Given a statement_uid, it returns all arguments, which use this statement and adds
    the corresponding text to it, which normally appears in the bubbles. The resulting
    text depends on the provided language.

    :param statement_uid: Id to a statement, which should be analyzed
    :return: list of dictionaries containing some properties of these arguments
    :rtype: list
    """
    arguments = get_all_arguments_by_statement(statement_uid)
    results = list()
    if arguments:
        for argument in arguments:
            results.append({"uid": argument.uid,
                            "text": get_text_for_argument_uid(argument.uid)})
        return results


def __build_argument_for_jump(arg_array, with_html_tag):
    """

    :param arg_array:
    :param colored_position:
    :param with_html_tag:
    :return:
    """
    tag_premise = ('<' + TextGenerator.tag_type + ' data-argumentation-type="argument">') if with_html_tag else ''
    tag_conclusion = ('<' + TextGenerator.tag_type + ' data-argumentation-type="attack">') if with_html_tag else ''
    tag_end = ('</' + TextGenerator.tag_type + '>') if with_html_tag else ''
    lang = get_lang_for_argument(arg_array[0])
    _t = Translator(lang)

    if len(arg_array) == 1:
        db_argument = DBDiscussionSession.query(Argument).filter_by(uid=arg_array[0]).first()
        premises, uids = get_text_for_premisesgroup_uid(db_argument.premisesgroup_uid)
        conclusion = get_text_for_statement_uid(db_argument.conclusion_uid)

        if lang == 'de':
            intro = _t.get(_t.rebut1) if db_argument.is_supportive else _t.get(_t.overbid1)
            ret_value = tag_conclusion + intro[0:1].upper() + intro[1:] + ' ' + conclusion + tag_end
            ret_value += ' ' + _t.get(_t.because).lower() + ' ' + tag_premise + premises + tag_end
        else:
            ret_value = tag_conclusion + conclusion + ' ' + (_t.get(_t.isNotRight).lower() if not db_argument.is_supportive else '') + tag_end
            ret_value += _t.get(_t.because).lower()
            ret_value += ' ' + tag_premise + premises + tag_end

    else:
        db_argument = DBDiscussionSession.query(Argument).filter_by(uid=arg_array[1]).first()
        conclusions_premises, uids = get_text_for_premisesgroup_uid(db_argument.premisesgroup_uid)
        conclusions_conclusion = get_text_for_statement_uid(db_argument.conclusion_uid)

        db_argument = DBDiscussionSession.query(Argument).filter_by(uid=arg_array[0]).first()
        premises, uids = get_text_for_premisesgroup_uid(db_argument.premisesgroup_uid)

        ret_value = tag_conclusion + conclusions_premises + ' '
        ret_value += _t.get(_t.doesNotJustify) + ' '
        ret_value += conclusions_conclusion + tag_end + ' '
        ret_value += _t.get(_t.because).lower() + ' ' + tag_premise + premises + tag_end

    return ret_value


def __build_single_argument(uid, rearrange_intro, with_html_tag, colored_position, attack_type, _t):
    """

    :param uid:
    :param rearrange_intro:
    :param with_html_tag:
    :param colored_position:
    :param attack_type:
    :param _t:
    :return:
    """
    db_argument = DBDiscussionSession.query(Argument).filter_by(uid=uid).first()
    premises, uids = get_text_for_premisesgroup_uid(db_argument.premisesgroup_uid)
    conclusion = get_text_for_statement_uid(db_argument.conclusion_uid)
    lang = get_lang_for_argument(uid)

    if lang != 'de':
        # conclusion = conclusion[0:1].lower() + conclusion[1:]  # pretty print
        premises = premises[0:1].lower() + premises[1:]  # pretty print

    sb_tmp = ''
    se = '</' + TextGenerator.tag_type + '>' if with_html_tag else ''
    if attack_type not in ['dont_know', 'jump']:
        sb = '<' + TextGenerator.tag_type + '>' if with_html_tag else ''
        if colored_position:
            sb = '<' + TextGenerator.tag_type + ' data-argumentation-type="position">' if with_html_tag else ''
    else:
        sb = '<' + TextGenerator.tag_type + ' data-argumentation-type="argument">'
        sb_tmp = '<' + TextGenerator.tag_type + ' data-argumentation-type="attack">'

    # color_everything = attack_type == 'undercut' and False
    # if not color_everything:
    if attack_type not in ['dont_know', 'jump']:
        if attack_type == 'undermine':
            premises = sb + premises + se
        else:
            conclusion = sb + conclusion + se
    else:
        se = '</' + TextGenerator.tag_type + '>'
        premises = sb + premises + se
        conclusion = sb_tmp + conclusion + se
    # if not color_everything:

    if lang == 'de':
        if rearrange_intro:
            intro = _t.get(_t.itTrueIsThat) if db_argument.is_supportive else _t.get(_t.itFalseIsThat)
        else:
            intro = _t.get(_t.itIsTrueThat) if db_argument.is_supportive else _t.get(_t.itIsFalseThat)

        # if color_everything:
        #     ret_value = sb + intro[0:1].upper() + intro[1:] + ' ' + conclusion + se
        # else:
        ret_value = intro[0:1].upper() + intro[1:] + ' ' + conclusion
        ret_value += ' ' + _t.get(_t.because).lower() + ' ' + premises
    else:
        tmp = sb + ' ' + _t.get(_t.isNotRight).lower() + se + ', ' + _t.get(_t.because).lower() + ' '
        ret_value = conclusion + ' '
        ret_value += _t.get(_t.because).lower() if db_argument.is_supportive else tmp
        ret_value += ' ' + premises

    # if color_everything:
    #     return sb + ret_value + se
    # else:
    return ret_value


def __build_nested_argument(arg_array, first_arg_by_user, user_changed_opinion, with_html_tag, start_with_intro, doesnt_hold_because, _t):
    """

    :param arg_array:
    :param lang:
    :param first_arg_by_user:
    :param user_changed_opinion:
    :param with_html_tag:
    :param start_with_intro:
    :param doesnt_hold_because:
    :param _t:
    :return:
    """

    # get all pgroups and at last, the conclusion
    pgroups = []
    supportive = []
    arg_array = arg_array[::-1]
    lang = get_lang_for_argument(arg_array[0])
    for uid in arg_array:
        db_argument = DBDiscussionSession.query(Argument).filter_by(uid=uid).first()
        text, tmp = get_text_for_premisesgroup_uid(db_argument.premisesgroup_uid)
        pgroups.append((text[0:1].lower() + text[1:])if lang != 'de' else text)
        supportive.append(db_argument.is_supportive)
    uid = DBDiscussionSession.query(Argument).filter_by(uid=arg_array[0]).first().conclusion_uid
    conclusion = get_text_for_statement_uid(uid)

    sb = '<' + TextGenerator.tag_type + '>' if with_html_tag else ''
    se = '</' + TextGenerator.tag_type + '>' if with_html_tag else ''
    because = (se + ', ') if lang == 'de' else (' ' + se)
    because += _t.get(_t.because).lower() + ' ' + sb

    if len(arg_array) % 2 is 0 and not first_arg_by_user:  # system starts
        ret_value = se
        ret_value += _t.get(_t.earlierYouArguedThat) if user_changed_opinion else _t.get(_t.otherUsersSaidThat)
        ret_value += sb + ' '
        users_opinion = True  # user after system
        if lang != 'de':
            conclusion = conclusion[0:1].lower() + conclusion[1:]  # pretty print
    else:  # user starts
        ret_value = (se + _t.get(_t.soYourOpinionIsThat) + ': ' + sb) if start_with_intro else ''
        users_opinion = False  # system after user
        conclusion = conclusion[0:1].upper() + conclusion[1:]  # pretty print
    ret_value += conclusion + (because if supportive[0] else doesnt_hold_because) + pgroups[0] + '.'

    for i in range(1, len(pgroups)):
        ret_value += ' ' + se
        if users_opinion:
            if user_changed_opinion:
                ret_value += _t.get(_t.otherParticipantsConvincedYouThat)
            else:
                ret_value += _t.get(_t.butYouCounteredWith)
        else:
            ret_value += _t.get(_t.otherUsersHaveCounterArgument)
        ret_value += sb + ' ' + pgroups[i] + '.'

        # if user_changed_opinion:
        # ret_value += ' ' + se + _t.get(_t.butThenYouCounteredWith) + sb + ' ' + pgroups[i] + '.'
        # else:
        # ret_value += ' ' + se + (_t.get(_t.butYouCounteredWith) if users_opinion else _t.get(_t.otherUsersHaveCounterArgument)) + sb + ' ' + pgroups[i] + '.'
        users_opinion = not users_opinion

    ret_value = ret_value.replace('.</' + TextGenerator.tag_type + '>', '</' + TextGenerator.tag_type + '>.').replace('. </' + TextGenerator.tag_type + '>', '</' + TextGenerator.tag_type + '>. ')
    return ret_value[:-1]  # cut off punctuation


def get_text_for_premisesgroup_uid(uid):
    """
    Returns joined text of the premise group and the premise ids

    :param uid: premisesgroup_uid
    :return: text, uids
    """
    db_premises = DBDiscussionSession.query(Premise).filter_by(premisesgroup_uid=uid).join(Statement).all()
    text = ''
    uids = []
    for premise in db_premises:
        lang = get_lang_for_statement(premise.statements.uid)
        _t = Translator(lang)
        tmp = get_text_for_statement_uid(premise.statements.uid)
        if lang != 'de':
            tmp[0:1].lower() + tmp[1:]
        uids.append(str(premise.statements.uid))
        text += ' ' + _t.get(_t.aand) + ' ' + tmp

    return text[5:], uids


def get_text_for_statement_uid(uid, colored_position=False):
    """
    Returns text of statement with given uid

    :param uid: Statement.uid
    :param colored_position: Boolean
    :return: String
    """
    try:
        if isinstance(int(uid), int):
            db_statement = DBDiscussionSession.query(Statement).filter_by(uid=uid).first()
            if not db_statement:
                return None

            db_textversion = DBDiscussionSession.query(TextVersion).order_by(TextVersion.uid.desc()).filter_by(
                uid=db_statement.textversion_uid).first()
            content = db_textversion.content

            while content.endswith(('.', '?', '!')):
                content = content[:-1]

            sb = '<' + TextGenerator.tag_type + ' data-argumentation-type="position">' if colored_position else ''
            se = '</' + TextGenerator.tag_type + '>' if colored_position else ''
            return sb + content + se

    except (ValueError, TypeError):
        return None


def get_text_for_conclusion(argument, start_with_intro=False, rearrange_intro=False):
    """
    Check the arguments conclusion whether it is an statement or an argument and returns the text

    :param argument: Argument
    :param lang: ui_locales
    :param start_with_intro: Boolean
    :param rearrange_intro: Boolean
    :return: String
    """
    if argument.argument_uid:
        return get_text_for_argument_uid(argument.argument_uid, start_with_intro, rearrange_intro=rearrange_intro)
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
    issue = DBDiscussionSession.query(Issue).filter_by(uid=uid).first()
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
                tmp = part.replace('/', 'X', 2).find('/') + 1
                uids.append(part[tmp])
        return uids
    except AttributeError:
        return []


def get_lang_for_argument(uid):
    """
    Return ui_locales code, if the argument exists, otherwise 'en' as fallback

    :param uid: id of the argument
    :return: ui_locales code for the discussion with the given argument
    """
    db_argument = DBDiscussionSession.query(Argument).filter_by(uid=uid).first()
    if not db_argument:
        return fallback_lang

    return get_lang_for_issue(db_argument.issue_uid)


def get_lang_for_statement(uid):
    """
    Return ui_locales code, if the statement exists, otherwise 'en' as fallback

    :param uid: id of the statement
    :return: ui_locales code for the discussion with the given statement
    """
    db_statement = DBDiscussionSession.query(Statement).filter_by(uid=uid).first()
    if not db_statement:
        return fallback_lang

    return get_lang_for_issue(db_statement.issue_uid)


def get_lang_for_issue(uid):
    """
    Return ui_locales code, if the issue exists, otherwise 'en' as fallback

    :param uid: id of the issue
    :return: ui_locales code for the discussion with the given issue
    """
    db_issue = DBDiscussionSession.query(Issue).filter_by(uid=uid).first()
    if not db_issue:
        return fallback_lang

    db_lang = DBDiscussionSession.query(Language).filter_by(uid=db_issue.lang_uid).first()
    if not db_lang:
        return fallback_lang

    return db_lang.ui_locales


def get_user_by_private_or_public_nickname(nickname):
    """
    Gets the user by his (public) nickname, based on the option, whether his nickname is public or not

    :param nickname: Nickname of the user
    :return: Current user or None
    """
    db_user = DBDiscussionSession.query(User).filter_by(nickname=nickname).first()
    db_public_user = DBDiscussionSession.query(User).filter_by(public_nickname=nickname).first()

    db_settings = None
    current_user = None

    if db_user:
        db_settings = DBDiscussionSession.query(Settings).filter_by(author_uid=db_user.uid).first()
    elif db_public_user:
        db_settings = DBDiscussionSession.query(Settings).filter_by(author_uid=db_public_user.uid).first()

    if db_settings:
        if db_settings.should_show_public_nickname and db_user:
            current_user = db_user
        elif not db_settings.should_show_public_nickname and db_public_user:
            current_user = db_public_user

    return current_user
