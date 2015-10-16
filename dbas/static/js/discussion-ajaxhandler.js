/*global $, jQuery, alert, GuiHandler, InteractionHandler, internal_error, popupErrorDescriptionId */

/**
 * @author Tobias Krauthoff
 * @email krauthoff@cs.uni-duesseldorf.de
 * @copyright Krauthoff 2015
 */

// Todo: replace JSON.stringify(err)

function AjaxSiteHandler() {
	'use strict';
	var push=0,
		loca=0,
		hash=0,
		aler=0;

	/**
	 * Redirection before an ajax call
	 * @param uid current identifier
	 */
	this.callSiteForGetPremisseForStatement = function (uid) {
		this.redirectBrowser('uid=' + uid, attrGetPremissesForStatement);
	};

	/**
	 * Redirection before an ajax call
	 * @param pgroup_id
	 * @param conclusion_id
	 */
	this.callSiteForGetReplyForPremisseGroup = function (pgroup_id, conclusion_id) {
		this.redirectBrowser('pgroup_id=' + pgroup_id + '&conclusion_id=' + conclusion_id, attrReplyForPremissegroup);
	};

	/**
	 * Redirection before an ajax callpgroup_id
	 * @param id_text
	 * @param pgroup_id
	 */
	this.callSiteForGetReplyForArgument = function (id_text, pgroup_id) {
		this.redirectBrowser('id_text=' + id_text + '&pgroup_id=' + pgroup_id, attrReplyForArgument);
	};

	/**
	 * Redirection before an ajax call
	 * @param id current identifier
	 * @param relation
	 * @param confrontation_uid
	 */
	this.callSiteForHandleReplyForResponseOfConfrontation = function (id, relation, confrontation_uid) {
		this.redirectBrowser('id=' + id + '&relation=' + relation + '&confrontation=' + confrontation_uid, attrReplyForResponseOfConfrontation);
	};

	/**
	 * Redirection before an ajax call
	 * @param keyValuePair current key value pair
	 * @param service current service
	 */
	this.redirectBrowser = function (keyValuePair, service) {
		var issue = new Helper().getCurrentIssueId();
		window.location.href = mainpage + 'discussion/' + keyValuePair + '&issue=' + issue + '/' + service + '/' + attrGo;
	};

	/**
	 *
	 * @param data
	 * @param url
	 * @param settings_data
	 */
	this.debugger = function (data, url, settings_data) {
		if (hash==1) window.location = '/' + url + '?' + settings_data;
		if (loca==1) window.location = '/content/' + url + '?' + settings_data;
		if (push==1) history.pushState(data, '', document.location);
		if (aler==1) alert('AJAX\n' + url + '/' + settings_data);
	};

	/**
	 * Send an ajax request for getting all positions as dicitonary uid <-> value
	 * @param issue_id
	 */
	this.getStartStatements = function (issue_id) {
		var csrfToken = $('#' + hiddenCSRFTokenId).val(), settings_data, url;
		$.ajax({
			url: 'ajax_get_start_statements',
			type: 'GET',
			data: {
				issue: issue_id
			},
			dataType: 'json',
			async: true,
			headers: {
				'X-CSRF-Token': csrfToken
			},
			beforeSend: function(jqXHR, settings ){
				settings_data = settings.data;
				url = this.url;
			}
		}).done(function ajaxGetAllPositionsDone(data) {
			new InteractionHandler().callbackIfDoneForGetStartStatements(data);
			new AjaxSiteHandler().debugger(data, url, settings_data);
		}).fail(function ajaxGetAllPositionsFail(err) {
			new GuiHandler().setErrorDescription(internal_error);
			// new GuiHandler().showDiscussionError('Internal failure, could not find any start point.');
			new GuiHandler().showDiscussionError(JSON.stringify(err));
		});
	};

	/**
	 * Send an ajax request for getting all premisses for a givens tatement
	 * @param params of clicked statement
	 */
	this.getPremisseForStatement = function (params) {
		var csrfToken = $('#' + hiddenCSRFTokenId).val(), settings_data, url;
		params = params.split('&');
		$.ajax({
			url: 'ajax_get_premisses_for_statement',
			method: 'POST',
			data: {
				uid: params[0], issue: params[1]
			},
			dataType: 'json',
			async: true,
			headers: {
				'X-CSRF-Token': csrfToken
			},
			beforeSend: function(jqXHR, settings ){
				settings_data = settings.data;
				url = this.url;
			}
		}).done(function ajaxGetPremisseForStatementDone(data) {
			new InteractionHandler().callbackIfDoneForPremisseForStatement(data);
			new AjaxSiteHandler().debugger(data, url, settings_data);
		}).fail(function ajaxGetPremisseForStatementFail(err) {
			new GuiHandler().setErrorDescription(internal_error);
			// new GuiHandler().showDiscussionError('Internal failure while requesting data for your statement.');
			new GuiHandler().showDiscussionError(JSON.stringify(err));
		});
	};

	/**
	 * Sends an ajax request for getting all premisses for a given statement
	 * @param params of clicked statement
	 */
	this.getReplyForPremisseGroup = function (params) {
		var csrfToken = $('#' + hiddenCSRFTokenId).val(), settings_data, url;
		params = params.split('&');
		$.ajax({
			url: 'ajax_reply_for_premissegroup',
			method: 'POST',
			data: {
				pgroup: params[0], conclusion: params[1], issue: params[2]
			},
			dataType: 'json',
			async: true,
			headers: {
				'X-CSRF-Token': csrfToken
			},
			beforeSend: function(jqXHR, settings ){
				settings_data = settings.data;
				url = this.url;
			}
		}).done(function ajaxGetReplyForPremisseDone(data) {
			new InteractionHandler().callbackIfDoneReplyForPremissegroup(data);
			new AjaxSiteHandler().debugger(data, url, settings_data);
		}).fail(function ajaxGetReplyForPremisseFail(err) {
			new GuiHandler().setErrorDescription(internal_error);
			// new GuiHandler().showDiscussionError('Internal failure while requesting another opininion.');
			new GuiHandler().showDiscussionError(JSON.stringify(err));
		});
	};

	/**
	 * Sends an ajax request for getting all confrotations for a given argument
	 * @param params of the clicked premisse group
	 */
	this.getReplyForArgument = function (params) {
		var csrfToken = $('#' + hiddenCSRFTokenId).val(), settings_data, url;
		params = params.split('&');
		$.ajax({
			url: 'ajax_reply_for_argument',
			method: 'POST',
			data: {
				id_text: params[0], pgroup: params[1], issue: params[2]
			},
			dataType: 'json',
			async: true,
			headers: {
				'X-CSRF-Token': csrfToken
			},
			beforeSend: function(jqXHR, settings ){
				settings_data = settings.data;
				url = this.url;
			}
		}).done(function ajaxGetReplyForArgumentDone(data) {
			new InteractionHandler().callbackIfDoneReplyForArgument(data);
			new AjaxSiteHandler().debugger(data, url, settings_data);
		}).fail(function ajaxGetReplyForArgumentFail(err) {
			new GuiHandler().setErrorDescription(internal_error);
			// new GuiHandler().showDiscussionError('Internal failure while requesting another opininion.');
			new GuiHandler().showDiscussionError(JSON.stringify(err));
		});
	};

	/**
	 * Sends an ajax request for handle the reaction of a confrontation
	 * @param params of clicked relation and statement
	 */
	this.handleReplyForResponseOfConfrontation = function (params) {
		var csrfToken = $('#' + hiddenCSRFTokenId).val(), settings_data, url;
		params = params.split('&');
		$.ajax({
			url: 'ajax_reply_for_response_of_confrontation',
			method: 'POST',
			data: {
				id: params[0], relation: params[1], confrontation: params[2], issue: params[3]
			},
			dataType: 'json',
			async: true,
			headers: {
				'X-CSRF-Token': csrfToken
			},
			beforeSend: function(jqXHR, settings ){
				settings_data = settings.data;
				url = this.url;
			}
		}).done(function ajaxHandleReplyForResponseOfConfrontationDone(data) {
			new InteractionHandler().callbackIfDoneHandleReplyForResponseOfConfrontation(data);
			new AjaxSiteHandler().debugger(data, url, settings_data);
		}).fail(function ajaxHandleReplyForResponseOfConfrontationFail(err) {
			new GuiHandler().setErrorDescription(internal_error);
			// new GuiHandler().showDiscussionError('Internal failure while requesting another opininion.');
			new GuiHandler().showDiscussionError(JSON.stringify(err));
		});
	};

	/**
	 * Sends new premisses to the server. Answer will be given to a callback
	 * @param dictionary for inserting
	 */
	this.sendNewPremisseForX = function (dictionary) {
		var url = window.location.href;
		url = url.substr(url.indexOf('issue=') + 'issue='.length);
		dictionary['issue'] = url.substr(0,url.indexOf('/'));
		var csrfToken = $('#' + hiddenCSRFTokenId).val();
		$.ajax({
			url: 'ajax_set_new_premisses_for_X',
			type: 'POST',
			data: dictionary,
			dataType: 'json',
			async: true,
			headers: {
				'X-CSRF-Token': csrfToken
			}
		}).done(function ajaxSendNewPremissesForXDone(data) {
			new InteractionHandler().callbackIfDoneForSendNewPremissesX(data);
		}).fail(function ajaxSendNewPremissesForXFail(err) {
			// new GuiHandler().setErrorDescription(internal_error);
			new GuiHandler().setErrorDescription(JSON.stringify(err));
		});
	};

	/**
	 * Sends new position to the server. Answer will be given to a callback
	 * @param statement for sending
	 */
	this.sendNewStartStatement = function (statement) {
		var csrfToken = $('#' + hiddenCSRFTokenId).val();
		$.ajax({
			url: 'ajax_set_new_start_statement',
			type: 'POST',
			data: {
				statement: statement, issue: new Helper().getCurrentIssueId()
			},
			dataType: 'json',
			async: true,
			headers: {
				'X-CSRF-Token': csrfToken
			}
		}).done(function ajaxSendStartStatementDone(data) {
			new InteractionHandler().callbackIfDoneForSendNewStartStatement(data);
		}).fail(function ajaxSendStartStatementFail(err) {
			// new GuiHandler().setErrorDescription(internal_error);
			new GuiHandler().setErrorDescription(JSON.stringify(err));
		});
	};

	/**
	 * Requests the logfile for the given uid
	 * @param statement_uid current uid of the statement
	 */
	this.getLogfileForStatement = function (statement_uid) {
		var csrfToken = $('#' + hiddenCSRFTokenId).val(), settings_data, url;
		$.ajax({
			url: 'ajax_get_logfile_for_statement',
			type: 'GET',
			data: {
				uid: statement_uid, issue: new Helper().getCurrentIssueId()
			},
			dataType: 'json',
			async: true,
			headers: {
				'X-CSRF-Token': csrfToken
			},
			beforeSend: function(jqXHR, settings ){
				settings_data = settings.data;
				url = this.url;
			}
		}).done(function ajaxGetLogfileForStatementDone(data) {
			new InteractionHandler().callbackIfDoneForGetLogfileForStatement(data);
			new AjaxSiteHandler().debugger(data, url, settings_data);
		}).fail(function ajaxGetLogfileForStatementFail(err) {
			// $('#' + popupEditStatementErrorDescriptionId).text('Unfortunately, the log file could not be requested (server offline or csrf check' +
			// 	' failed. Sorry!');
			$('#' + popupEditStatementErrorDescriptionId).text(JSON.stringify(err));
		});
	};

	/**
	 * Sends a correcture of a statement
	 * @param uid
	 * @param edit_dialog_td_id
	 * @param corrected_text the corrected text
	 * @param final_insert
	 */
	this.sendCorrectureOfStatement = function (uid, edit_dialog_td_id, corrected_text, final_insert) {
		var csrfToken = $('#' + hiddenCSRFTokenId).val(),settings_data, url;
		$.ajax({
			url: 'ajax_set_correcture_of_statement',
			type: 'POST',
			data: {
				uid: uid,
				text: corrected_text,
				final: final_insert,
				issue: new Helper().getCurrentIssueId()
			},
			dataType: 'json',
			async: true,
			headers: {
				'X-CSRF-Token': csrfToken
			},
			beforeSend: function(jqXHR, settings ){
				settings_data = settings.data;
				url = this.url;
			}
		}).done(function ajaxSendCorrectureOfStatementDone(data) {
			new InteractionHandler().callbackIfDoneForSendCorrectureOfStatement(data, edit_dialog_td_id);
			new AjaxSiteHandler().debugger(data, url, settings_data);
		}).fail(function ajaxSendCorrectureOfStatementFail(err) {
			// $('#' + popupEditStatementErrorDescriptionId).text('Unfortunately, the correcture could not be send (server offline or csrf check' +
			// 	' failed. Sorry!');
			$('#' + popupEditStatementErrorDescriptionId).text(JSON.stringify(err));
		});
	};

	/**
	 * Shortens url
	 * @param long_url for shortening
	 */
	this.getShortenUrl = function (long_url) {
		var encoded_url = encodeURI(long_url), settings_data, url;
		$.ajax({
			url: 'ajax_get_shortened_url',
			type: 'GET',
			dataType: 'json',
			data: {
				url: encoded_url, issue: new Helper().getCurrentIssueId()
			},
			async: true,
			beforeSend: function(jqXHR, settings ){
				settings_data = settings.data;
				url = this.url;
			}
		}).done(function ajaxGetShortenUrlDone(data) {
			new InteractionHandler().callbackIfDoneForShortenUrl(data);
			new AjaxSiteHandler().debugger(data, url, settings_data);
		}).fail(function ajaxGetShortenUrl(err) {
			$('#' + popupUrlSharingInputId).val(long_url);
		});
	};

	/**
	 * Requests all users
	 */
	this.getUsersOverview = function () {
		var csrfToken = $('#' + hiddenCSRFTokenId).val(), settings_data, url;
		$.ajax({
			url: 'ajax_all_users',
			type: 'GET',
			dataType: 'json',
			async: true,
			headers: {
				'X-CSRF-Token': csrfToken
			},
			beforeSend: function(jqXHR, settings ){
				settings_data = settings.data;
				url = this.url;
			}
		}).done(function ajaxGetAllUsersDone(data) {
			new InteractionHandler().callbackIfDoneGetUsersOverview(data);
			new AjaxSiteHandler().debugger(data, url, settings_data);
		}).fail(function ajaxGetAllUsersFail(err) {
			// new GuiHandler().setErrorDescription(internal_error);
			new GuiHandler().setErrorDescription(JSON.stringify(err));
		});
	};

	/**
	 * Requests all attacks
	 */
	this.getAttackOverview = function () {
		var csrfToken = $('#' + hiddenCSRFTokenId).val(), settings_data, url;
		$.ajax({
			url: 'ajax_get_attack_overview',
			type: 'GET',
			dataType: 'json',
			data: { issue: new Helper().getCurrentIssueId() },
			async: true,
			headers: {
				'X-CSRF-Token': csrfToken
			},
			beforeSend: function(jqXHR, settings ){
				settings_data = settings.data;
				url = this.url;
			}
		}).done(function ajaxGetAllUsersDone(data) {
			new InteractionHandler().callbackIfDoneAttackOverview(data);
			new AjaxSiteHandler().debugger(data, url, settings_data);
		}).fail(function ajaxGetAllUsersFail(err) {
			// new GuiHandler().setErrorDescription(internal_error);
			new GuiHandler().setErrorDescription(JSON.stringify(err));
		});
	};

	/***
	 *
	 * @param value
	 * @param callbackid
	 * @param type 0 for statements, 1 for edit-popup
	 * @param extra optional
	 */
	this.fuzzySearch = function (value, callbackid, type, extra) {
		var settings_data, url;
		if(value.len==0){
			return;
		}

		$.ajax({
			url: 'ajax_fuzzy_search',
			type: 'GET',
			dataType: 'json',
			data: { value: value, type:type, extra: extra, issue: new Helper().getCurrentIssueId() },
			async: true,
			global: false,
			beforeSend: function(jqXHR, settings ){
				settings_data = settings.data;
				url = this.url;
			}
		}).done(function ajaxGetAllUsersDone(data) {
			new InteractionHandler().callbackIfDoneFuzzySearch(data, callbackid);
			new AjaxSiteHandler().debugger(data, url, settings_data);
		}).fail(function ajaxGetAllUsersFail(err) {
		});
		$('#' + callbackid).focus();
	};

	/**
	 *
	 */
	this.getIssueList = function() {
		var settings_data, url;
		$.ajax({
			url: 'ajax_get_issue_list',
			type: 'GET',
			dataType: 'json',
			async: true,
			beforeSend: function(jqXHR, settings ){
				settings_data = settings.data;
				url = this.url;
			}
		}).done(function ajaxGetIssueListDone(data) {
			new InteractionHandler().callbackIfDoneForGetIssueList(data);
			new AjaxSiteHandler().debugger(data, url, settings_data);
		}).fail(function ajaxGetIssueListFail(err) {
			// new GuiHandler().setErrorDescription(internal_error);
			new GuiHandler().setErrorDescription(JSON.stringify(err));
		});
	};
}