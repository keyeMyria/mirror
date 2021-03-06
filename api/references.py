"""
Handle references from other websites, prepare, store and load them into D-BAS.

.. codeauthor:: Christian Meter <meter@cs.uni-duesseldorf.de
"""

import transaction
from api.extractor import extract_reference_information, extract_author_information, extract_issue_information
from dbas.database import DBDiscussionSession
from dbas.database.discussion_model import StatementReferences, User, Issue, TextVersion
from dbas.lib import resolve_issue_uid_to_slug, get_all_arguments_with_text_by_statement_id
from dbas.helper.url import UrlManager

from .lib import escape_html, logger

log = logger()


def url_to_statement(issue_uid, statement_uid, agree=True):
    """
    Generate URL to given statement_uid in specific issue (by slug).
    Used to directly jump into the discussion.

    :param issue_uid: uid of current issue
    :type issue_uid: id
    :param statement_uid: Statement id to generate the link to
    :type statement_uid: int
    :param agree: Indicate (dis-)agreement with a statement
    :type agree: boolean
    :return: direct URL to jump to the provided statement
    :rtype: str
    """
    if isinstance(agree, str):
        if agree == "true":
            mode = "agree"
        else:
            mode = "disagree"
    else:
        mode = "agree" if agree is True else "disagree"
    slug = resolve_issue_uid_to_slug(issue_uid)
    url_manager = UrlManager(slug=slug)
    return "api/" + url_manager.get_url_for_justifying_statement(statement_uid, mode)


def prepare_single_reference(ref):
    """
    Given a StatementReference database-object extract information and generate a URL for it.
    Then prepare a dict and return it.

    :param ref: single Reference
    :type ref: StatementReferences
    :return: dictionary with some prepared fields of a reference
    :rtype: dict
    """
    if ref:
        url = url_to_statement(ref.issue_uid, ref.statement_uid)
        return {"uid": ref.uid, "text": ref.reference, "url": url}


def store_reference(api_data, statement_uid=None):
    """
    Validate provided reference and store it in the database.
    Has side-effects.

    .. todo::
        Remove parameter discuss_url and calculate here the correct url

    :param api_data: user provided data
    :param statement_uid: the statement the reference should be assigned to
    :return:
    """
    try:
        reference = api_data["reference"]
        if not reference:
            return  # Early exit if there is no reference
        if not statement_uid:
            log.error("[API/Reference] No statement_uid provided.")
            return

        user_uid = api_data["user_uid"]
        host = escape_html(api_data["host"])
        path = escape_html(api_data["path"])
        issue_uid = api_data["issue_id"]

        db_ref = StatementReferences(escape_html(reference), host, path, user_uid, statement_uid, issue_uid)
        DBDiscussionSession.add(db_ref)
        DBDiscussionSession.flush()
        transaction.commit()
        return db_ref
    except KeyError as e:
        log.error("[API/Reference] KeyError: could not access field in api_data. " + repr(e))


# =============================================================================
# Getting references from database
# =============================================================================

def get_complete_reference(ref_id=None):
    """
    Given a reference uid, query all interesting information and retrieve the database objects.

    :param ref_id: StatementReference.uid
    :return: reference, user, issue
    :rtype: tuple
    """
    if ref_id:
        reference = DBDiscussionSession.query(StatementReferences).get(ref_id)
        user = DBDiscussionSession.query(User).get(reference.author_uid)
        issue = DBDiscussionSession.query(Issue).get(reference.issue_uid)
        textversion = DBDiscussionSession.query(TextVersion).get(reference.statement_uid)
        return reference, user, issue, textversion


def get_all_references_by_reference_text(ref_text=None):
    """
    Query database for all occurrences of a given reference text. Prepare list with information about
    used issue, author and a url to the statement.

    :param ref_text: Reference text
    :return: list of used references
    """
    if ref_text:
        refs = list()
        matched = DBDiscussionSession.query(StatementReferences).filter_by(reference=ref_text).all()
        for reference in matched:
            user = DBDiscussionSession.query(User).get(reference.author_uid)
            issue = DBDiscussionSession.query(Issue).get(reference.issue_uid)
            textversion = DBDiscussionSession.query(TextVersion).get(reference.statement_uid)
            statement_url = url_to_statement(issue.uid, reference.statement_uid)
            refs.append({"reference": extract_reference_information(reference),
                         "author": extract_author_information(user),
                         "issue": extract_issue_information(issue),
                         "arguments": get_all_arguments_with_text_by_statement_id(reference.statement_uid),
                         "statement": {"uid": reference.statement_uid,
                                       "url": statement_url,
                                       "text": textversion.content}})
        return refs


def get_references_for_url(host=None, path=None):
    """
    Query database for given URL and return all references.

    :param host: sanitized string of the reference's host
    :type host: str
    :param path: path to article / reference on reference's host
    :type path: str
    :return: list of strings representing quotes from the given site, which were stored in our database
    :rtype: list
    """
    if host and path:
        return DBDiscussionSession.query(StatementReferences).filter_by(host=host, path=path).all()


def get_reference_by_id(ref_id=None):
    """
    Query database to get a reference by its id.

    :param ref_id: StatementReferences.uid
    :return: StatementReference
    """
    if ref_id:
        return DBDiscussionSession.query(StatementReferences).get(ref_id)
