function button_click(productID){

	if (purchases_free){
		$.post('activity/purchase_free', {
			'type': 'product',
			'productID': productID
		})
		.error(function(jqXHR){
			no_credit_dialog.load($.parseJSON(jqXHR.responseText).result);
		})
		.complete(function(jqXHR){
			response = $.parseJSON(jqXHR.responseText);

			$('#free_left').html(response.restrictions);
			$('#purchases').html(response.purchases);

		});
	} else if (site_user.selected_user_id() !== ""){
		$.post('user/', {
			'user'     : site_user.selected_user_id(),
			'passcode' : site_user.selected_user_pc(),
			'barcode'  : site_user.selected_user_bc(),

			'type':'product',
			'productID': productID})
		.success(function(){
			if(!purchases_free){
				$.idleTimer('destroy');
				$.idleTimer(3 * 1000);
				$(document).bind("idle.idleTimer", function(){
					reset();
					$.idleTimer('destroy');
					$.idleTimer(10*1000);
					$(document).bind('idle.idleTimer', function(){
						reset();
					});
				});
			}
		})
		.error(function(jqXHR){
			no_credit_dialog.load(jqXHR.responseText);
		})
		.complete(function(){
			site_user.update_user();
		});
	}
}

