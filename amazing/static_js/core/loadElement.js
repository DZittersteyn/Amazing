user_dialog = {
	email_address: function(email) {
		var pattern = new RegExp(/^[+a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+$/i);
		return pattern.test(email);
	},

	bank_account: function(bank_account){
		/*TODO: digit check. */
		var pattern = new RegExp(/^[0-9]+$/i);
		return pattern.test(bank_account);
	},

	name: function(name){
		var pattern = new RegExp(/^[a-zA-Z].*[ ].*/i);
		return pattern.test(name);
	},

	check_fields: function(){
		var valid = true;
		valid = user_dialog.set_field_valid($('#edit_email').val() === "" || user_dialog.email_address($('#edit_email').val()), '#edit_email')
					&& valid;

		valid = user_dialog.set_field_valid(user_dialog.bank_account($('#edit_bank_account').val()), '#edit_bank_account')
					&& valid;

		valid = user_dialog.set_field_valid(user_dialog.name($('#edit_name').val()), '#edit_name')
					&& valid;

		valid = user_dialog.set_field_valid($('#edit_address').val() !== "", '#edit_address')
					&& valid;

		valid = user_dialog.set_field_valid(true, '#edit_barcode')
					&& valid;

		valid = user_dialog.set_field_valid($('#edit_city').val() !== "", '#edit_city')
					&& valid;

		return valid;
	},

	set_field_valid: function(valid, field){
		if(valid){
			$(field).removeClass('ui-state-error');
			$(field).addClass('ui-state-success');
		}else{
			$(field).addClass('ui-state-error');
			$(field).removeClass('ui-state-success');
		}
		return valid;
	},

	reset_field: function(field){
		$(field).removeClass('ui-state-error');
		$(field).removeClass('ui-state-success');
	},

	reset_fields: function(){
		reset_field('#edit_name');
		reset_field('#edit_email');
		reset_field('#edit_bank_account');
		reset_field('#edit_address');
		reset_field('#edit_city');
	},

	set_fields: function(user){
		$('#edit_pk').val(user ? user.pk : "");
		$('#edit_name').val(user ? user.name : "");
		$('#edit_address').val(user ? user.address : "");
		$('#edit_city').val(user ? user.city : "");
		$('#edit_bank_account').val(user ? user.bank_account : "");
		$('#edit_email').val(user ? user.email : "");
		$('#edit_barcode').val(user ? user.barcode : "");
		$('#edit_pin').val("");
		$('#edit_pin').attr("hidden",true);
		$('#has_pin').button().click(function(){
			$('#edit_pin').attr("hidden",false);
			$('#has_pin').next().hide();
			$('#has_pin').hide();
		});

	}


};

new_user_dialog = {

	load: function(){
		$.get('newUser.html',function (data){
			$('body').append(data);
		})
		.success(function(){
			user_dialog.set_fields(null);

			$('#newUser').dialog({
				close: function(){
					new_user_dialog.unload();
				},
				modal:true,
				autoOpen: false,
					minWidth: 740,
					title: 'Nieuwe gebruiker',
					buttons: [{
						text: "Annuleer",
						click: function(){
							new_user_dialog.unload();
						}
					},
					{
						text: "Maak aan",
						click: function(){
							if(user_dialog.check_fields()){
								var passcode = $('#has_pin').prop("checked")?CryptoJS.SHA1($('#edit_pin').val()).toString():"";
								$.post('user/new', {
									'mode': 'new',
									'name': $('#edit_name').val(),
									'address': $('#edit_address').val(),
									'city': $('#edit_city').val(),
									'bank_account': $('#edit_bank_account').val(),
									'email': $('#edit_email').val(),
									'barcode': $('#edit_barcode').val(),
									'has_passcode': $('#edit_pin').val() === "" ? "False" : "True",
									'passcode': passcode
								}).success(function(data){
									new_user_dialog.unload();
									site_gui.set_gui_user_by_id(data, "", passcode);
								});
							}
						}
					}
				]
			});

			site_gui.init_on_screen_keyboards();
			$('#newUser').dialog('open').removeClass('hidden');
		});
	},

	unload: function(){
		$('#newUser').remove();
	}
};

edit_user_dialog = {


	load: function(){
		if(site_user.selected_user_id){
			$.get('newUser.html',function (data){
				$('body').append(data);
			})
			.success(function(){
				$.getJSON("user/", {
					'user'     : site_user.selected_user_id(),
					'passcode' : site_user.selected_user_pc(),
					'barcode'  : site_user.selected_user_bc()
				}, function(user){
					user_dialog.set_fields(user);
					$('#newUser').dialog({
			close: function(){
				edit_user_dialog.unload();
			},
			modal: true,
			autoOpen: false,
			minWidth: 740,
			title: 'Wijzig gebruiker',
			buttons: [
			{
				text: "Annuleer",
				click: function(){
					edit_user_dialog.unload();
				}
			},
			{
				text: "Sla op",
				click: function(){
					if(user_dialog.check_fields()){
						$.post('user/edit', {
							'user'    : site_user.selected_user_id(),
							'passcode': site_user.selected_user_pc(),
							'barcode' : site_user.selected_user_bc(),

							'mode': 'edit',
							'new_name': $('#edit_name').val(),
							'new_address': $('#edit_address').val(),
							'new_city': $('#edit_city').val(),
							'new_bank_account': $('#edit_bank_account').val(),
							'new_email': $('#edit_email').val(),
							'new_barcode': $('#edit_barcode').val(),
							'has_passcode': $('#edit_pin').val() === "" ?"False":"True",
							'changed_passcode': $('#has_pin').prop("checked") ? "True":"False",
							'new_passcode': CryptoJS.SHA1($('#edit_pin').val()).toString()
						}).success(function(data){
							//init_userlist();
							edit_user_dialog.unload();
							site_user.update_user();
						});
					}
				}
			}

			]
		});

		site_gui.init_on_screen_keyboards();
		$('#newUser').dialog('open').removeClass('hidden');
				});

			});
		}
	},

	unload: function(){
		$('#newUser').remove();
	}
};

undo_dialog = {

	submit_and_refresh: function(purchaseid){
		$.post('user/purchase', {
			'user'        : site_user.selected_user_id(),
			'passcode'    : site_user.selected_user_pc(),
			'barcode'     : site_user.selected_user_bc(),

			'valid'       : $('#purchase-' + purchaseid).prop("checked"),
			'purchaseid'  : purchaseid
		}, function(data){
			if($('#userinfo').size()){        //user panel
				site_user.update_user();
			}else if($('#user_data').size()){ //admin panel
				user = user_tab.selected_user();

				user_tab.user_options.reload_user();
				//$('#user_data').load('admin_userdata', {'user': user, 'activity': $('#activities').val()});
			}

			$('#purchaseli-'+purchaseid).html(data);
			$('#purchase-' + purchaseid).button().click(function(){
				undo_dialog.submit_and_refresh(purchaseid);
			});
		})
		.error(function(jqxhr){
			if(jqxhr.status == 409){
				alert("Onvoldoende Credits!");
			}
		});
	},

	load: function(request){
		if(!request){
			request = {};
			request.user = site_user.selected_user_id();
			request.passcode = site_user.selected_user_pc();
			request.barcode = site_user.selected_user_bc();
		}
		$.get('user/undodialog', request,
		function (data){
			$('body').append(data);
		})
		.success(function(){
			$('#expandOld').click(function(){
				$(this).next().slideToggle(400,'swing');
				$('#plusminus').toggleClass('plus');
			});


			$("#undoDialog li").each(function(){
				pattern = /purchaseli-(\d+)/;
				match = pattern.exec($(this).attr('id'));
				if(match){
					var purchaseid = match[1];
					if($(this).parent('#undoDialogPurchaseList').length){
						$(this).find('.checkboxwlabel').button()
						.click(function(){
							undo_dialog.submit_and_refresh(purchaseid);
						});
					} else {
						$(this).find('.checkboxwlabel').button({disabled: true});
						// TODO: Server-side check!
					}
				}
			});


			$('#undoDialog').dialog({
				close: function(){
					undo_dialog.unload();
				},
				resizable: false,
				modal: true,
				autoOpen: false,
				width: 570,
				height: 630,
				title: 'Transactieoverzicht' + ' ' + $('#undo_user').html() ,
				buttons: [{
					text: "Sluiten",
					click: function(){
						undo_dialog.unload();
					}
				}]
			});
			
			$('#undoDialog').dialog('open').removeClass('hidden');

		});
	
	},

	unload: function(){
		$('#undoDialog').remove();
	}
};

buy_line_dialog = {

	load: function(){
		$.get('buyLine.html',function (data){
			$('body').append(data);
		})
		.success(function(){
			$('#numLines').slider({
				range:"min",
				min: 0,
				value: 5,
				step: 5,
				max: 100,
				slide: function(event, ui){
					$("#txtNumLines").html(ui.value);
					$("#price").html((ui.value * $("#pieceprice").html()).toFixed(2));
				}
			});

			$("#txtNumLines").html($('#numLines').slider('value'));
			$("#price").html(($('#numLines').slider('value') * $("#pieceprice").html()).toFixed(2));
			

			$('#buyLine_dialog').dialog({
				modal: true,
				autoOpen: false,
				minWidth: 400,
				minHeight: 200,
				close: function(){
					buy_line_dialog.unload();
				},
				buttons: {
					Annuleer: function(){
						buy_line_dialog.unload();
					},
					Machtiging: function(){
						$.post('user/', { 'user'       : site_user.selected_user_id(),
															'passcode'   : site_user.selected_user_pc(),
															'barcode'    : site_user.selected_user_bc(),
															'type'       : 'credit',
															'credittype' : 'DIGITAL',
															'amount'     : $("#numLines").slider('value')
														})
						.complete(function(){
							site_user.update_user();
							buy_line_dialog.unload();
						});
					}
				}
			}).dialog('open');


		});
	},

	unload: function(){
		$('#buyLine_dialog').remove();
	}
};

no_credit_dialog = {
	load: function(){
		$.get('noCredit.html',function (data){
			$('body').append(data);
		})
		.success(function(){
			$('#noCredit').dialog({
				modal: true,
				autoOpen: false,
				buttons: {
					Ok: function(){
						no_credit_dialog.unload();
					}
				},
				close: function(){
					no_credit_dialog.unload();
				}
			}).dialog('open').removeClass('hidden');
		});
	},

	unload: function(){
		$('#noCredit').remove();
	}
};


