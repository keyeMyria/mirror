/**
 * @author Tobias Krauthoff
 * @email krauthoff@cs.uni-duesseldorf.de
 */
'use strict';


function Main () {
	/**
	 * Sets all click functions
	 * @param guiHandler
	 * @param ajaxHandler
	 */
	this.setClickFunctions = function (guiHandler, ajaxHandler) {
		$('.icon-add-premise').each(function () {
			$(this).click(function () {
				guiHandler.appendAddPremiseRow($(this));
				$(this).hide().prev().show();
				$('#' + sendNewPremiseId).val(_t(saveMyStatements));
			});
		});
		
		/*
		 $('.icon-rem-premise').each(function() {
		 // set in GuiHandler
		 });
		 */
		
		// admin list all users button
		$('#' + listAllUsersButtonId).click(function listAllUsersButtonId() {
			if ($(this).val() === _t(showAllUsers)) {
				ajaxHandler.getUsersOverview();
				$(this).val(_t(hideAllUsers));
			} else {
				$('#' + adminsSpaceForUsersId).empty();
				$(this).val(_t(showAllUsers));
			}
		});
		
		// admin list all attacks button
		$('#' + listAllArgumentId).click(function listAllUsersAttacksId() {
			if ($(this).val() === _t(showAllAttacks)) {
				ajaxHandler.getArgumentOverview();
			} else {
				$('#' + adminsSpaceForArgumentsId).empty();
			}
		});
		
		// hiding the argument container, when the X button is clicked
		$('#' + closeStatementContainerId).click(function closeStatementContainerId() {
			$('#' + addStatementContainerId).hide();
			$('#' + addStatementErrorContainer).hide();
			$('#' + discussionSpaceId + ' li:last-child input').attr('checked', false).prop('checked', false).enable = true;
		});
		
		// hides container
		$('#' + closePremiseContainerId).click(function closeStatementContainerId() {
			$('#' + addPremiseContainerId).hide();
			$('#' + addPremiseErrorContainer).hide();
			$('#' + discussionSpaceId + ' li:last-child input').attr('checked', false).prop('checked', false).enable = true;
		});
		
		// hiding the island view, when the X button is clicked
		$('#' + closeIslandViewContainerId).click(function () {
			guiHandler.resetChangeDisplayStyleBox();
			$('#li_' + addReasonButtonId).attr('checked', true).prop('checked', true);
		});
		
		// hiding the island view, when the X button is clicked
		$('#' + closeGraphViewContainerId).click(function () {
			guiHandler.resetChangeDisplayStyleBox();
		});
		
		// open edit statement
		$('#' + editStatementButtonId).click(function () {
			guiHandler.showEditStatementsPopup();
		});
		
		// close popups
		$('#' + popupEditStatementCloseButtonXId).click(function popupEditStatementCloseButtonXId() {
			guiHandler.hideandClearEditStatementsPopup();
		});
		$('#' + popupEditStatementCloseButtonId).click(function popupEditStatementCloseButtonId() {
			guiHandler.hideandClearEditStatementsPopup();
		});
		$('#' + popupUrlSharingCloseButtonXId).click(function popupUrlSharingCloseButtonXId() {
			guiHandler.hideAndClearUrlSharingPopup();
		});
		$('#' + popupUrlSharingCloseButtonId).click(function popupUrlSharingCloseButtonId() {
			guiHandler.hideAndClearUrlSharingPopup();
		});
		
		// share url for argument blogging
		$('#' + shareUrlId).click(function shareurlClick() {
			guiHandler.showUrlSharingPopup();
		});
		
		/**
		 * Switch between shortened and long url
		 */
		$('#' + popupUrlSharingLongUrlButtonID).click(function () {
			var input_field = $('#' + popupUrlSharingInputId);
			
			if ($(this).data('is-short-url') == '0') {
				input_field.val(input_field.data('short-url'));
				$(this).data('is-short-url', '1').text(_t_discussion(fetchLongUrl));
			} else {
				input_field.val(window.location);
				$(this).data('is-short-url', '0').text(_t_discussion(fetchShortUrl));
			}
		});
		
		/**
		 * Sharing shortened url with mail
		 */
		$('#' + shareUrlButtonMail).click(function shareUrlButtonMail() {
			new Sharing().emailShare('user@example.com', _t(interestingOnDBAS), _t(haveALookAt) + ' ' + $('#' + popupUrlSharingInputId).val());
		});
		
		/**
		 * Sharing shortened url on twitter
		 */
		$('#' + shareUrlButtonTwitter).click(function shareUrlButtonTwitter() {
			new Sharing().twitterShare($('#' + popupUrlSharingInputId).val(), '');
		});
		
		/**
		 * Sharing shortened url on google
		 */
		$('#' + shareUrlButtonGoogle).click(function shareUrlButtonGoogle() {
			new Sharing().googlePlusShare($('#' + popupUrlSharingInputId).val());
		});
		
		/**
		 * Sharing shortened url on facebook
		 */
		$('#' + shareUrlButtonFacebook).click(function shareUrlButtonFacebook() {
			var val = $('#' + popupUrlSharingInputId).val();
			new Sharing().facebookShare(val, "FB Sharing", _t(haveALookAt) + ' ' + val,
				mainpage + "static/images/logo.png");
		});
		
		guiHandler.setDisplayStyleAsDiscussion();
		$('#' + displayStyleIconGuidedId).click(function displayStyleIconGuidedFct() {
			guiHandler.setDisplayStyleAsDiscussion();
		});
		$('#' + displayStyleIconIslandId).click(function displayStyleIconIslandFct() {
			guiHandler.setDisplayStyleAsIsland();
		});
		$('#' + displayStyleIconExpertId).click(function displayStyleIconExpertFct() {
			guiHandler.setDisplayStyleAsGraphView();
		});
		
		/**
		 * Handling report button
		 */
		$('#' + reportButtonId).click(function reportFunction() {
			// jump to contact tab
			var line1 = 'Report ' + new Helper().getTodayAsDate(),
				line2 = 'URL: ' + window.location.href,
				line3 = _t(fillLine).toUpperCase(),
				params = {
					'content': line1 + '\n' + line2 + '\n' + line3,
					'name': $('#header_user').parent().text().replace(/\s/g, '')
				};
			
			new Helper().redirectInNewTabForContact(params);
			
		});
		
		// opinion barometer
		$('#' + opinionBarometerImageId).show().click(function opinionBarometerFunction() {
			new DiscussionBarometer().showBarometer();
		});
		
		// issues
		$('#' + issueDropdownListID + ' .enabled').each(function () {
			if ($(this).children().length > 0) {
				$(this).children().click(function () {
					var href = $(this).attr('href'),
						text = _t(switchDiscussionText1) + ' <strong>' + $(this).attr('value') + '</strong> ';
					text += _t(switchDiscussionText2);
					text += '<br><br>';
					text += _t(switchDiscussionText3);
					$(this).attr('href', '#');
					displayConfirmationDialogWithCheckbox(_t(switchDiscussion), text, _t.keepSetting, href, true);
				});
			}
		});
		$('#' + issueDropdownListID + ' .disabled a').off('click').unbind('click');
		
		// get infos about the author
		//$('[id^="' + questionBubbleId + '-"').click(function () {
		$('.triangle-l').click(function () {
			if ($(this).attr('id').indexOf(questionBubbleId) != -1) {
				var uid = $(this).attr('id').replace(questionBubbleId + '-', '');
				ajaxHandler.getMoreInfosAboutArgument(uid, true);
			}
		});
		
		// adding issues
		$('#' + addTopicButtonId).click(function () {
			guiHandler.showAddTopicPopup(new InteractionHandler().callbackIfDoneForSendNewIssue);
		});
		
		// user info click
		$('.triangle-r-info').each(function () {
			if ($(this).data('votecount') > 0) {
				$(this).click(function () {
					var data_type = $(this).data('type'),
						data_argument_uid = $(this).data('argument-uid'),
						data_statement_uid = $(this).data('statement-uid'),
						data_is_supportive = $(this).data('is-supportive');
					new AjaxDiscussionHandler().getMoreInfosAboutOpinion(data_type, data_argument_uid, data_statement_uid, data_is_supportive);
				});
			} else {
				$(this).removeClass('triangle-r-info').addClass('triangle-r-info-nohover');
			}
		});
		
		$('#' + contactSubmitButtonId).click(function () {
			setTimeout("$('body').addClass('loading')", 0);
		});
	};
	
	/**
	 * Sets click functions for the elements in the sidebar
	 * @param maincontainer - main container which contains the content on the left and the sidebar on the rigt
	 * @param localStorageId - id of the parameter in the local storage
	 */
	this.setSidebarClicks = function (maincontainer, localStorageId) {
		var helper = new Helper();
		var sidebarwrapper = maincontainer.find('.' + sidebarWrapperClass);
		var wrapper = maincontainer.find('.' + contentWrapperClass);
		var hamburger = sidebarwrapper.find('.' + hamburgerIconClass);
		var tackwrapper = sidebarwrapper.find('.' + sidebarTackWrapperClass);
		var tack = sidebarwrapper.find('.' + sidebarTackClass);
		var sidebar = sidebarwrapper.find('.' + sidebarClass);
		
		$(hamburger).click(function () {
			$(this).toggleClass('open');
			var width = wrapper.width();
			
			if (sidebar.is(':visible')) {
				tackwrapper.fadeOut();
				sidebar.toggle('slide');
				hamburger.css('margin-right', '0.5em')
					.css('background-color', '');
				maincontainer.css('max-height', '');
				sidebarwrapper.css('background-color', '')
					.css('height', '');
				helper.delay(function () {
					wrapper.width('');//width + sidebar.outerWidth());
				}, 300);
				helper.setLocalStorage(localStorageId, 'false');
			} else {
				wrapper.width(width - sidebar.outerWidth());
				maincontainer.css('max-height', maincontainer.outerHeight() + 'px');
				helper.delay(function () {
					sidebar.toggle('slide');
					hamburger.css('margin-right', (sidebarwrapper.width() - hamburger.width()) / 2 + 'px')
						.css('margin-left', 'auto')
						.css('background-color', sidebar.css('background-color'));
					sidebarwrapper.css('background-color', $('#' + discussionBubbleSpaceId).css('background-color'))
						.css('height', maincontainer.outerHeight() + 'px');
					tackwrapper.fadeIn();
				}, 200);
			}
		});
		
		// action for tacking the sidebar
		tackwrapper.click(function () {
			var shouldShowSidebar = helper.getLocalStorage(localStorageId) == 'true';
			if (shouldShowSidebar) {
				helper.rotateElement(tack, '0');
				helper.setLocalStorage(localStorageId, 'false');
				
				tack.data('title', _t_discussion(pinNavigation));
				
				// hide sidebar if it is visible
				if (sidebar.is(':visible')) {
					hamburger.click();
				}
			} else {
				helper.rotateElement(tack, '90');
				helper.setLocalStorage(localStorageId, 'true');
				tack.data('title', _t_discussion(unpinNavigation));
			}
		});
		
	};
	
	/**
	 * Sets style options for the elements in the sidebar
	 * @param maincontainer - main container which contains the content on the left and the sidebar on the rigt
	 * @param localStorageId - id of the parameter in the local storage
	 */
	this.setSidebarStyle = function (maincontainer, localStorageId) {
		// read local storage for pinning the bar / set title
		var shouldShowSidebar = new Helper().getLocalStorage(localStorageId) == 'true';
		var sidebarwrapper = maincontainer.find('.' + sidebarWrapperClass);
		var wrapper = maincontainer.find('.' + contentWrapperClass);
		var tackwrapper = sidebarwrapper.find('.' + sidebarTackWrapperClass);
		var tack = sidebarwrapper.find('.' + sidebarTackClass);
		var sidebar = sidebarwrapper.find('.' + sidebarClass);
		var helper = new Helper();
		if (shouldShowSidebar) {
			var width = wrapper.width();
			var hamburger = sidebarwrapper.find('.' + hamburgerIconClass);
			
			helper.rotateElement(tack, '90');
			helper.setAnimationSpeed(wrapper, '0.0');
			helper.setAnimationSpeed(hamburger, '0.0');
			
			hamburger.addClass('open');
			
			wrapper.width(width - sidebar.outerWidth());
			maincontainer.css('max-height', maincontainer.outerHeight() + 'px');
			sidebar.show();
			hamburger.css('margin-right', (sidebarwrapper.width() - hamburger.width()) / 2 + 'px')
				.css('margin-left', 'auto')
				.css('background-color', sidebar.css('background-color'));
			sidebarwrapper.css('background-color', $('#' + discussionBubbleSpaceId).css('background-color'))
				.css('height', maincontainer.outerHeight() + 'px');
			tackwrapper.fadeIn();
			
			helper.setAnimationSpeed(wrapper, '0.5');
			helper.setAnimationSpeed(hamburger, '0.5');
			
			tackwrapper.data('title', _t_discussion(unpinNavigation));
		} else {
			tackwrapper.data('title', _t_discussion(pinNavigation));
		}
	};
	
	/**
	 * Sets all keyUp functions
	 * @param guiHandler
	 * @param ajaxHandler
	 */
	this.setKeyUpFunctions = function (guiHandler, ajaxHandler) {
		// gui for the fuzzy search (statements)
		$('#' + addStatementContainerMainInputId).keyup(function () {
			new Helper().delay(function () {
				var escapedText = new Helper().escapeHtml($('#' + addStatementContainerMainInputId).val());
				if ($('#' + discussionBubbleSpaceId).find('p:last-child').text().indexOf(_t(initialPositionInterest)) != -1) {
					// here we have our start statement
					ajaxHandler.fuzzySearch(escapedText, addStatementContainerMainInputId, fuzzy_start_statement, '');
				} else {
					// some trick: here we have a premise for our start statement
					ajaxHandler.fuzzySearch(escapedText, addStatementContainerMainInputId, fuzzy_start_premise, '');
				}
			}, 200);
		});
		
		// gui for the fuzzy search (premises)
		$('#' + addPremiseContainerMainInputId).keyup(function () {
			new Helper().delay(function () {
				var escapedText = new Helper().escapeHtml($('#' + addPremiseContainerMainInputId).val());
				ajaxHandler.fuzzySearch(escapedText, addPremiseContainerMainInputId, fuzzy_add_reason, '');
			}, 200);
		});
		
		// gui for editing statements
		$('#' + popupEditStatementTextareaId).keyup(function popupEditStatementTextareaKeyUp() {
			new Helper().delay(function () {
				ajaxHandler.fuzzySearch($('#' + popupEditStatementTextareaId).val(),
					popupEditStatementTextareaId,
					fuzzy_statement_popup,
					$('#' + popupEditStatementContentId + ' .text-hover').attr('id').substr(3));
				$('#' + popupEditStatementWarning).hide();
				$('#' + popupEditStatementWarningMessage).text('');
			}, 200);
		});
	};
	
	/**
	 *
	 * @param guiHandler
	 */
	this.setStyleOptions = function (guiHandler) {
		guiHandler.setMaxHeightForBubbleSpace();
		
		guiHandler.hideSuccessDescription();
		guiHandler.hideErrorDescription();
		
		// align buttons
		// var restart, issues, restartWidth, issueWidth;
		// restart = $('#discussion-restart-btn');
		// issues = $('#' + issueDropdownButtonID);
		// restartWidth = restart.outerWidth();
		// issueWidth = issues.outerWidth();
		// restart.attr('style', restartWidth<issueWidth ? 'width: ' + issueWidth + 'px;' : '');
		// issues.attr('style', restartWidth>issueWidth ? 'width: ' + restartWidth + 'px;' : '');
		
		// focus text of input elements
		// $('input[type='text']'').on("click", function () {
		$('#' + popupUrlSharingInputId).on("click", function () {
			$(this).select();
		});
		
		// hover effects on text elements
		var data = 'data-argumentation-type';
		var list = $('#' + discussionSpaceListId);
		list.find('span[' + data + '!=""]').each(function () {
			var attr = $(this).attr(data);
			var tmp = $('<span>').addClass(attr + '-highlighter');
			tmp.appendTo(document.body);
			var old_color = $(this).css('color');
			var new_color = tmp.css('color');
			tmp.remove();
			$(this).hover(
				function () {
					$('#dialog-speech-bubbles-space').find('span[' + data + '="' + attr + '"]')
						.css('color', new_color)
						.css('background-color', '#edf3e6')
						.css('border-radius', '2px');
				}, function () {
					$('#dialog-speech-bubbles-space').find('span[' + data + '="' + attr + '"]')
						.css('color', old_color)
						.css('background-color', '')
						.css('border-radius', '0');
				}
			);
		});
		
		// hover on radio buttons
		list.find('input').each(function(){
			$(this).hover(function(){
				$(this).prop('checked', true);
			}, function(){
				$(this).prop('checked', false);
			})
		});
		list.find('label').each(function(){
			$(this).hover(function(){
				$(this).prev().prop('checked', true);
			}, function(){
				$(this).prev().prop('checked', false);
			})
		});
	};
	
	/**
	 *
	 */
	this.setWindowOptions = function () {
		// ajax loading animation
		$(document).on({
			ajaxStart: function ajaxStartFct() {
				setTimeout("$('body').addClass('loading')", 0);
			},
			ajaxStop: function ajaxStopFct() {
				setTimeout("$('body').removeClass('loading')", 0);
			}
		});
		
		// some hack
		$('#navbar-left').empty();
		
		//$(window).load(function windowLoad() {
		//});
		
		$(window).resize(function () {
			new GuiHandler().setMaxHeightForBubbleSpace();
		});
	};
	
	/**
	 *
	 */
	this.setGuiOptions = function () {
		$('#' + popupLogin).on('hidden.bs.modal', function () {// uncheck login button on hide
			var login_item = $('#' + discussionSpaceListId).find('#item_login');
			if (login_item.length > 0)
				login_item.attr('checked', false).prop('checked', false)
		}).on('shown.bs.modal', function () {
			$('#' + loginUserId).focus();
		});
		
		// highlight edited statement
		var pos = window.location.href.indexOf('edited_statement=');
		if (pos != -1) {
			var ids = window.location.href.substr(pos + 'edited_statement='.length);
			var splitted = ids.split(',');
			$.each(splitted, function (index, value) {
				$('#' + value).css('background-color', '#FFF9C4');
			});
		}
	};
	
	/**
	 *
	 * @param guiHandler
	 * @param interactionHandler
	 */
	this.setInputExtraOptions = function (guiHandler, interactionHandler) {
		var spaceList = $('#' + discussionSpaceListId);
		var input = spaceList.find('li:last-child input');
		var text = [], splits, conclusion, supportive, arg, relation;
		splits = window.location.href.split('?');
		splits = splits[0].split('/');
		var sendStartStatement = function () {
			text = $('#' + addStatementContainerMainInputId).val();
			interactionHandler.sendStatement(text, '', '', '', '', fuzzy_start_statement);
		};
		var sendStartPremise = function () {
			conclusion = splits[splits.length - 2];
			supportive = splits[splits.length - 1] == 't';
			text = [];
			$('#' + addPremiseContainerBodyId + ' input').each(function () {
				if ($(this).val().length > 0)
					text.push($(this).val());
			});
			interactionHandler.sendStatement(text, conclusion, supportive, '', '', fuzzy_start_premise);
		};
		var sendArgumentsPremise = function () {
			text = [];
			$('#' + addPremiseContainerBodyId + ' input').each(function () {
				if ($(this).val().length > 0)
					text.push($(this).val());
			});
			var add = window.location.href.indexOf('support') != -1 ? 1 : 0;
			arg = splits[splits.length - 3 - add];
			supportive = splits[splits.length - 2 - add] == 't';
			relation = splits[splits.length - 1 - add];
			interactionHandler.sendStatement(text, '', supportive, arg, relation, fuzzy_add_reason);
		};
		
		if (window.location.href.indexOf('/r/') != -1) {
			$('#' + discussionSpaceId + ' label').each(function () {
				$(this).css('width', '95%');
			})
		}
		
		$('#' + discussionSpaceId + ' input').each(function () {
			$(this).attr('checked', false).prop('checked', false);
		});
		
		$('#' + sendNewStatementId).off("click").click(function () {
			if ($(this).attr('name').indexOf('start') != -1) {
				sendStartStatement();
			}
		});
		$('#' + sendNewPremiseId).off("click").click(function () {
			if (input.attr('id').indexOf('start_statement') != -1) {
				sendStartStatement();
			} else if (input.attr('id').indexOf('start_premise') != -1) {
				sendStartPremise();
			} else if (input.attr('id').indexOf('justify_premise') != -1) {
				sendArgumentsPremise();
			}
		});
		
		// hide one line options
		var children = spaceList.find('input');
		var id = children.eq(0).attr('id');
		var ids = ['start_statement', 'start_premise', 'justify_premise', 'login'];
		if (children.length == 1 && ($.inArray(id, ids) != -1 && $('#link_popup_login').text().trim().indexOf(_t(login)) == -1)) {
			children.eq(0).attr('checked', true).prop('checked', true).parent().hide();
		}
		
		// TODO CLEAR DESIGN
		// options for the extra buttons, where the user can add input!
		
		id = input.attr('id').indexOf('item_' == 0) ? input.attr('id').substr('item_'.length) : input.attr('id');
		if ($.inArray(id, ids) != -1) {
			input.attr('onclick', '');
			input.click(function () {
				// new position at start
				if (input.attr('id').indexOf('start_statement') != -1) {
					// guiHandler.showHowToWriteTextPopup();
					guiHandler.showAddPositionContainer();
					$('#' + sendNewStatementId).off("click").click(function () {
						sendStartStatement();
					});
				}
				// new premise for the start
				else if (input.attr('id').indexOf('start_premise') != -1) {
					// guiHandler.showHowToWriteTextPopup();
					guiHandler.showAddPremiseContainer();
					$('#' + sendNewPremiseId).off("click").click(function () {
						sendStartPremise();
					});
				}
				// new premise while judging
				else if (input.attr('id').indexOf('justify_premise') != -1) {
					// guiHandler.showHowToWriteTextPopup();
					guiHandler.showAddPremiseContainer();
					$('#' + sendNewPremiseId).off("click").click(function () {
						sendArgumentsPremise();
					});
				}
				// login
				else if (input.attr('id').indexOf('login') != -1) {
					$('#' + popupLogin).modal('show');
				}
			});
		}
	};
}

/**
 * main function
 */
$(document).ready(function mainDocumentReady() {
	var tacked_sidebar = 'tacked_sidebar';
	var guiHandler = new GuiHandler();
	var ajaxHandler = new AjaxDiscussionHandler();
	var interactionHandler = new InteractionHandler();
	var main = new Main();
	var tmp;
	var discussionContainer = $('#' + discussionContainerId);
	
	guiHandler.setHandler(interactionHandler);
	main.setStyleOptions(guiHandler);
	main.setSidebarStyle(discussionContainer, tacked_sidebar);
	main.setSidebarClicks(discussionContainer, tacked_sidebar);
	// sidebar of the graphview is set in GuiHandler:setDisplayStyleAsGraphView()
	main.setClickFunctions(guiHandler, ajaxHandler);
	main.setKeyUpFunctions(guiHandler, ajaxHandler);
	main.setWindowOptions();
	main.setGuiOptions();
	main.setInputExtraOptions(guiHandler, interactionHandler);

	// displayBubbleInformationDialog();

	// some extras
	// get restart url and cut the quotes
	tmp = $('#discussion-restart-btn').attr('onclick').substr('location.href='.length);
	tmp = tmp.substr(1, tmp.length - 2);
	$('#' + discussionEndRestart).attr('href', tmp);

	//
	tmp = window.location.href.split('?');
	if (tmp[0].indexOf('/reaction/') != -1){
		$('#island-view-undermine-button').attr('onclick', $('#item_undermine').attr('onclick'));
		$('#island-view-support-button').attr('onclick', $('#item_support').attr('onclick'));
		$('#island-view-undercut-button').attr('onclick', $('#item_undercut').attr('onclick'));
		$('#island-view-rebut-button').attr('onclick', $('#item_rebut').attr('onclick'));
	}

	$(document).delegate('.open', 'click', function(event){
		$(this).addClass('oppenned');
		event.stopPropagation();
	});
	$(document).delegate('body', 'click', function(event) {
		$('.open').removeClass('oppenned');
	});
	$(document).delegate('.cls', 'click', function(event){
		$('.open').removeClass('oppenned');
		event.stopPropagation();
	});
});