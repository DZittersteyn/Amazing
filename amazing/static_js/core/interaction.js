function button_click(productID){
	if (get_selected_user_id() != ""){
		$.post('user/' + get_selected_user_id(), {'type':'product', 'productID': productID})
		.success(function(){
			/* TODO: enable me :D
			$.idleTimer(3 * 1000);
			$(document).bind("idle.idleTimer", function(){
				$.idleTimer(10*1000);
				$(document).bind("idle.idleTimer", function(){
					reset();
				});				

			});
			*/
		})
		.error(function(){
			loadNoCreditDialog();
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
	loadNewUserDialog();
}


function edit_user(id){
	loadEditUserDialog(id);
}
