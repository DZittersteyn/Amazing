function setup_admin(){
	$('#tabs').tabs();
	$('#userselect > button').button();
	$('#adduser').click(function(){loadNewUserDialog();});



	$('input').button().click(
		function(){
			$('#useroptions').load('adminoptions/' + $(this).prop('id').split('-')[1]+".html");
		});

	init_csrf_token();

}