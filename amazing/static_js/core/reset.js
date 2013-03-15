function reset(){
    console.log('reset');
	site_gui.clear_selected();
	$("#usertabs").tabs("option", "selected", 0);
    $('#product_scan').slideUp();
    $('#productselect').val('');
    $('#barcodeselect').val('');
    $('#barcodeselect').prop('disabled',false);
    $('#barcodeselect').focus();
    $('#barcodeselect').removeClass('ui-state-error');

}