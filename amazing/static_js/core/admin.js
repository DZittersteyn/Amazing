admin = {
	setup: function(){
		$('.tabs').tabs();


		user_tab.setup();
		activity_tab.setup();
		inventory_tab.setup();
		system_user_tab.setup();


		$('#filter_inactive_users').button().click(function(){
			if($(this).is(":checked")){
				$(".nonactive").addClass("hidden");
			}else{
				$(".nonactive").removeClass("hidden");
			}
		});

		site_gui.init_csrf_token();
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
			$.get('adminoptions', {'user': user_tab.selected_user()}, function(data){
				$('#useroptions').html(data);
			});
		},

		setup: function(){
			$('#commit_purchase').button().button('disable').click(function(){
				purchase = user_tab.get_auth();
				purchase['type'] = 'product';
				purchase['activity'] = $('#activities').val();
				purchase['admin'] = 'admin';
				$('.valuefield').each(function(){
					purchase['productID'] = this.id;
					purchase['amount'] = this.value;
					$.post('user/', purchase);
				});
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
					}else{
						$('#commit_purchase').button('enable').children().html('Purchase in activity "<span class="actlabel"></span>"');
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


			$('#user_tab').on('keyup', 'input[type=text]', function(){
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
				activity_tab.reload_activitylist();
			});
		});

		activity_tab.reload_activitylist();

		$('#activity_tab').on('click', '.activitybutton-input', function(){
			$.get('activityoptions', {'activity': $(this).prop('id').split('-')[1]}, function(data){
				$('#activityoptions').html(data);
			});
		});


		$('#activity_tab').on('keyup', 'input[type=text]', function(){
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

	reload_activitylist: function(){

		$.get('adminactivitylist', function(data){
			$('#activityselect').html(data);
		}).success(function(){
			$('.activitybutton-input').button();
		});


	},

	selected_activity: function(){
		if ($('.activitybutton-input:checked')){
			return $('.activitybutton-input:checked').prop('id').split('-')[1];
		}
	}

};

inventory_tab = {
	setup: function(){

	}
};

system_user_tab = {
	setup: function(){

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
				console.log($(this));
				$(this).button('disable');
				$.get('adminmanageexport', {'export': $(this).prop('id').split('-')[1], 'start':'True'});
			});

			$('#exports').on('click', '.downloadbutton', function(){
				window.location.href = 'export/' + $(this).prop('id').split('-')[1];
			});
	    }
	}
};

