function button_click(productID){
	if (get_selected_user_id() != ""){
		$.post('user/' + get_selected_user_id(), {'type':'product', 'productID': productID})
		.success()
		.error(function(){
			$('#noCredit').dialog('open');
		})
		.complete(function(){
			set_gui_user(get_selected_user_id());
		});
	}
}

function is_valid_email_address(email) {
	var pattern = new RegExp(/^[+a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+$/i);
	return pattern.test(email);
}

function is_valid_bank_account(bank_account){

	/*TODO: digit check. */
	var pattern = new RegExp(/^[0-9]+$/i);
	return pattern.test(bank_account);	
}

function set_field_valid(valid, field){
	if(valid){
		$(field).removeClass('ui-state-error');
		$(field).addClass('ui-state-success');
	}else{
		$(field).addClass('ui-state-error');
		$(field).removeClass('ui-state-success');
	}
	return valid;
}
function reset_field(field){
	$(field).removeClass('ui-state-error');
	$(field).removeClass('ui-state-success');
}

function reset_fields(){
	reset_field('#edit_name');
	reset_field('#edit_email');
	reset_field('#edit_bank_account');
	reset_field('#edit_address');
	reset_field('#edit_city');
}

function check_fields(){
	var valid = true;
	valid = set_field_valid($('#edit_email').val() == "" || is_valid_email_address($('#edit_email').val()), '#edit_email') 
				&& valid;

	valid = set_field_valid(is_valid_bank_account($('#edit_bank_account').val()), '#edit_bank_account') 
				&& valid;

	valid = set_field_valid($('#edit_name').val() != "", '#edit_name') 
				&& valid;

	valid = set_field_valid($('#edit_address').val() != "", '#edit_address') 
				&& valid;

	valid =set_field_valid($('#edit_barcode').val() != "", '#edit_barcode') 
				&& valid;

	valid = set_field_valid($('#edit_city').val() != "", '#edit_city') 
				&& valid;

	return valid;

}

function new_user(){
	$('#edit_name').val("");
	$('#edit_address').val("");
	$('#edit_city').val("");
	$('#edit_bank_account').val("");
	$('#edit_email').val("");
	$('#edit_barcode').val("");
	$('#newUser').dialog({
							modal:true,
							autoOpen: false,
						});
	$('#newUser').dialog('option', 'minWidth', 740);
	$('#newUser').dialog('option', 'title', 'Nieuwe gebruiker')
	$('#newUser').dialog('option', 'buttons',  [{
													text: "Maak aan",
													click: function(){
														if(check_fields()){
															$.post('user/', {
																'mode': 'new',
																'name': $('#edit_name').val(),
																'address': $('#edit_address').val(),
																'city': $('#edit_city').val(),
																'bank_account': $('#edit_bank_account').val(),
																'email': $('#edit_email').val(),
																'barcode': $('#edit_barcode').val(),																
															}).success(function(data){
																console.log(data);
																init_userlist();
																set_gui_user(data);
																$('#newUser').dialog('close');
															});
														}
													},
												},
												{
													text: "Annuleer",
													click: function(){
														$(this).dialog('close');
													},
												}]);
	$('#newUser').dialog('open').removeClass('hidden');
}


function edit_user(id){

	$.getJSON("user/" + id, function(user){
		$('#edit_pk').val(user[0].pk);
		$('#edit_name').val(user[0].fields.name);
		$('#edit_address').val(user[0].fields.address);
		$('#edit_city').val(user[0].fields.city);
		$('#edit_bank_account').val(user[0].fields.bank_account);
		$('#edit_email').val(user[0].fields.email);
		$('#edit_barcode').val(user[0].fields.barcode);
		$('#newUser').dialog({
							modal:true,
							autoOpen: false,
						});
		$('#newUser').dialog('option', 'minWidth', 740);
		$('#newUser').dialog('option', 'title', 'Wijzig gebruiker')
		$('#newUser').dialog('option', 'buttons', [{
													text: "Sla op",
													click: function(){
														if(check_fields()){
															$.post('user/', {
																'mode': 'edit',
																'pk': $('#edit_pk').val(),
																'name': $('#edit_name').val(),
																'address': $('#edit_address').val(),
																'city': $('#edit_city').val(),
																'bank_account': $('#edit_bank_account').val(),
																'email': $('#edit_email').val(),
																'barcode': $('#edit_barcode').val(),																
															}).success(function(){
																init_userlist();
																set_gui_user($('#edit_pk').val());
																$('#newUser').dialog('close');
															});
														}
													},
												},
												{
													text: "Annuleer",
													click: function(){
														$(this).dialog('close');
													},
												}]);
		
		$('#newUser').dialog('open').removeClass('hidden');
	});
}
