function button_click(productID){
	if (site_user.selected_user_id() !== ""){
		$.post('user/', {
			'user'     : site_user.selected_user_id(),
			'passcode' : site_user.selected_user_pc(),
			'barcode'  : site_user.selected_user_bc(),

			'type':'product',
			'productID': productID})
		.success(function(){
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
			
		})
		.error(function(){
			no_credit_dialog.load();
		})
		.complete(function(){
			site_user.update_user();
		});
	}
}

