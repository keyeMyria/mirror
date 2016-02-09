/**
 * @author Tobias Krauthoff
 * @email krauthoff@cs.uni-duesseldorf.de
 * @copyright Krauthoff 2015
 */

function InteractionHandler() {
	'use strict';

	/**
	 * Callback, when a new position was send
	 * @param data returned data
	 */
	this.callbackIfDoneForSendNewStartStatement = function (data) {
		var parsedData = $.parseJSON(data);
		if (parsedData.status == '-1') {
			$('#' + addStatementErrorContainer).show();
			$('#' + addStatementErrorMsg).text(_t(notInsertedErrorBecauseInternal));
		} else if (parsedData.status == '0') {
			$('#' + addStatementErrorContainer).show();
			$('#' + addStatementErrorMsg).text(_t(notInsertedErrorBecauseTooShort));
		} else {
			$('#' + discussionSpaceId + 'input:last-child').attr('checked', false).prop('checked', false);
			window.location.href = parsedData.url;
		}
	};

	/**
	 * Callback, when new statements were send
	 * @param data returned data
	 */
	this.callbackIfDoneForSendNewPremisesArgument = function (data) {
		var parsedData = $.parseJSON(data);
		if (parsedData.status == '-1') {
			$('#' + addStatementErrorContainer).show();
			$('#' + addStatementErrorMsg).text(_t(notInsertedErrorBecauseInternal));
		} else if (parsedData.status == '0') {
			$('#' + addStatementErrorContainer).show();
			$('#' + addStatementErrorMsg).text(_t(notInsertedErrorBecauseTooShort));
		} else {
			window.location.href = parsedData.url;
		}
	};

	/**
	 * Callback, when new premises were send
	 * @param data returned data
	 * @param isSupportive
	 */
	this.callbackIfDoneForSendNewStartPremise = function (data, isSupportive) {
		var parsedData = $.parseJSON(data);
		if (parsedData.status == '0') {
			$('#' + addStatementErrorContainer).show();
			$('#' + addStatementErrorMsg).text(_t(notInsertedErrorBecauseInternal));
		} else if (parsedData.status == '0') {
			$('#' + addStatementErrorContainer).show();
			$('#' + addStatementErrorMsg).text(_t(notInsertedErrorBecauseTooShort));
		} else {
			window.location.href = parsedData.url;
		}
	};

	/**
	 * Callback, when the logfile was fetched
	 * @param data of the ajax request
	 */
	this.callbackIfDoneForGettingLogfile = function (data) {
		var parsedData = $.parseJSON(data);
		// status is the length of the content
		if (parsedData.status == '0') {
			$('#' + popupEditStatementLogfileSpaceId).text(_t(noCorrections));
		} else {
			$('#' + popupEditStatementLogfileSpaceId).text('');
			new GuiHandler().showStatementCorrectionsInPopup(parsedData.content);
		}
	};

	/**
	 * Callback, when a correcture could be send
	 * @param data of the ajax request
	 * @param element
	 */
	this.callbackIfDoneForSendCorrectureOfStatement = function (data, element) {
		var parsedData = $.parseJSON(data);
		if (parsedData.status == '-1') {
			$('#' + popupEditStatementErrorDescriptionId).text(_t(noCorrectionsSet));
		} else if (parsedData.status == '0') {
			$('#' + popupEditStatementErrorDescriptionId).text('');
			$('#' + popupEditStatementSuccessDescriptionId).text('');
			$('#' + popupEditStatementWarning).show();
			$('#' + popupEditStatementWarningMessage).text(_t(duplicateDialog));
		} else {
			new GuiHandler().updateOfStatementInDiscussion(parsedData, element);
			$('#' + popupEditStatementErrorDescriptionId).text('');
			$('#' + popupEditStatementSuccessDescriptionId).text(_t(correctionsSet));
		}
	};

	/**
	 * Callback, when a url was shortend
	 * @param data of the ajax request
	 * @param long_url url which should be shortend
	 */
	this.callbackIfDoneForShortenUrl = function (data, long_url) {
		var parsedData = $.parseJSON(data), service;
		if (parsedData.status == '1') {
			service = '<a href="' + parsedData.service_url + '" title="' + parsedData.service + '" target="_blank">' + parsedData.service + '</a>';
			$('#' + popupUrlSharingDescriptionPId).html(_t(feelFreeToShareUrl) + ', ' + _t(shortenedBy) + ' ' + service + ':');
			$('#' + popupUrlSharingInputId).val(parsedData.url);
		} else {
			$('#' + popupUrlSharingDescriptionPId).text(_t(feelFreeToShareUrl) + ":");
			$('#' + popupUrlSharingInputId).val(long_url);
		}
	};

	/**
	 * Callback for Fuzzy Search
	 * @param data
	 * @param callbackid
	 * @param type
	 */
	this.callbackIfDoneFuzzySearch = function (data, callbackid, type) {
		var parsedData = $.parseJSON(data);
		// if there is no returned data, we will clean the list
		if (Object.keys(parsedData).length == 0) {
			$('#' + proposalStatementListGroupId).empty();
			$('#' + proposalPremiseListGroupId).empty();
			$('#' + proposalEditListGroupId).empty();
		} else {
			new GuiHandler().setStatementsAsProposal(parsedData, callbackid, type);
		}
	};

	/**
	 *
	 * @param text
	 * @param conclusion
	 * @param supportive
	 * @param arg
	 * @param relation
	 * @param type
	 */
	this.sendStatement = function (text, conclusion, supportive, arg, relation, type) {
		// error on "no text"
		if (text.length == 0) {
			new GuiHandler().setErrorDescription(_t(inputEmpty));
		} else {

			var undecided_texts= [], decided_texts= [];
			for (var i = 0; i < text.length; i++) {
				// replace multiple whitespaces
				text[i] = text[i].replace(/\s\s+/g, ' ');

				// cutting all 'and ' and 'and'
				while (text[i].indexOf((_t(and) + ' '), text[i].length - (_t(and) + ' ').length) !== -1 ||
					text[i].indexOf((_t(and)), text[i].length - (_t(and) ).length) !== -1 ){
					if (text[i].indexOf((_t(and) + ' '), text[i].length - (_t(and) + ' ').length) !== -1)
						text[i] = text[i].substr(0, text[i].length - (_t(and) + ' ').length);
					else
						text[i] = text[i].substr(0, text[i].length - (_t(and)).length);
				}

				// whitespace at the end
				while (text[i].indexOf((' '), text[i].length - (' ').length) !== -1)
					text[i] = text[i].substr(0, text[i].length - (' ').length);

				// sorting the statements, whether they include the keyword 'AND'
				if (text[i].toLocaleLowerCase().indexOf(' ' + _t(and) + ' ') != -1)
					undecided_texts.push(text[i]);
				else
					decided_texts.push(text[i]);
			}

			if (undecided_texts.length > 0){
				new GuiHandler().showSetStatementContainer(undecided_texts, decided_texts, supportive, type);
			} else if (decided_texts.length > 0){
				alert("TODO: more than one decided text")
			} else {
				// normal case
				text = text[0];
				if (type == fuzzy_add_reason) {
					new AjaxSiteHandler().sendNewPremiseForArgument(arg, relation, supportive, text);
				} else if (type == fuzzy_start_statement) {
					new AjaxSiteHandler().sendNewStartStatement(text);
				} else if (type == fuzzy_start_premise) {
					new AjaxSiteHandler().sendNewStartPremise(text, conclusion, supportive);
				}
			}
		}
	}
}