"""
Provides helping function for the managing reputation.

.. codeauthor:: Tobias Krauthoff <krauthoff@cs.uni-duesseldorf.de
"""

from dbas.database import DBDiscussionSession
from dbas.database.discussion_model import User, ReviewDelete, LastReviewerDelete, ReviewOptimization, \
    LastReviewerOptimization, ReviewEdit, LastReviewerEdit, OptimizationReviewLocks, get_now
from dbas.review.helper.reputation import get_reputation_of
from dbas.review.helper.subpage import reputation_borders
from dbas.lib import get_profile_picture, is_user_author
from sqlalchemy import and_
from dbas.logger import logger

max_lock_time_in_sec = 180


def get_review_queues_as_lists(main_page, translator, nickname):
    """
    Prepares dictionary for the edit section.

    :param main_page: URL
    :param translator: Translator
    :param nickname: Users nickname
    :return: Array
    """
    logger('ReviewQueues', 'get_review_queues_as_lists', 'main')
    db_user = DBDiscussionSession.query(User).filter_by(nickname=nickname).first()
    if not db_user:
        return None

    review_list = list()
    review_list.append(__get_delete_dict(main_page, translator, nickname))
    review_list.append(__get_optimization_dict(main_page, translator, nickname))
    review_list.append(__get_edit_dict(main_page, translator, nickname))
    if is_user_author(nickname):
        review_list.append(__get_history_dict(main_page, translator))
        review_list.append(__get_ongoing_dict(main_page, translator))

    return review_list


def __get_delete_dict(main_page, translator, nickname):
    """
    Prepares dictionary for the a section.

    :param main_page: URL
    :param translator: Translator
    :param nickname: Users nickname
    :return: Dict()
    """
    #  logger('ReviewQueues', '__get_delete_dict', 'main')
    task_count = __get_review_count_for(ReviewDelete, LastReviewerDelete, nickname)

    key = 'deletes'
    count, all_rights = get_reputation_of(nickname)
    tmp_dict = {'task_name': 'Deletes',
                'id': 'deletes',
                'url': main_page + '/review/' + key,
                'icon': 'fa fa-trash-o',
                'task_count': task_count,
                'is_allowed': count >= reputation_borders[key] or all_rights,
                'is_allowed_text': translator.get(translator.visitDeleteQueue),
                'is_not_allowed_text': translator.get(translator.visitDeleteQueueLimitation).replace('XX', str(reputation_borders[key])),
                'last_reviews': __get_last_reviewer_of(LastReviewerDelete, main_page)
                }
    return tmp_dict


def __get_optimization_dict(main_page, translator, nickname):
    """
    Prepares dictionary for the a section.

    :param main_page: URL
    :param translator: Translator
    :param nickname: Users nickname
    :return: Dict()
    """
    #  logger('ReviewQueues', '__get_optimization_dict', 'main')
    task_count = __get_review_count_for(ReviewOptimization, LastReviewerOptimization, nickname)

    key = 'optimizations'
    count, all_rights = get_reputation_of(nickname)
    tmp_dict = {'task_name': 'Optimizations',
                'id': 'optimizations',
                'url': main_page + '/review/' + key,
                'icon': 'fa fa-flag',
                'task_count': task_count,
                'is_allowed': count >= reputation_borders[key] or all_rights,
                'is_allowed_text': translator.get(translator.visitOptimizationQueue),
                'is_not_allowed_text': translator.get(translator.visitOptimizationQueueLimitation).replace('XX', str(reputation_borders[key])),
                'last_reviews': __get_last_reviewer_of(LastReviewerOptimization, main_page)
                }
    return tmp_dict


def __get_edit_dict(main_page, translator, nickname):
    """
    Prepares dictionary for the a section.

    :param main_page: URL
    :param translator: Translator
    :param nickname: Users nickname
    :return: Dict()
    """
    #  logger('ReviewQueues', '__get_edit_dict', 'main')
    task_count = __get_review_count_for(ReviewEdit, LastReviewerEdit, nickname)

    key = 'edits'
    count, all_rights = get_reputation_of(nickname)
    tmp_dict = {'task_name': 'Edits',
                'id': 'edits',
                'url': main_page + '/review/' + key,
                'icon': 'fa fa-pencil-square-o',
                'task_count': task_count,
                'is_allowed': count >= reputation_borders[key] or all_rights,
                'is_allowed_text': translator.get(translator.visitEditQueue),
                'is_not_allowed_text': translator.get(translator.visitEditQueueLimitation).replace('XX', str(reputation_borders[key])),
                'last_reviews': __get_last_reviewer_of(LastReviewerEdit, main_page)
                }
    return tmp_dict


def __get_history_dict(main_page, translator):
    """
    Prepares dictionary for the a section. Queue should be added iff the user is author!

    :param main_page: URL
    :param translator: Translator
    :return: Dict()
    """
    #  logger('ReviewQueues', '__get_history_dict', 'main')
    key = 'history'
    tmp_dict = {'task_name': 'History',
                'id': 'flags',
                'url': main_page + '/review/' + key,
                'icon': 'fa fa-history',
                'task_count': '-',
                'is_allowed': True,
                'is_allowed_text': translator.get(translator.visitHistoryQueue),
                'is_not_allowed_text': '',
                'last_reviews': list()
                }
    return tmp_dict


def __get_ongoing_dict(main_page, translator):
    """
    Prepares dictionary for the a section. Queue should be added iff the user is author!

    :param main_page: URL
    :param translator: Translator
    :return: Dict()
    """
    #  logger('ReviewQueues', '__get_ongoing_dict', 'main')
    key = 'ongoing'
    tmp_dict = {'task_name': 'Ongoing',
                'id': 'flags',
                'url': main_page + '/review/' + key,
                'icon': 'fa fa-clock-o',
                'task_count': '-',
                'is_allowed': True,
                'is_allowed_text': translator.get(translator.visitOngoingQueue),
                'is_not_allowed_text': '',
                'last_reviews': list()
                }
    return tmp_dict


def __get_review_count_for(review_type, last_reviewer_type, nickname):
    """
    Returns the count of reviews of *review_type* for the user with *nickname*, whereby all reviewed data
    of *last_reviewer_type* is not observed

    :param review_type: ReviewEdit, ReviewOptimization or ...
    :param last_reviewer_type: LastReviewerEdit, LastReviewer...
    :param nickname: Users nickname
    :return: Integer
    """
    #  logger('ReviewQueues', '__get_review_count_for', 'main')
    db_user = DBDiscussionSession.query(User).filter_by(nickname=nickname).first()
    if not db_user:
        db_reviews = DBDiscussionSession.query(review_type).filter_by(is_executed=False).all()
        return len(db_reviews)

    # get all reviews but filter reviews, which
    # - the user has detected
    # - the user has reviewed
    db_last_reviews_of_user = DBDiscussionSession.query(last_reviewer_type).filter_by(reviewer_uid=db_user.uid).all()
    already_reviewed = []
    for last_review in db_last_reviews_of_user:
        already_reviewed.append(last_review.review_uid)
    db_reviews = DBDiscussionSession.query(review_type).filter(and_(review_type.is_executed == False,
                                                                    review_type.detector_uid != db_user.uid))

    if len(already_reviewed) > 0:
        db_reviews = db_reviews.filter(~review_type.uid.in_(already_reviewed))
    db_reviews = db_reviews.all()

    return len(db_reviews)


def __get_last_reviewer_of(reviewer_type, main_page):
    """
    Returns a list with the last reviewers of the given type. Multiple reviewers are filtered

    :param reviewer_type:
    :param main_page:
    :return:
    """
    #  logger('ReviewQueues', '__get_last_reviewer_of', 'main')
    users_array = list()
    db_reviews = DBDiscussionSession.query(reviewer_type).order_by(reviewer_type.uid.desc()).all()
    limit = min(5, len(db_reviews))
    index = 0
    while index < limit:
        db_review = db_reviews[index]
        db_user = DBDiscussionSession.query(User).filter_by(uid=db_review.reviewer_uid).first()
        if db_user:
            tmp_dict = dict()
            tmp_dict['img_src'] = get_profile_picture(db_user, 40)
            tmp_dict['url'] = main_page + '/user/' + db_user.get_global_nickname()
            tmp_dict['name'] = db_user.get_global_nickname()
            # skip it, if it is already in
            if tmp_dict in users_array:
                limit += 1 if len(db_reviews) > limit else 0
            else:
                users_array.append(tmp_dict)
        else:
            limit += 1 if len(db_reviews) > limit else 0
        index += 1
    return users_array


def lock_optimization_review(nickname, review_uid, translator, transaction):
    """

    :param nickname:
    :param review_uid:
    :param translator:
    :param transaction:
    :return:
    """
    logger('ReviewQueues', 'lock', 'main')
    success = ''
    info = ''
    error = ''
    is_locked = False

    # has user already locked an item?
    db_user  = DBDiscussionSession.query(User).filter_by(nickname=nickname).first()

    if not db_user or int(review_uid) < 1:
        error = translator.get(translator.internalKeyError)
        return success, info, error, is_locked

    # check if author locked an item and maybe tidy up old locks
    db_locks = DBDiscussionSession.query(OptimizationReviewLocks).filter_by(author_uid=db_user.uid).first()
    if db_locks:
        if is_review_locked(db_locks.review_optimization_uid):
            info = translator.get(translator.dataAlreadyLockedByYou)
            is_locked = True
            return success, info, error, is_locked
        else:
            DBDiscussionSession.query(OptimizationReviewLocks).filter_by(author_uid=db_user.uid).delete()

    # is already locked?
    if is_review_locked(review_uid):
        info = translator.get(translator.dataAlreadyLockedByOthers)
        is_locked = True
        return success, info, error, is_locked

    DBDiscussionSession.add(OptimizationReviewLocks(db_user.uid, review_uid))
    DBDiscussionSession.flush()
    transaction.commit()
    is_locked = True

    return success, info, error, is_locked


def unlock_optimization_review(review_uid, transaction):
    """

    :param review_uid:
    :param transaction:
    :return:
    """
    tidy_up_optimization_locks()
    logger('ReviewQueues', 'unlock_optimization_review', 'main')
    DBDiscussionSession.query(OptimizationReviewLocks).filter_by(review_optimization_uid=review_uid).delete()
    DBDiscussionSession.flush()
    transaction.commit()
    return True


def is_review_locked(review_uid):
    """

    :param review_uid:
    :return:
    """
    tidy_up_optimization_locks()
    logger('ReviewQueues', 'is_review_locked', 'main')
    db_lock = DBDiscussionSession.query(OptimizationReviewLocks).filter_by(review_optimization_uid=review_uid).first()
    if not db_lock:
        return False
    return (get_now() - db_lock.locked_since).seconds < max_lock_time_in_sec


def tidy_up_optimization_locks():
    """

    :return:
    """
    logger('ReviewQueues', 'tidy_up_optimization_locks', 'main')
    db_locks = DBDiscussionSession.query(OptimizationReviewLocks).all()
    for lock in db_locks:
        if (get_now() - lock.locked_since).seconds >= max_lock_time_in_sec:
            DBDiscussionSession.query(OptimizationReviewLocks).filter_by(review_optimization_uid=lock.review_optimization_uid).delete()