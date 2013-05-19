admin = {
	setup: function(){
		$('.tabs').tabs();


		user_tab.setup();
		activity_tab.setup();
		inventory_tab.setup();
		system_user_tab.setup();
		totals_tab.setup();

		site_gui.init_csrf_token();
	}

};

totals_tab = {
	
	reload_totals: function(){
		$.get('totals/list', function(data){
			$('#totals_settings').html(data);
			$('#reload_totals').button().click(function(){
				totals_tab.reload_totals();
			});

			$('#total_clear').button().click(function(){
				totals_tab.reload_totals();
				$('#total_overview').html('');
			});
			$('#compute_totals').button().click(function(){
				$.get('totals/result', {'from': $('#total_from').val(), 'to': $('#total_to').val() }, function(data){
					$('#total_overview').html(data);
					$('#total_select').slideUp();
					$('#total_summary').slideDown();
				});

			});
		});
	},

	setup: function(){

		totals_tab.reload_totals();


		$('#totals_tab').on('change', '#total_select > select', function(){
			if($('#total_to').val() !== null && $('#total_from').val() !== null && $('#total_to').val() > $('#total_from').val()){
				$('#compute_totals').fadeIn();
			}else{
				$('#compute_totals').fadeOut();
			}

			var select = $(this);
			var details = select.next();
			$.get('totals/list', {'pk': select.val()}, function(data){
				details.slideUp(function(){
					details.html('');
					for(var item in data){
						var line = $('<p/>');
						$('<span/>').html(data[item].description).addClass('desc').appendTo(line);
						$('<span/>').html(data[item].modification).addClass('nums').appendTo(line);
						line.appendTo(details);
					}
					select.next().slideDown();
				});
			});
		});

	}

};

user_tab = {



	get_auth: function(){
		return	{
					'user': user_tab.selected_user(),
					'passcode': user_tab.selected_pc(),
					'barcode': user_tab.selected_bc()
				};
	},

	selected_user: function(){
		return $('#pk').html();
	},

	selected_pc: function(){
		return $('#passcode').html();
	},

	selected_bc: function(){
		return $('#barcode').html();
	},

	setup: function(){

		$('#adduser').button();
		$('#user_tab').on('click', '#adduser', function(){
			new_user_dialog.load();
		});

		user_tab.reload_userlist();
		$('#user_tab').on('click', '.userbutton-input', function(){
			$.get('adminoptions', {'user': $(this).prop('id').split('-')[1]}, function(data){
				$('#useroptions').html(data);
			});
		});


		$('#filter_inactive_users').button().click(function(){
			if($(this).is(":checked")){
				$(".nonactive").addClass("hidden");
			}else{
				$(".nonactive").removeClass("hidden");
			}
		});

	},

	reload_userlist: function(){

		var selected = user_tab.selected_user();


		$.get('adminuserlist', function(data){
			$('#userselect').html(data);
		}).success(function(){
			$('.userbutton-input').button();
		
			if($("#filter_inactive_users").is(":checked")){
				$(".nonactive").addClass("hidden");
			} else {
				$(".nonactive").removeClass("hidden");
			}

			if(selected){
				$(selected).button().click();
			}
		});
	},
 
	user_options : {

		reload_user: function(){
			var user = user_tab.selected_user();
			var act = $('#activities').val();

			$.get('adminoptions', {'user': user}, function(data){
				$('#useroptions').html(data);
				$('#activities').val(act);
				$('#activities').change();
			});
		},

		setup: function(){
			$('#commit_purchase').button().button('disable').click(function(){
				purchase = user_tab.get_auth();
				purchase['activity'] = $('#activities').val();
				purchase['admin'] = 'admin';
				
				purchase['type'] = 'product';
				$('.valuefield.product').each(function(){
					purchase['productID'] = this.id;
					purchase['amount'] = this.value;
					this.value = 0;
					$.post('user/', purchase);
				});
				
				purchase['type'] = 'credit';
				$('.valuefield.credit').each(function(){
					purchase['credittype'] = this.id;
					purchase['amount'] = this.value;
					this.value = 0;
					$.post('user/', purchase);
				});
			});
			
			$('#user_data').on('keyup', '.valuefield', function(){
				var field = $(this);

				if(field.val() === "0"){
					field.removeClass('ui-state-highlight');
					field.next().addClass('hidden');
				}else{
					field.addClass('ui-state-highlight');
					field.next().removeClass('hidden');
				}
			
			});

			$('#setactive').buttonset();
			$('#activate').click(function(){
				$.post('user/activate', {'user': user_tab.selected_user()},function(){
					user_tab.reload_userlist();
				});
			});
			$('#deactivate').click(function(){
				$.post('user/deactivate', {'user': user_tab.selected_user()}, function(){
					user_tab.reload_userlist();
				});
			});

			$('#admin_undo').button().click(function(){
				request = user_tab.get_auth();
				request.activity = $('#activities').val();
				undo_dialog.load(request);
			});



			$('#activities').change(function(){
				user = user_tab.selected_user();

				$('#user_data').load('admin_userdata', {'user': user, 'activity': $('#activities').val()}, function(){
					if($('#activities').val() == 'all'){
						$('#commit_purchase').button('disable').children().html('Select an activity');
						$('.valuefield').each(function(){
							this.disabled=true;
						});
					}else{
						$('#commit_purchase').button('enable').children().html('Purchase in activity "<span class="actlabel"></span>"');
						$('.valuefield').each(function(){
							this.disabled=false;
						});
					}
					$('.actlabel').html($('#activities option:selected').text());
				});
			});


			$('#revertchanges').button().click(function(){
				user_tab.user_options.reload_user();
			});

			$('#submitchanges').button().click(function(){
				user = user_tab.get_auth();

				user['mode']				= 'edit';
				user['new_name']			= $('#name').val();
				user['new_address']			= $('#address').val();
				user['new_city']			= $('#city').val();
				user['new_bank_account']	= $('#bank_account').val();
				user['new_email']			= $('#email').val();
				user['new_barcode']			= $('#barcode').val();
				user['changed_passcode']	= "False";
				$.post('user/edit', user, function(){
					user_tab.user_options.reload_user();
					user_tab.reload_userlist();
				});

			});


			$('#resetpassword').button().click(function(){
				$.post('user/reset', {'user': user_tab.selected_user()});
				user_tab.reload_userlist();
			});


			$('#user_tab').on('keyup', '.leftpane input[type=text]', function(){
				var field = $(this);

				user = user_tab.get_auth();
				user['field'] = field.attr('id');
				user['value'] = field.val();

				$.get('consistent', user, function(data){
					if(data == "True"){
						field.removeClass('ui-state-highlight');
						field.next().addClass('hidden');
					}else{
						field.addClass('ui-state-highlight');
						field.next().removeClass('hidden');
					}
				});

			});


		}

	}
};

activity_tab = {


	setup: function(){

		$('#add_activity').button().click(function(e){
			e.preventDefault();
			$.post('adminactivitylist/new', {'name': $('#new_activity_name').val()}, function(){
				$('#new_activity_name').val('');
				activity_tab.reload_activitylist();
			}).error(function(jqXHR){
				alert(jqXHR.responseText);
			});
		});

		activity_tab.reload_activitylist();

		$('#activity_tab').on('click', '.activitybutton-input', function(){
			activity_tab.activity_options.load($(this).prop('id').split('-')[1]);
		});



		$('#activity_tab').on('keyup', '.leftpane input[type=text]:not(#activity_restrictions input)', function(){
			var field = $(this);

			activity = {'activity' : activity_tab.selected_activity()};
			activity['field'] = field.attr('name');
			activity['value'] = field.val();

			$.get('consistent', activity, function(data){
				if(data == "True"){
					field.removeClass('ui-state-highlight');
					field.next().addClass('hidden');
				}else{
					field.addClass('ui-state-highlight');
					field.next().removeClass('hidden');
				}
			});

		});


	},

	activity_options: {

		setup: function(){
			console.log('hai');


			$('#clear_start').button().click(function(){
				activity_tab.activity_options.set_date_time('#activity_start');
				$('#activity_start_date').trigger('keyup');
				$('#activity_start_time').trigger('keyup');
			});

			$('#clear_end').button().click(function(){
				activity_tab.activity_options.set_date_time('#activity_end');
				$('#activity_end_date').trigger('keyup');
				$('#activity_end_time').trigger('keyup');
			});

			$('#now_start').button().click(function(){
				activity_tab.activity_options.set_date_time('#activity_start', new Date());
				$('#activity_start_date').trigger('keyup');
				$('#activity_start_time').trigger('keyup');
			});

			$('#now_end').button().click(function(){
				activity_tab.activity_options.set_date_time('#activity_end', new Date());
				$('#activity_end_date').trigger('keyup');
				$('#activity_end_time').trigger('keyup');
			});


			$('#commit_difference').button().click(function(){
				var diffs = {};
				$('#user_data input.valuefield').each(function(){
					if ($(this).val() !== '0'){
						diffs[$(this).prop('id').replace('act_','')] = -$(this).val();
						$(this).val("0");
					}
				});
				diffs.description = "Losses during activity: " + $('#activity_name').val();
				diffs.activity = activity_tab.selected_activity();
				$.post('inventory/purchase', diffs, function(){
					activity_tab.reload_activitylist(true);

				});
			});


			$('#submitchanges_activity').button().click(function(){
				var activity = {};
				activity['id'] = activity_tab.selected_activity();
				activity['name'] = $('#activity_name').val();
				activity['responsible'] = $('#activity_resp').val();
				activity['note'] = $('#activity_note').val();
				activity['start'] = $('#activity_start_date').val() + " " +$('#activity_start_time').val();
				activity['end'] = $('#activity_end_date').val() + " " +$('#activity_end_time').val();
				activity['free'] = $('#activity_free').val();


				var rests = $('#activity_restrictions_details table tbody');

				$('tr', rests).each(function(){
					if($('.type', this).val()){
						activity['_restriction_' + $('.type', this).val()] = $('.val input', this).val();
					}
				});

				$.post('activity/edit', activity, function(){
					activity_tab.reload_activitylist(true);
					activity_tab.activity_options.load(activity_tab.selected_activity());
				}).error(function(jqXHR){
					alert(jqXHR.responseText);
				});
			});

			$('#revertchanges_activity').button().click(function(){
				activity_tab.activity_options.load(activity_tab.selected_activity());
			});

			$('#delete_activity').button().click(function(){
				$.post('activity/delete', {'id': activity_tab.selected_activity()}, function(){
					activity_tab.reload_activitylist(true);
					$('#activityoptions').html("");
				}).error(function(jqXHR){
					alert(jqXHR.responseText);
				});
			});

		},

		load: function(id){
			$.get('activityoptions', {'activity': id}, function(data){
				$('#activityoptions').html(data);
			});
		},

		set_date_time: function(field, datetime){
			var date = '';
			var time = '';
			if(datetime){
				date = $.datepicker.formatDate('dd/mm/yy',datetime);
				var hr = (datetime.getHours() < 10 ? '0' : '') + datetime.getHours();
				var mn = (datetime.getMinutes() < 10 ? '0' : '') + datetime.getMinutes();
				time = hr + ':' + mn;
			}
			$(field+'_date').val(date);
			$(field+'_time').val(time);

		}
	},


	reload_activitylist: function(reclick){
		reclick = typeof reclick !== 'undefined' ? reclick : false;

		var selected = activity_tab.selected_activity();

		$.get('adminactivitylist', function(data){
			$('#activityselect').html(data);
		}).success(function(){
			$('.activitybutton-input').button();
			if(reclick){
				$('#activity-' +selected).button().click();
			}
		});


	},

	selected_activity: function(){
		if ($('.activitybutton-input:checked').length){
			return $('.activitybutton-input:checked').prop('id').split('-')[1];
		}
	}

};

inventory_tab = {

	new_inventory: [],

	setup: function(){
		inventory_tab.reload_inventory_list();
		$('#inventory_tab').on('click', '.inventory', function(){
			$(this).children('.detail').slideToggle();
		});

		$('#inventory_tab').on('click', '.inventorynote', function(event){
			event.stopPropagation();
			var id = $(this).prop('id');
			var match = $(this).prop('id').split('_');
			var type = match[1];
			var pk = match[2];
			var popup = $('<div/>').html('<input type="text" id="new_note"/>').dialog({
				close: function(){
					$(this).dialog('destroy').remove();
				},
				resizable: false,
				height:150,
				width: 200,
				title:"New Note",
				modal: true,
				buttons: {
					"Cancel": function(){
						$(this).dialog('destroy').remove();
					},
					"OK": function(){
						alert('#inventory_'+ type +'_'+ pk + ' > div > p:first');
						$('#inventory_'+ type +'_'+ pk + ' > div > p:first').html($('#new_note').val());
						var dialog = $(this);
						$.post('inventory/edit',{'pk':pk, 'type': type, 'new_desc': $('#new_note').val()})
						.error(function(jqXHR){
							alert(jqXHR.textStatus);
						})
						.complete(function(){
							dialog.dialog( "destroy" ).remove();
						});

						$(this).dialog('destroy').remove();
					}
				}
			});

		});

		$('#inventory_tab').on('click', '.inventorydelete', function(event){
			
			event.stopPropagation();
			var match = $(this).prop('id').split('_');
			var type = match[1];
			var pk = match[2];

			$( '<div/>' ).html("Do you really want to delete this inventory entry? This action can not be undone. If you delete an item that has already been used to generate an export, this is DEFINITELY not a good idea.").dialog({
				close: function(){
					$(this).dialog('destroy').remove();
				},
				resizable: false,
				height:190,
				width: 500,
				title:"Are you sure?",
				modal: true,
				buttons: {
					"Delete!": function() {
						var dialog = $(this);
						$.post('inventory/delete',{'pk':pk, 'type': type},function(){
							inventory_tab.reload_inventory_list();
						})
						.error(function(jqXHR){
							alert(jqXHR.textStatus);
						})
						.complete(function(){
							dialog.dialog( "destroy" ).remove();
						});
					},
					Cancel: function() {
						$( this ).dialog( "destroy" ).remove();
					}
				}
			});


		});

		$('#inventory_current_scan').on('click', 'button', function(){
			var rem = $(this).prop('id').replace('inventory_list_remove_','');

			inventory_tab.new_inventory.splice(rem,1);
			inventory_tab.redraw_current_scan();
		});

		$('#inventory_barcode').keydown( function(e) {
			var key = e.charCode ? e.charCode : e.keyCode ? e.keyCode : 0;
			if(key == 13) {
				e.preventDefault();
				var barcode = $(this).val();
				inventory_tab.submit_barcode(barcode);
			}
		});

		$('#inventory_newprod_type').load('inventory/types');
		$('#inventory_create_new_prod').button().click(function(){
			$.post('inventory/product', {
				'mode': 'add',
				'barcode': $('#inventory_barcode').val(),
				'amount': $('#inventory_newprod_amount').val(),
				'description': $('#inventory_newprod_name').val(),
				'category': $('#inventory_newprod_type').val()
			}).error(function(jqXHR, textStatus, errorThrown){
				alert(jqXHR.responseText);
			}).complete(function(){
				$('#inventory_newprod_amount').val('');
				$('#inventory_newprod_name').val('');
				$('#inventory_barcode').focus();
				$('#inventory_new_prod_div').slideUp();
				inventory_tab.submit_barcode($('#inventory_barcode').val());

			});
		});

		$('#inventory_commit_delete_barcode').button().click(function(){
			$.post('inventory/product', {
				'mode': 'delete',
				'barcode': $('#inventory_delete_barcode').val()
			}).error(function(data, resp, jqXHR){
				alert(jqXHR.responseText);
			}).success(function(data, resp, jqXHR){
				alert(jqXHR.responseText);
				$('#inventory_delete_barcode').val('');
			});
		});

		$('#inventory_commit_purchase').button().click(function(){
			purchases = {};
			purchases['description'] = $('#inventory_purchase_note').val();
			$('#inventory_purchase_note').val('');
			inventory_tab.new_inventory.forEach(function(purchase){
				if(!purchases[purchase.category]){
					purchases[purchase.category] = 0;
				}
				purchases[purchase.category] += purchase.num;
			});
			$.post('inventory/purchase', purchases, function(){
				inventory_tab.new_inventory = [];
				inventory_tab.redraw_current_scan();
				inventory_tab.reload_inventory_list();
				inventory_tab.reload_totals();

			}).error(function(jqXHR){
				alert(jqXHR.responseText);
			});
		});



		$('#inventory_tab').on('keyup', '.leftpane .valuefield', function(){
			var now = $(this).val();
			var ori = $('#' + $(this).prop('id').replace("balance", "original")).val();
			var field = $(this);
			var diff = now - ori;
			if(now === '' || isNaN(now) || diff === 0){
				diff = "&rArr;";
			}else if (diff>0){
				diff = "+" + diff;
			}
			field.siblings('.numchanged').html(diff);

			if(ori == now){
				field.removeClass('ui-state-highlight');
				field.removeClass('ui-state-error');
				field.siblings('.numchanged').addClass('hidden');
				field.siblings('.changedalert').addClass('hidden');
			}else if(now.match(/^-?[0-9]+$/)){
				field.removeClass('ui-state-error');
				field.addClass('ui-state-highlight');
				field.siblings('.changedalert').addClass('hidden');
				field.siblings('.numchanged').removeClass('hidden');
			}else{
				field.removeClass('ui-state-highlight');
				field.addClass('ui-state-error');
				field.siblings('.numchanged').addClass('hidden');
				field.siblings('.changedalert').removeClass('hidden');
			}
		});

		$('#admin_load_inventory').button().click(function(){
			inventory_tab.reload_totals();
		});
	},

	redraw_current_scan: function(){
		$('#inventory_current_scan').html('');

		for(var i = inventory_tab.new_inventory.length-1; i >=0; i--){
			var entry = $('<li/>');
			var content = $('<p/>').appendTo(entry);
			$('<span/>', {class:'inventory_description'}).html(inventory_tab.new_inventory[i].desc).appendTo(content);
			$('<span/>', {class:'inventory_amount'}).html(inventory_tab.new_inventory[i].num).appendTo(content);
			$('<span/>', {class:'inventory_cat_description'}).html(inventory_tab.new_inventory[i].categorydesc).appendTo(content);
			$('<button>', {id:'inventory_list_remove_' + i}).html('x').button().appendTo(content);

			entry.appendTo($('#inventory_current_scan'));

		}
	},

	submit_barcode: function(barcode){
		var jqXHR = $.getJSON('inventory/product', {'barcode': barcode}, function(data) {
			$('#inventory_new_prod_div').slideUp();

			inventory_tab.new_inventory.push(data);
			inventory_tab.redraw_current_scan();
			$('#inventory_barcode').val('');


		}).error(function(jqXHR, textStatus, errorThrown){
			if(jqXHR.status == 404){
				$('#inventory_new_prod_div').slideDown();
				$('#inventory_newprod_name').focus();
			}else{
				alert(jqXHR.responseText);
			}
		});
	},

	reload_inventory_list: function(){
		$.get('inventory/list', function(data){
			$('#inventory_list').html(data);
			$('.inventorydelete').button();
			$('.inventorynote').button();

		});
	},

	reload_totals: function(){
		$('#inventory').load('spinner', function(){
			$.get('inventory/total', function(data){
				$('#inventory').html(data);
				$('#commit_balance').button().click(function(){
					var vals = {};
					var correct = true;
					var error = "";
					vals['description'] = $('#inventory_balance_note').val()
					$('#inventory_tab .leftpane .valuefield').each(function(idx, value){
						var field = $(value);
						var name = field.prop('id').replace('_balance','').toUpperCase();
						if (field.val().match(/^-?[0-9]+$/)){
							vals[name] = parseInt(field.val(), 10);
						}else{
							error += 'Incorrect value: ' + $('#' + name.toLowerCase() + '_description').html() + ' ' + field.val() + '\n';
							correct = false;
						}
					});

					if(!correct){
						alert(error);
					}else{
						$.post('inventory/balance', vals, function(){
							inventory_tab.reload_inventory_list();
							inventory_tab.reload_totals();
						});
					}
				});
			});
		});
	}
};

system_user_tab = {
	setup: function(){
		

		$('#system_user_tab').on('click', '.systemuserbutton-input', function(){
			system_user_tab.system_user_options.load($(this).prop('id').split('-')[1]);
		});
		system_user_tab.reload_system_user_list();
		$('#add_system_user').button().click(function(e){
			e.preventDefault();
			$.post('system_user/new', {'name': $('#new_system_user_name').val(), 'password': $('#new_system_user_password').val()}, function(){
				$('#new_system_user_name').val('');
				$('#new_system_user_password').val('');
				system_user_tab.reload_system_user_list();
			}).error(function(jqXHR){
				alert(jqXHR.responseText);
			});
		});
	},

	selected_system_user: function(){
		if ($('.systemuserbutton-input:checked').length){
			return $('.systemuserbutton-input:checked').prop('id').split('-')[1];
		}
	},

	reload_system_user_list: function(reclick){
		reclick = typeof reclick !== 'undefined' ? reclick : false;

		var selected = system_user_tab.selected_system_user();

		$.get('system_user/list', function(data){
			$('#systemuserselect').html(data);
		}).success(function(){
			$('.systemuserbutton-input').button();
			if(reclick){
				$('#systemuser-' +selected).button().click();
			}
		});
	},

	system_user_options: {

		load: function(id){
			$.get('system_user/user', {'user': id}, function(data){
				$('#system_user_options').html(data);
			});
		},


		setup: function(){

			$('#system_user_tab').on('keyup', '.leftpane input[type=password]', function(){
				var field = $(this);
				if( $(this).val() === ""){
					field.removeClass('ui-state-highlight');
					field.next().addClass('hidden');
				}else{
					field.addClass('ui-state-highlight');
					field.next().removeClass('hidden');
				}
			});

			$('#system_user_tab').on('keyup', '.leftpane input[type=text]', function(){
				var field = $(this);

				activity = {'system_user' : system_user_tab.selected_system_user()};
				activity['field'] = field.attr('name');
				activity['value'] = field.val();

				$.get('consistent', activity, function(data){
					if(data == "True"){
						field.removeClass('ui-state-highlight');
						field.next().addClass('hidden');
					}else{
						field.addClass('ui-state-highlight');
						field.next().removeClass('hidden');
					}
				});

			});

			$('#delete_system_user').button().click(function(){
				$.post('system_user/delete',{'system_user': system_user_tab.selected_system_user()}, function(){
					system_user_tab.reload_system_user_list(false);
					$('#system_user_options').html("");
				}).error(function(jqXHR){
					alert(jqXHR.responseText);
				});
			});

			$('#revertchanges_system_user').button().click(function(){
				system_user_tab.reload_system_user_list(true);
			});
			$('#submitchanges_system_user').button().click(function(){
				$.post('system_user/edit',{'system_user': system_user_tab.selected_system_user(),
					'name': $('#system_user_name').val(),
					'password': $('#system_user_password').val(),
					'email': $('#system_user_email').val(),
					'admin': $('#is_admin').is(':checked'),
					'su': $('#is_su').is(':checked')
				},
					function(){
					system_user_tab.reload_system_user_list(true);
				}).error(function(jqXHR){
					alert(jqXHR.responseText);
				});
			});

		}

	}
};

export_tab = {
	setup: function(){
		$('#loadexportcontent').button().click(function(){
            $('#exportcontent').html("");
            $('#exportcontent').load('adminexportcontent');
        });
	},

	export_options: {
		setup: function(){
			$('.refreshbutton').button().click(function(){
				var id = $(this).prop('id').split('-')[1];
				$.get('adminmanageexport',{'export': id}, function(data){
					$('#progress-' + id).html(data);
					$('.exportbutton').button();
					$('.downloadbutton').button();
				});
			});

			$('.refreshbutton').button().click();

			$('#exports').on('click', '.exportbutton', function(){
				$(this).button('disable');
				$.get('adminmanageexport', {'export': $(this).prop('id').split('-')[1], 'start':'True'});
			});

			$('#exports').on('click', '.downloadbutton', function(){
				window.location.href = 'export/' + $(this).prop('id').split('-')[1];
			});
		}
	}
};

