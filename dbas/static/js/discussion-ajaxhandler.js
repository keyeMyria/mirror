/*global $, jQuery, alert, GuiHandler, InteractionHandler, internal_error, popupErrorDescriptionId, _t */

/**
 * @author Tobias Krauthoff
 * @email krauthoff@cs.uni-duesseldorf.de
 * @copyright Krauthoff 2015
 */

function AjaxSiteHandler() {
	'use strict';
	var push=0,
			loca=0,
			hash=0,
			aler= 0;

	/**
	 * Redirection before an ajax call
	 * @param uid current identifier
	 */
	this.callSiteForChooseActionForStatement = function (uid) {
		this.redirectBrowser('uid=' + uid, attrChooseActionForStatement);
	};

	/**
	 * Redirection before an ajax call
	 * @param uid current identifier
	 * @param isSupportive true, if the premisse should be supportive
	 */
	this.callSiteForGetPremiseForStatement = function (uid, isSupportive) {
		this.redirectBrowser('uid=' + uid + '&supportive=' + isSupportive, attrGetPremisesForStatement);
	};

	/**
	 * Redirection before an ajax call
	 * @param uid current identifier
	 * @param isSupportive
	 */
	this.callSiteForGetMoreForArgument = function (uid, isSupportive) {
		this.redirectBrowser('uid=' + uid + '&supportive=' + isSupportive, attrMoreAboutArgument);
	};

	/**
	 * Redirection before an ajax call
	 * @param pgroup_id
	 * @param conclusion_id
	 * @param isSupportive true, if the premisse should be supportive
	 */
	this.callSiteForGetReplyForPremiseGroup = function (pgroup_id, conclusion_id, isSupportive) {
		this.redirectBrowser('pgroup_id=' + pgroup_id + '&conclusion_id=' + conclusion_id + '&supportive=' + isSupportive, attrReplyForPremisegroup);
	};

	/**
	 * Redirection before an ajax callpgroup_id
	 * @param id_text
	 * @param pgroup_id
	 * @param isSupportive true, if the premisse should be supportive
	 */
	this.callSiteForGetReplyForArgument = function (id_text, pgroup_id, isSupportive) {
		this.redirectBrowser('id_text=' + id_text + '&pgroup_id=' + pgroup_id + '&supportive=' + isSupportive, attrReplyForArgument);
	};

	/**
	 * Redirection before an ajax call
	 * @param id current identifier
	 * @param relation
	 * @param isSupportive true, if the premisse should be supportive
	 */
	this.callSiteForHandleReplyForResponseOfConfrontation = function (id, relation, isSupportive) {
		this.redirectBrowser('id=' + id + '&relation=' + relation + '&supportive=' + isSupportive, attrReplyForResponseOfConfrontation);
	};

	/**
	 * Redirection before an ajax call
	 * @param keyValuePair current key value pair
	 * @param service current service
	 */
	this.redirectBrowser = function (keyValuePair, service) {
		var issue = new Helper().getCurrentIssueId();
		window.location.href = mainpage + 'discussion/' + keyValuePair + '&issue=' + issue + '/' + service + '/' + attrGo;
		// never use this ! window.location.replace(mainpage+'discussion/'+keyValuePair+'&issue='+issue+'/'+service+'/'+attrGo);
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
			method: 'GET',
			data: {
				issue: issue_id, url: window.location.href
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
			new NavigationHandler().setNavigationBreadcrumbs(data);
		}).fail(function ajaxGetAllPositionsFail(err) {
			// new GuiHandler().setErrorDescription(_t(internalError));
			// new GuiHandler().showDiscussionError('Internal failure, could not find any start point.');
			new GuiHandler().showDiscussionError(_t(requestFailed) + ' (' + new Helper().startWithLowerCase(_t(errorCode)) + ' 1). '
				+ _t(doNotHesitateToContact) + '. ' + _t(restartOnError) + '.');
		});
	};

	/**
	 * Send an ajax request for getting all premises for a givens tatement
	 * @param params of clicked statement
	 * @param type
	 */
	this.getPremiseForStatement = function (params, type) {
		var csrfToken = $('#' + hiddenCSRFTokenId).val(), settings_data, url, supportive;
		params = params.split('&');
		supportive = params[1].indexOf('true') != -1;
		url = type == id_premisse ? 'ajax_get_premise_for_statement' : 'ajax_get_premises_for_statement';
		$.ajax({
			url: url,
			method: 'POST',
			data: {
				uid: params[0], supportive: params[1], issue: params[2], url: window.location.href
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
		}).done(function ajaxGetPremiseForStatementDone(data) {
			if 		(type == id_premisses) new InteractionHandler().callbackIfDoneForGetPremisesForStatement(data, supportive);
			else if (type == id_premisse) new InteractionHandler().callbackIfDoneForGetPremiseForStatement(data);
			else {

			new GuiHandler().showDiscussionError(_t(requestFailed) + ' (' + new Helper().startWithLowerCase(_t(errorCode)) + ' 2.x). '
				 + _t(doNotHesitateToContact) + '. ' + _t(restartOnError) + '.');
			}
			new AjaxSiteHandler().debugger(data, url, settings_data);
			new NavigationHandler().setNavigationBreadcrumbs(data);
		}).fail(function ajaxGetPremiseForStatementFail() {
			// new GuiHandler().setErrorDescription(_t(internalError));ription(_t(internalError));
			// new GuiHandler().showDiscussionError('Internal failure while requesting data for your statement.');
			new GuiHandler().showDiscussionError(_t(requestFailed) + ' (' + new Helper().startWithLowerCase(_t(errorCode)) + ' 2.' + type + '). '
				 + _t(doNotHesitateToContact) + '. ' + _t(restartOnError) + '.');
		});
	};

	/**
	 * Send an ajax request for getting text of a statement
	 * @param params of clicked statement
	 */
	this.getTextForStatement = function (params) {
		var csrfToken = $('#' + hiddenCSRFTokenId).val(), settings_data, url;
		params = params.split('&');
		$.ajax({
			url: 'ajax_get_text_for_statement',
			method: 'POST',
			data: {
				uid: params[0], issue: params[1], url: window.location.href
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
		}).done(function ajaxGetTextForStatementDone(data) {
			new InteractionHandler().callbackIfDoneForTextGetTextForStatement(data);
			new AjaxSiteHandler().debugger(data, url, settings_data);
			new NavigationHandler().setNavigationBreadcrumbs(data);
		}).fail(function ajaxGetTextForStatementFail() {
			// new GuiHandler().setErrorDescription(_t(internalError));ription(_t(internalError));
			new GuiHandler().showDiscussionError(_t(requestFailed) + ' (' + new Helper().startWithLowerCase(_t(errorCode)) + ' 14). '
				 + _t(doNotHesitateToContact) + '. ' + _t(restartOnError) + '.');
		});
	};

	/**
	 * Sends an ajax request for getting all premises for a given statement
	 * @param params of clicked statement
	 */
	this.getReplyForPremiseGroup = function (params) {
		var csrfToken = $('#' + hiddenCSRFTokenId).val(), settings_data, url, supportive;
		params = params.split('&');
		supportive = params[2].indexOf('true') != -1;
		$.ajax({
			url: 'ajax_reply_for_premisegroup',
			method: 'POST',
			data: {
				pgroup: params[0], conclusion: params[1], supportive: params[2], issue: params[3], url: window.location.href
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
		}).done(function ajaxGetReplyForPremiseDone(data) {
			new InteractionHandler().callbackIfDoneReplyForPremisegroup(data, supportive);
			new AjaxSiteHandler().debugger(data, url, settings_data);
			new NavigationHandler().setNavigationBreadcrumbs(data);
		}).fail(function ajaxGetReplyForPremiseFail() {
			// new GuiHandler().setErrorDescription(_t(internalError));ription(_t(internalError));
			// new GuiHandler().showDiscussionError('Internal failure while requesting another opininion.');
			new GuiHandler().showDiscussionError(_t(requestFailed) + ' (' + new Helper().startWithLowerCase(_t(errorCode)) + ' 3). '
				 + _t(doNotHesitateToContact) + '. ' + _t(restartOnError) + '.');
		});
	};

	/**
	 * Sends an ajax request for getting all confrotations for a given argument
	 * @param params of the clicked premise group
	 */
	this.getReplyForArgument = function (params) {
		var csrfToken = $('#' + hiddenCSRFTokenId).val(), settings_data, url, supportive;
		params = params.split('&');
		supportive = params[2].indexOf('true') != -1;

		$.ajax({
			url: 'ajax_reply_for_argument',
			method: 'POST',
			data: {
				id_text: params[0], pgroup: params[1], supportive: params[2], issue: params[3], url: window.location.href
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
			new InteractionHandler().callbackIfDoneReplyForArgument(data, supportive);
			new AjaxSiteHandler().debugger(data, url, settings_data);
			new NavigationHandler().setNavigationBreadcrumbs(data);
		}).fail(function ajaxGetReplyForArgumentFail() {
			// new GuiHandler().setErrorDescription(_t(internalError));ription(_t(internalError));
			// new GuiHandler().showDiscussionError('Internal failure while requesting another opininion.');
			new GuiHandler().showDiscussionError(_t(requestFailed) + ' (' + new Helper().startWithLowerCase(_t(errorCode)) + ' 4). '
				 + _t(doNotHesitateToContact) + '. ' + _t(restartOnError) + '.');
		});
	};

	/**
	 * Sends an ajax request for handle the reaction of a confrontation
	 * @param params of clicked relation and statement
	 */
	this.handleReplyForResponseOfConfrontation = function (params) {
		var csrfToken = $('#' + hiddenCSRFTokenId).val(), settings_data, url, supportive, supportive_argument;
		params = params.split('&');
		supportive = params[2].indexOf('true') != -1;
		supportive_argument = params[0].indexOf('support') != -1;
		$.ajax({
			url: 'ajax_reply_for_response_of_confrontation',
			method: 'POST',
			data: {
				id: params[0], relation: params[1], confrontation: params[2], supportive:params[3], issue: params[4], url: window.location.href
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
			// special case fur supports
			if (supportive_argument) {
				new InteractionHandler().callbackIfDoneReplyForArgument(data, supportive);
			} else {
				new InteractionHandler().callbackIfDoneHandleReplyForResponseOfConfrontation(data, supportive);
			}
			new AjaxSiteHandler().debugger(data, url, settings_data);
			new NavigationHandler().setNavigationBreadcrumbs(data);
		}).fail(function ajaxHandleReplyForResponseOfConfrontationFail() {
			// new GuiHandler().setErrorDescription(_t(internalError));ription(_t(internalError));
			// new GuiHandler().showDiscussionError('Internal failure while requesting another opininion.');
			new GuiHandler().showDiscussionError(_t(requestFailed) + ' (' + new Helper().startWithLowerCase(_t(errorCode)) + ' 5). '
				 + _t(doNotHesitateToContact) + '. ' + _t(restartOnError) + '.');
		});
	};

	/**
	 * Sends new premises to the server. Answer will be given to a callback
	 * @param dictionary for inserting; can have the keys {related_argument, premisegroup_id, current_attack, confrontation_uid}; must
	 * have keys with pro_i and con_i
	 */
	this.sendNewPremiseForX = function (dictionary) {
		var url = window.location.href;
		url = url.substr(url.indexOf('issue=') + 'issue='.length);
		dictionary['issue'] = url.substr(0,url.indexOf('/'));
		var csrfToken = $('#' + hiddenCSRFTokenId).val();
		$.ajax({
			url: 'ajax_set_new_premises_for_x',
			method: 'POST',
			data: dictionary,
			dataType: 'json',
			async: true,
			headers: {
				'X-CSRF-Token': csrfToken
			}
		}).done(function ajaxSendNewPremisesForXDone(data) {
			new InteractionHandler().callbackIfDoneForSendNewPremisesX(data);
		}).fail(function ajaxSendNewPremisesForXFail() {
			// new GuiHandler().setErrorDescription(_t(internalError));
			new GuiHandler().showDiscussionError(_t(requestFailed) + ' (' + new Helper().startWithLowerCase(_t(errorCode)) + ' 6). '
				 + _t(doNotHesitateToContact) + '. ' + _t(restartOnError) + '.');
		});
	};

	/**
	 * Sends new premises to the server. Answer will be given to a callback
	 * @param text of the premise
	 * @param conclusion_id id of the conclusion
	 * @param supportive boolean, whether it is supportive
	 */
	this.sendNewStartPremise = function (text, conclusion_id, supportive) {
		var url = window.location.href;
		url = url.substr(url.indexOf('issue=') + 'issue='.length);
		var csrfToken = $('#' + hiddenCSRFTokenId).val();
		$.ajax({
			url: 'ajax_set_new_start_premise',
			method: 'POST',
			data: {
				'text':text,
				'conclusion_id': conclusion_id,
				'support': supportive
			},
			dataType: 'json',
			async: true,
			headers: {
				'X-CSRF-Token': csrfToken
			}
		}).done(function ajaxSendNewStartPremiseDone(data) {
			new InteractionHandler().callbackIfDoneForSendNewStartPremise(data, supportive);
		}).fail(function ajaxSendNewStartPremiseFail() {
			// new GuiHandler().setErrorDescription(_t(internalError));
			new GuiHandler().showDiscussionError(_t(requestFailed) + ' (' + new Helper().startWithLowerCase(_t(errorCode)) + ' 7). '
				 + _t(doNotHesitateToContact) + '. ' + _t(restartOnError) + '.');
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
			method: 'POST',
			data: {
				statement: statement
			},
			dataType: 'json',
			async: true,
			headers: {
				'X-CSRF-Token': csrfToken
			}
		}).done(function ajaxSendStartStatementDone(data) {
			new InteractionHandler().callbackIfDoneForSendNewStartStatement(data);
		}).fail(function ajaxSendStartStatementFail() {
			// new GuiHandler().setErrorDescription(_t(internalError));
			new GuiHandler().showDiscussionError(_t(requestFailed) + ' (' + new Helper().startWithLowerCase(_t(errorCode)) + ' 8). '
				 + _t(doNotHesitateToContact) + '. ' + _t(restartOnError) + '.');
		});
	};

	/**
	 * Requests the logfile for the given uid
	 * @param id_id current uid of the statement
	 */
	this.getLogfileForStatement = function (id_id) {
		var csrfToken = $('#' + hiddenCSRFTokenId).val(), settings_data, url;
		$.ajax({
			url: 'ajax_get_logfile_for_statement',
			method: 'GET',
			data: {
				uid: id_id
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
			new InteractionHandler().callbackIfDoneForGettingLogfile(data);
			new AjaxSiteHandler().debugger(data, url, settings_data);
		}).fail(function ajaxGetLogfileForStatementFail() {
			// $('#' + popupEditStatementErrorDescriptionId).html('Unfortunately, the log file could not be requested (server offline or csrf check' +
			// 	' failed. Sorry!');
			$('#' + popupEditStatementErrorDescriptionId).html(_t(requestFailed) + ' (' + new Helper().startWithLowerCase(_t(errorCode)) + ' 15). '
				 + _t(doNotHesitateToContact) + '. ' + _t(restartOnError) + '.');
		});
	};

	/**
	 * Sends a correcture of a statement
	 * @param uid
	 * @param element
	 * @param corrected_text the corrected text
	 */
	this.sendCorrectureOfStatement = function (uid, corrected_text, element) {
		var csrfToken = $('#' + hiddenCSRFTokenId).val(),settings_data, url;
		$.ajax({
			url: 'ajax_set_correcture_of_statement',
			method: 'POST',
			data: {
				uid: uid,
				text: corrected_text
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
			new InteractionHandler().callbackIfDoneForSendCorrectureOfStatement(data, element);
			new AjaxSiteHandler().debugger(data, url, settings_data);
		}).fail(function ajaxSendCorrectureOfStatementFail() {
			// $('#' + popupEditStatementErrorDescriptionId).html('Unfortunately, the correcture could not be send (server offline or csrf check' +
			// 	' failed. Sorry!');
			$('#' + popupEditStatementErrorDescriptionId).html(_t(requestFailed) + ' (' + new Helper().startWithLowerCase(_t(errorCode)) + ' 13). '
				 + _t(doNotHesitateToContact) + '. ' + _t(restartOnError) + '.');
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
			method: 'GET',
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
		}).fail(function ajaxGetShortenUrl() {
			$('#' + popupUrlSharingInputId).val(long_url);
		});
	};

	/***
	 * Ajax request for the fuzzy search
	 * @param value
	 * @param callbackid
	 * @param type 0 for statements, 1 for edit-popup
	 * @param extra optional
	 */
	this.fuzzySearch = function (value, callbackid, type, extra) {
		var settings_data, url, callback = $('#' + callbackid);

		if(callback.val().length==0) {
			$('#' + proposalStatementListGroupId).empty();
			$('#' + proposalPremiseListGroupId).empty();
			$('#' + proposalEditListGroupId).empty();
			return;
		}

		$.ajax({
			url: 'ajax_fuzzy_search',
			method: 'GET',
			dataType: 'json',
			data: { value: value, type:type, extra: extra, issue: new Helper().getCurrentIssueId() },
			async: true,
			global: false,
			beforeSend: function(jqXHR, settings ){
				settings_data = settings.data;
				url = this.url;
			}
		}).done(function ajaxGetAllUsersDone(data) {
			new InteractionHandler().callbackIfDoneFuzzySearch(data, callbackid, type);
			new AjaxSiteHandler().debugger(data, url, settings_data);
		}).fail(function ajaxGetAllUsersFail() {
			new Helper().delay(function ajaxGetAllUsersFailDelay() {
				new GuiHandler().showDiscussionError(_t(requestFailed) + ' (' + new Helper().startWithLowerCase(_t(errorCode)) + ' 11). '
						+ _t(doNotHesitateToContact) + '. ' + _t(restartOnError) + '.');
			}, 350);
		});
		callback.focus();
	};

	/**
	 *
	 */
	this.getIssueList = function() {
		var settings_data, url;
		$.ajax({
			url: 'ajax_get_issue_list',
			method: 'GET',
			dataType: 'json',
			async: true,
			beforeSend: function(jqXHR, settings ){
				settings_data = settings.data;
				url = this.url;
			}
		}).done(function ajaxGetIssueListDone(data) {
			new InteractionHandler().callbackIfDoneForGetIssueList(data);
			new AjaxSiteHandler().debugger(data, url, settings_data);
		}).fail(function ajaxGetIssueListFail() {
			// new GuiHandler().setErrorDescription(_t(internalError));
			new GuiHandler().setErrorDescription(_t(requestFailed) + ' (' + new Helper().startWithLowerCase(_t(errorCode)) + ' 12). '
				 + _t(doNotHesitateToContact) + '. ' + _t(restartOnError) + '.');
		});
	};
}