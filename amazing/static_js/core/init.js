site_user = {
	selected_user_id: function(){
		return $('#user_id').html();
	},

	selected_user_pc: function(){
		return $('#passcode').html();
	},

	selected_user_bc: function(){
		return $('#barcode').html();
	},

	set_selecting_user_id: function(src){
		if($(src).length){
			$('#selecting_user_id').html($(src).attr("id").split('-')[1]);
		}
	},
	
	selecting_user_id: function(src){
		return $('#selecting_user_id').html();
	},

	update_user: function(){
		site_gui.set_gui_user_by_id(
				site_user.selected_user_id(),
				site_user.selected_user_bc(),
				site_user.selected_user_pc()
			);
	}

};

site_gui = {

	clear_selected: function(){
		console.log("clear");
		$('#user_id').html("");
		$('#passcode').html("");
		$('#username').html("");
		$('#selecting_user_id').html("");
		$('#credit').html("");
		$('#barcode').html("");
		$('#purchases').html("");
		site_gui.set_user_spec_buttons(false);
		$('.ui-selected').removeClass('ui-selected');
	},

	set_user_spec_buttons: function(enable){
		var enableString = 'disable';
		if(enable){
			enableString = 'enable';
		}
		$('#buyline').button(enableString);
		$('#undo').button(enableString);
		$('#edituser').button(enableString);
		$('#CANDYBIG').button(enableString);
		$('#CANDYSMALL').button(enableString);
		$('#BEER').button(enableString);
		$('#CAN').button(enableString);
		$('#SOUP').button(enableString);
		$('#BREAD').button(enableString);
		$('#SAUSAGE').button(enableString);
		$('#BAPAO').button(enableString);
	},

	set_gui_user: function(user, settab){
		settab = typeof settab !== 'undefined' ? settab : false;

		if(user){
			$('#username').html(user.name);
			$('#credit').html(user.credit);
			$('#barcode').html(user.barcode);
			$('#user_id').html(user.pk);
			if(settab){
				$('#usertabs').tabs("select", (user.name.toLowerCase().charCodeAt(0)-'a'.charCodeAt(0))/2 +1);
			}
			$('#user-'+user.pk).addClass('ui-selected');

			$.get("user/purchases",{
					'user'     : site_user.selected_user_id(),
					'passcode' : site_user.selected_user_pc(),
					'barcode'  : site_user.selected_user_bc()
			}, function(data){
				$('#purchases').html(data);
				site_gui.init_expandables();
			});

			site_gui.set_user_spec_buttons(true);
		}
	},

	set_gui_user_by_id: function(id, barcode, passcode){
		$.getJSON("user/", {
			'user'     : id,
			'passcode' : passcode,
			'barcode'  : barcode
		}, function(user){
			console.log('here');
			site_gui.set_gui_user(user);
		})
		.error(function(jqxhr){
			if(jqxhr.status == 401){
				$('#purchases').load("passcode",function(){
					site_gui.init_on_screen_keyboards();
					$('#pin_input').focus();
				});
			}
		});
	},

	buy_line: function(){
		if(site_user.selected_user_id() !== ""){
			buy_line_dialog.load();
		}
	},

	init_tabs: function(){
		$("#usertabs").tabs({
			ajaxOptions: {
				success: function(data, textstatus, jqxhr){
					var cp =  $("#usertabs").tabs('option','selected');
					var up = Math.floor(($("#username").html().toLowerCase().charCodeAt(0)-'a'.charCodeAt(0))/2) +1;
					console.log('succ' + cp + " " + up );
					site_gui.init_selectables();
					if(cp != up){
						site_gui.clear_selected();
					}else{
						$('#user-' + site_user.selected_user_id()).addClass('ui-selected');
					}
				}
			},
			show: function(event, ui){
				if(ui.index === 0){
					$('#barcodeselect').focus();
					site_gui.clear_selected();
				}

			}
		});

		$("#usertabs").addClass('ui-tabs-vertical ui-helper-clearfix');

		$("#usertabs li.tab").removeClass('ui-corner-top').addClass('ui-corner-left');
		site_gui.init_barcode_submit();
	},

	init_selectables: function(){
		$( ".checkboxwlabel" ).button()
			.click(function(){
				site_user.set_selecting_user_id(this);
				site_gui.set_gui_user_by_id(
					site_user.selecting_user_id(),
					site_user.selected_user_bc(),
					site_user.selected_user_pc()
				);
			}
		);
	},

	init_user_buttons: function(){
		$("#edituser").button()
			.button('disable')
			.click(function(){
				edit_user_dialog.load();
			})
			.addClass('doubleheightbutton');
		$('#add').button()
			.click(function(){
				new_user_dialog.load();
			})
			.addClass('doubleheightbutton');
		$('#undo').button()
			.click(function(){
				undo_dialog.load();
			})
			.button('disable')
			.addClass('doubleheightbutton');
		$("#buyline").button()
			.button('disable')
			.addClass('doubleheightbutton')
			.click(function(){
				buy_line_dialog.load();
			});
	},

	init_product_buttons: function(){
		$(".productbutton").button().button('disable');

		$(".productbutton").each(function(index){
			$(this).bind('click', function(){
				button_click($(this).attr('id'));
			});
		});
	},

	init_userlist: function(){
		$("#usertabs").load("userlist.html", function(){
			site_gui.init_selectables();
			site_gui.init_tabs();
			
		});
	},

	init_expandables: function(){
		$('.expandable').click(function(){
			$($(this).find('div')[1]).toggle(400,'swing');
		});
	},

	init_on_screen_keyboards: function(){
		$(".osk_norm").keyboard({
			layout: "custom",
			openOn: "click",
			autoAccept: true,
			stickyShift: false,
			customLayout : {
				'default': [
					'` 1 2 3 4 5 6 7 8 9 0 - = {bksp}',
					'{sp:1} q w e r t y u i o p [ ] \\',
					'a s d f g h j k l ; \' ',
					'{shift} z x c v b n m , . / {shift}',
					'{cancel} {space} {accept}'
				],
				'shift': [
					'~ ! @ # $ % ^ & * ( ) _ + {bksp}',
					'{tab} Q W E R T Y U I O P { } |',
					'A S D F G H J K L : " {enter}',
					'{shift} Z X C V B N M < > ? {shift}',
					'{cancel} {space} {accept}'
				]
			}
		});


		$(".osk_mail").keyboard({
			layout: "custom",
			openOn: "click",
			autoAccept: true,
			stickyShift: false,
			customLayout : {
				'default': [
					' 1 2 3 4 5 6 7 8 9 0 -  {bksp}',
					'q w e r t y u i o p {sp:2}',
					'a s d f g h j k l {sp:2}',
					'{sp:3} z x c v b n m {sp:1} + @ . {sp:2}',
					'{cancel} {space} {accept}'
				],
				'shift': []
			}
		});

		$(".osk_bank").keyboard({
			layout: "custom",
			openOn: "click",
			autoAccept: true,
			stickyShift: false,
			customLayout : {
				'default': [
					'{sp:2} 1 2 3 {bksp}',
								' 4 5 6 ',
					'{sp:2} 7 8 9 {accept}',
					'  {sp:1} 0 {sp:1}'
					
				],
				'shift': []
			}
		});

		$(".osk_pin").keyboard({
			layout: "custom",
			openOn: "focus",
			accepted: function(e, keyboard, el){
				$('#passcode').html(CryptoJS.SHA1(el.value).toString());
				//keyboard.destroy();
				site_gui.set_gui_user_by_id(
					site_user.selecting_user_id(),
					site_user.selected_user_bc(),
					site_user.selected_user_pc()
				);
			},
			customLayout : {
				'default': [
					'{sp:2} 1 2 3 {bksp}',
								' 4 5 6 ',
					'{sp:2} 7 8 9 {accept}',
					'  {sp:1} 0 {sp:1}'
					
				],
				'shift': []
			}
		});
	},

	init_timer: function(){
		$.idleTimer('destroy');
		$.idleTimer(10 * 1000);
		$(document).bind("idle.idleTimer", function(){
			reset();
		});
	},

	init_csrf_token: function(){
		$(document).ajaxSend(function(event, xhr, settings) {
				function getCookie(name) {
						var cookieValue = null;
						if (document.cookie && document.cookie !== '') {
								var cookies = document.cookie.split(';');
								for (var i = 0; i < cookies.length; i++) {
										var cookie = jQuery.trim(cookies[i]);
										// Does this cookie string begin with the name we want?
										if (cookie.substring(0, name.length + 1) == (name + '=')) {
												cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
												break;
										}
								}
						}
						return cookieValue;
				}
				function sameOrigin(url) {
						// url could be relative or scheme relative or absolute
						var host = document.location.host; // host + port
						var protocol = document.location.protocol;
						var sr_origin = '//' + host;
						var origin = protocol + sr_origin;
						// Allow absolute or scheme relative URLs to same origin
						return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
								(url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
								// or any other URL that isn't scheme relative or absolute i.e relative.
								!(/^(\/\/|http:|https:).*/.test(url));
				}
				function safeMethod(method) {
						return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
				}

				if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
						xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
				}

		});
	},

	init_barcode_submit: function(){

		$(window).keydown(function(e){
			$('#productselect').focus();
			$('#barcodeselect').focus();
		});

		$('#reset').button().click(function(){
			reset();
		});


		$('#productselect').keypress(function(e){
			if(e.which == 13){
				var code = $('#productselect').val();
				$('#productselect').val('');
				e.preventDefault();
				$.post('user/', {
					'user'     : site_user.selected_user_id(),
					'passcode' : site_user.selected_user_pc(),
					'barcode'  : site_user.selected_user_bc(),
					'type': 'product',
					'product_barcode': code
				}, function(){
					site_user.update_user();
					$.idleTimer(3 * 1000);
					$(document).bind("idle.idleTimer", function(){
						$.idleTimer(10*1000);
						$(document).bind("idle.idleTimer", function(){
							reset();
						});

					});
				}).error(function(jqxhr, txtstatus, error){
					if(jqxhr.status==409){
						no_credit_dialog.load();
					}else{
						alert(jqxhr.textStatus);
					}

				});
			}
		});


		$('#barcodeselect').keypress(function(e){
			if(e.which == 13){
				$('#barcodeselect').removeClass('ui-state-error');
				e.preventDefault();
				var barcode = $('#barcodeselect').val();
				if(barcode === ''){
					return;
				}

				$.getJSON('user/barcode', {'barcode': barcode}, function(user){
					site_gui.set_gui_user(user, false);
					$('#product_scan').slideDown();
					$('#productselect').focus();
					$('#barcodeselect').prop('disabled',true);
				})
				.error(function(jqxhr,txtstatus, error){
					if(jqxhr.status == 404){ //no such user
						$('#barcodeselect').addClass('ui-state-error');
					}else if(jqxhr.status == 409){ //multiple users
						alert(jqxhr.responseText);
					}
				});
			}
		});


	},
	
	setup: function(){

		site_gui.init_product_buttons();
		site_gui.init_user_buttons();
		site_gui.init_userlist();
		site_gui.init_timer();
		site_gui.init_csrf_token();
	}

};


