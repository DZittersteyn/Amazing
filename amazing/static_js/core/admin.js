function setup(){
	$('#tabs').tabs();



	$('input').button().click(
		function(){
			$('#useroptions').load('adminoptions/' + $(this).prop('id').split('-')[1]+".html");

		});

}