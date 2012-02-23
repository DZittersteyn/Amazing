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
	reset_field('#name');
	reset_field('#email');
	reset_field('#bank_account');
	reset_field('#address');
	reset_field('#city');
}

function check_fields(){
	var valid = true;
	valid = set_field_valid($('#email').val() == "" || is_valid_email_address($('#email').val()), '#email') 
				&& valid;

	valid = set_field_valid(is_valid_bank_account($('#bank_account').val()), '#bank_account') 
				&& valid;

	valid = set_field_valid($('#name').val() != "", '#name') 
				&& valid;

	valid = set_field_valid($('#address').val() != "", '#address') 
				&& valid;

	valid =set_field_valid($('#barcode').val() != "", '#barcode') 
				&& valid;

	valid = set_field_valid($('#city').val() != "", '#city') 
				&& valid;

	return valid;

}

function new_user(){
	$('#name').val("");
	$('#address').val("");
	$('#city').val("");
	$('#bank_account').val("");
	$('#email').val("");
	$('#barcode').val("");
	$('#newUser').dialog('option', 'title', 'Nieuwe gebruiker')
	$('#newUser').dialog('option', 'buttons', [{
										text: "Maak aan",
										click: function(){
											if(check_fields()){
												$.post('user/', {
													'name', 

												}).success(function(){
													$('#newUser').dialog('close');
												}
											}

										},
									},
									{
										text: "Annuleer",
										click: function(){
											$(this).dialog('close');
										},
									}]);
	$('#newUser').dialog('open');
}


function edit_user(id){

	$.getJSON("user/" + id, function(user){
		$('#name').val(user[0].fields.name);
		$('#address').val(user[0].fields.address);
		$('#city').val(user[0].fields.city);
		$('#bank_account').val(user[0].fields.bank_account);
		$('#email').val(user[0].fields.email);
		$('#barcode').val(user[0].fields.barcode);
		$('#newUser').dialog('option', 'title', 'Wijzig gebruiker')
		$('#newUser').dialog('option', 'buttons' [{
									text: "Sla op",
									click: function(){
										


										$(this).dialog('close');
									},
								},
								{
									text: "Annuleer",
									click: function(){
										$(this).dialog('close');
									},
								}]);
		$('#newUser').dialog('open');
	});
}
