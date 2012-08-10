function setup_admin(){
	$('#tabs').tabs();


	$('#adduser').button().click(function(){
		loadNewUserDialog();
	});

	$('#filterinactive').button().click(function(){
		if($(this).is(":checked")){
			$(".nonactive").addClass("hidden");
		}else{
			$(".nonactive").removeClass("hidden");
		}
	});

	reload_admin_userlist();


	init_csrf_token();
}

function reload_admin_userlist(selected){
	$('#userselect').load('adminuserlist.html', function(){
		console.log("jeej");

		if($("#filterinactive").is(":checked")){
			$(".nonactive").addClass("hidden");
		}else{
			$(".nonactive").removeClass("hidden");
		}

		$('.userbutton-input').button().click(function(){
				$('#useroptions').load('adminoptions/' + $(this).prop('id').split('-')[1]+".html");
		});
		if(selected){
			$(selected).button().click();
		}
	});
}

function setup_admin_useroptions(){

	$('#removeuser').button().click(function(){
		$.post('user/' + admin_get_selected_user() + "/remove");
	});

	$('#edituser').button().click(function(){
		console.log("lol");
		edit_user(admin_get_selected_user(), admin_get_selected_pc(), admin_get_selected_bc());
	});

	$('#setactive').buttonset();
	$('#activate').click(function(){
		var selected = admin_get_selected_user()
		$.post('user/' + selected +'/activate');
		reload_admin_userlist("#user-" + selected);
	});
	$('#deactivate').click(function(){
		var selected = admin_get_selected_user()
		$.post('user/' + selected +'/deactivate');
		reload_admin_userlist("#user-" + selected);


	});

}

function admin_get_selected_user(){
	return $('#pk').html();
}

function admin_get_selected_pc(){
	return $('#passcode').html();
}

function admin_get_selected_bc(){
	return $('#barcode').html();
}
