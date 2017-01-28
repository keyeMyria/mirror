"""
Provides helping function for creating the history as bubbles.

.. codeauthor: Tobias Krauthoff <krauthoff@cs.uni-duesseldorf.de
"""

import transaction
from dbas.database import DBDiscussionSession
from dbas.database.discussion_model import Argument, Statement, User, History, Settings, sql_timestamp_pretty_print, Issue
from dbas.input_validator import check_reaction
from dbas.lib import create_speechbubble_dict, get_text_for_argument_uid, get_text_for_statement_uid,\
    get_text_for_premisesgroup_uid, get_text_for_conclusion
from dbas.logger import logger
from dbas.strings.keywords import Keywords as _
from dbas.strings.text_generator import tag_type, get_text_for_confrontation
from dbas.strings.translator import Translator
from dbas.database.initializedb import nick_of_anonymous_user


def save_issue_uid(issue_uid, nickname):
    """

    :param issue_uid:
    :param nickname:
    :return:
    """
    db_user = DBDiscussionSession.query(User).filter_by(nickname=nickname).first()
    if not db_user:
        return False

    db_settings = DBDiscussionSession.query(Settings).get(db_user.uid)
    if not db_settings:
        return False

    db_settings.set_last_topic_uid(issue_uid)
    transaction.commit()


def get_saved_issue(nickname):
    """

    :param nickname:
    :return:
    """
    db_user = DBDiscussionSession.query(User).filter_by(nickname=nickname).first()
    if not db_user:
        return 0

    db_settings = DBDiscussionSession.query(Settings).get(db_user.uid)
    if not db_settings:
        return 0

    val = db_settings.last_topic_uid
    db_issue = DBDiscussionSession.query(Issue).get(val)
    if not db_issue:
        return 0
    return 0 if db_issue.is_disabled else val


def get_splitted_history(history):
    """
    Splits history by specific keyword and removes leading '/'

    :param history: String
    :return: [String]
    """
    history = history.split('-')
    tmp = []
    for h in history:
        tmp.append(h[1:] if h[0:1] == '/' else h)

    return tmp


def create_bubbles_from_history(history, nickname='', lang='', application_url='', slug=''):
    """
    Creates the bubbles for every history step

    :param history: String
    :param nickname: User.nickname
    :param lang: ui_locales
    :param application_url: String
    :param slug: String
    :return: Array
    """
    if len(history) == 0:
        return []

    logger('history_helper', 'create_bubbles_from_history', 'nickname: ' + str(nickname) + ', history: ' + history)
    splitted_history = get_splitted_history(history)

    bubble_array = []
    consumed_history = ''

    nickname = nickname if nickname else nick_of_anonymous_user

    for index, step in enumerate(splitted_history):
        url = application_url + '/discuss/' + slug + '/' + step
        if len(consumed_history) != 0:
            url += '?history=' + consumed_history
        consumed_history += step if len(consumed_history) == 0 else '-' + step

        if 'justify/' in step:
            __prepare_justify_statement_step(bubble_array, index, step, nickname, lang, url)

        elif 'reaction/' in step:
            __prepare_reaction_step(bubble_array, index, application_url, step, nickname, lang, splitted_history, url)

        else:
            logger('history_helper', 'create_bubbles_from_history', str(index) + ': unused case -> ' + step)

    return bubble_array


def __prepare_justify_statement_step(bubble_array, index, step, nickname, lang, url):
    logger('history_helper', '__prepare_justify_statement_step', str(index) + ': justify case -> ' + step)
    steps = step.split('/')
    mode = steps[2]
    relation = steps[3] if len(steps) > 3 else ''

    if [c for c in ('t', 'f') if c in mode] and relation == '':
        bubbles = __get_bubble_from_justify_statement_step(step, nickname, lang, url)
        if bubbles:
            bubble_array += bubbles

    elif 'd' in mode and relation == '':
        bubbles = __get_bubble_from_dont_know_step(step, nickname, lang, url)
        if bubbles:
            bubble_array += bubbles


def __prepare_reaction_step(bubble_array, index, application_url, step, nickname, lang, splitted_history, url):
    logger('history_helper', '__prepare_reaction_step', str(index) + ': reaction case -> ' + step)
    bubbles = __get_bubble_from_reaction_step(application_url, step, nickname, lang, splitted_history, url)
    if bubbles:
        bubble_array += bubbles


def __get_bubble_from_justify_statement_step(step, nickname, lang, url):
    """
    Creates bubbles for the justify-keyword for an statement.

    :param step: String
    :param nickname: User.nickname
    :param lang: ui_locales
    :param url: String
    :return: [dict()]
    """
    logger('history_helper', '__justify_statement_step', 'def')
    steps = step.split('/')
    uid = int(steps[1])
    #  slug    = ''
    is_supportive = steps[2] == 't' or steps[2] == 'd'  # supportive = t(rue) or d(ont know) mode

    _tn = Translator(lang)
    #  url     = UrlManager(application_url, slug).get_slug_url(False)
    if lang == 'de':
        intro = _tn.get(_.youAgreeWith if is_supportive else _.youDisagreeWith) + ' '
    else:
        intro = '' if is_supportive else _tn.get(_.youDisagreeWith) + ': '
    text = get_text_for_statement_uid(uid)
    if lang != 'de':
        text = text[0:1].upper() + text[1:]

    msg = intro + '<' + tag_type + '>' + text + '</' + tag_type + '>'
    bubbsle_user = create_speechbubble_dict(is_user=True, message=msg, omit_url=False, statement_uid=uid,
                                            is_supportive=is_supportive, nickname=nickname, lang=lang, url=url)
    return [bubbsle_user]


def __get_bubble_from_attitude_step(step, nickname, lang, url):
    """
    Creates bubbles for the attitude-keyword for an statement.

    :param step: String
    :param nickname: User.nickname
    :param lang: ui_locales
    :param url: String
    :return: [dict()]
    """
    logger('history_helper', '__attitude_step', 'def')
    steps = step.split('/')
    uid = int(steps[1])
    text = get_text_for_statement_uid(uid)
    if lang != 'de':
        text = text[0:1].upper() + text[1:]
    bubble = create_speechbubble_dict(is_user=True, message=text, omit_url=False, statement_uid=uid, nickname=nickname,
                                      lang=lang, url=url)

    return [bubble]


def __get_bubble_from_dont_know_step(step, nickname, lang, url):
    """
    Creates bubbles for the dont-know-reaction for a statement.

    :param step: String
    :param nickname: User.nickname
    :param lang: ui_locales
    :param url: String
    :return: [dict()]
    """
    steps = step.split('/')
    uid = int(steps[1])

    text = get_text_for_argument_uid(uid, rearrange_intro=True, attack_type='dont_know', with_html_tag=False,
                                     start_with_intro=True)
    db_argument = DBDiscussionSession.query(Argument).get(uid)
    if not db_argument:
        text = ''

    from dbas.strings.text_generator import get_name_link_of_arguments_author
    _tn = Translator(lang)

    author, gender, is_okay = get_name_link_of_arguments_author(url, db_argument, nickname, False)
    if is_okay:
        intro = author + ' ' + _tn.get(_.thinksThat)
    else:
        intro = _tn.get(_.otherParticipantsThinkThat)
    sys_text = intro + ' ' + text[0:1].lower() + text[1:] + '. '
    sys_text += '<br><br>' + _tn.get(_.whatDoYouThinkAboutThat) + '?'
    sys_bubble = create_speechbubble_dict(is_system=True, message=sys_text, nickname=nickname)

    text = _tn.get(_.showMeAnArgumentFor) + (' ' if lang == 'de' else ': ') + get_text_for_conclusion(db_argument)
    user_bubble = create_speechbubble_dict(is_user=True, message=text, nickname=nickname)

    return [user_bubble, sys_bubble]


def __get_bubble_from_reaction_step(main_page, step, nickname, lang, splitted_history, url):
    """
    Creates bubbles for the reaction-keyword.

    :param step: String
    :param nickname: User.nickname
    :param lang: ui_locales
    :param splitted_history: [String].uid
    :param url: String
    :return: [dict()]
    """
    logger('history_helper', '__reaction_step', 'def: ' + str(step) + ', ' + str(splitted_history))
    steps = step.split('/')
    uid = int(steps[1])
    additional_uid = int(steps[3])
    attack = steps[2]

    if not check_reaction(uid, additional_uid, attack, is_history=True):
        return None

    is_supportive = DBDiscussionSession.query(Argument).get(uid).is_supportive
    last_relation = splitted_history[-1].split('/')[2]

    user_changed_opinion = len(splitted_history) > 1 and '/undercut/' in splitted_history[-2]
    support_counter_argument = False
    if step in splitted_history:
        index = splitted_history.index(step)
        try:
            support_counter_argument = 'reaction' in splitted_history[index - 1]
        except IndexError:
            support_counter_argument = False
    current_argument = get_text_for_argument_uid(uid, user_changed_opinion=user_changed_opinion,
                                                 support_counter_argument=support_counter_argument)
    db_argument = DBDiscussionSession.query(Argument).get(uid)
    db_confrontation = DBDiscussionSession.query(Argument).get(additional_uid)
    if db_argument.conclusion_uid is not None:
        db_statement = DBDiscussionSession.query(Statement).get(db_argument.conclusion_uid)
        reply_for_argument = not (db_statement and db_statement.is_startpoint)
    else:
        reply_for_argument = True

    premise, tmp = get_text_for_premisesgroup_uid(db_argument.premisesgroup_uid)
    conclusion = get_text_for_conclusion(db_argument)
    sys_conclusion = get_text_for_conclusion(db_confrontation)
    confr, tmp = get_text_for_premisesgroup_uid(db_confrontation.premisesgroup_uid)
    user_is_attacking = not db_argument.is_supportive

    if lang != 'de':
        current_argument = current_argument[0:1].upper() + current_argument[1:]
    premise = premise[0:1].lower() + premise[1:]

    _tn = Translator(lang)
    user_text = (_tn.get(_.otherParticipantsConvincedYouThat) + ': ') if last_relation == 'support' else ''
    user_text += '<' + tag_type + '>'
    user_text += current_argument if current_argument != '' else premise
    user_text += '</' + tag_type + '>.'
    sys_text, tmp = get_text_for_confrontation(main_page, lang, nickname, premise, conclusion, sys_conclusion, is_supportive,
                                               attack, confr, reply_for_argument, user_is_attacking, db_argument,
                                               db_confrontation, color_html=False)

    bubble_user = create_speechbubble_dict(is_user=True, message=user_text, omit_url=False, argument_uid=uid,
                                           is_supportive=is_supportive, nickname=nickname, lang=lang, url=url)
    if attack == 'end':
        bubble_syst = create_speechbubble_dict(is_system=True, message=sys_text, omit_url=True, nickname=nickname,
                                               lang=lang)
    else:
        bubble_syst = create_speechbubble_dict(is_system=True, uid='question-bubble-' + str(additional_uid),
                                               message=sys_text, omit_url=True, nickname=nickname, lang=lang)
    return [bubble_user, bubble_syst]


def save_history_in_cookie(request, path, history):
    """
    Saves history + new path in cookie

    :param request: request
    :param path: String
    :param history: String
    :return: none
    """
    if path.startswith('/discuss/'):
        path = path[len('/discuss/'):]
        path = path[path.index('/') if '/' in path else 0:]
        request.response.set_cookie('_HISTORY_', history + '-' + path)


def save_path_in_database(nickname, path):
    """
    Saves a path into the database

    :param nickname: User.nickname
    :param path: String
    :return: Boolean
    """

    if path.startswith('/discuss/'):
        path = path[len('/discuss/'):]
        path = path[path.index('/') if '/' in path else 0:]

    if not nickname:
        return []

    db_user = DBDiscussionSession.query(User).filter_by(nickname=nickname).first()
    if not db_user:
        return []

    DBDiscussionSession.add(History(author_uid=db_user.uid, path=path))
    DBDiscussionSession.flush()
    # transaction.commit()  # 207


def get_history_from_database(nickname, lang):
    """
    Returns history from database

    :param nickname: User.nickname
    :param lang: ui_locales
    :return: [String]
    """
    db_user = DBDiscussionSession.query(User).filter_by(nickname=nickname if nickname else '').first()
    if not nickname or not db_user:
        return []

    db_history = DBDiscussionSession.query(History).filter_by(author_uid=db_user.uid).all()
    return_array = []
    for history in db_history:
        return_array.append({'path': history.path,
                             'timestamp': sql_timestamp_pretty_print(history.timestamp, lang, False, True) + ' GMT'})

    return return_array


def delete_history_in_database(nickname):
    """
    Deletes history from database

    :param nickname: User.nickname
    :return: [String]
    """
    db_user = DBDiscussionSession.query(User).filter_by(nickname=nickname if nickname else '').first()
    if not nickname or not db_user:
        return []
    DBDiscussionSession.query(History).filter_by(author_uid=db_user.uid).delete()
    DBDiscussionSession.flush()
    transaction.commit()
