function get_selected_user_id(){
	return $('#user_id').html();
}

function get_selecting_user_id(){
	if($('.ui-selected').length){
		return $('.ui-selected').attr("id").split('-')[1];
	}else{
		return -1;
	}
}
function get_selected_user_pc(){
	return $('#passcode').html();
}


function set_user_spec_buttons(enable){
	var enableString = 'disable';
	if(enable){
		enableString = 'enable'
	}
	$('#buyline').button(enableString);
	$('#undo').button(enableString);
	$('#edituser').button(enableString);
	$('#CANDYBIG').button(enableString);
	$('#CANDYSMALL').button(enableString);
	$('#BEER').button(enableString);
	$('#CAN').button(enableString);
	$('#SOUP').button(enableString);
	$('#BREAD').button(enableString);
	$('#SAUSAGE').button(enableString); 
	$('#BAPAO').button(enableString);
	
}

function clear_selected(){
	$('#user_id').html("");
	$('#passcode').html("");
	$('#username').html("");
	$('#credit').html("");
	$('#barcode').html("");
	$('#purchases').html("");;
	set_user_spec_buttons(false);
	$('.ui-selected').removeClass('ui-selected');
}

function init_tabs(){
	$("#usertabs").tabs({
		ajaxOptions: {
			success: function(data, textstatus, jqxhr){
				var cp =  $("#usertabs").tabs('option','selected');
				var up = Math.floor(($("#username").html().toLowerCase().charCodeAt(0)-'a'.charCodeAt(0))/2) +1;
				init_selectables();
				if(cp != up){
					clear_selected();
				}else{
					$('#user-' + get_selected_user_id()).addClass('ui-selected');
				}
			},
		},
		show: function(event, ui){
			if(ui.index == 0){
				$('#barcodeselect').focus();
				clear_selected();
			}
				
		}
	})

	$("#usertabs").addClass('ui-tabs-vertical ui-helper-clearfix');

	$("#usertabs li.tab").removeClass('ui-corner-top').addClass('ui-corner-left');

	init_barcode_submit();

}

function init_selectables(){
	$( ".selectable" ).selectable({
		selected: function() {
			set_gui_user_by_id(get_selecting_user_id());			
		},
		unselected: function(){
			clear_selected();
		},
	});
	$( ".selection" ).addClass('ui-corner-bottom');
	$( ".selection" ).addClass('ui-corner-top');

}

function set_gui_user_pc(passcode){
	$('#passcode').html(CryptoJS.SHA1(passcode).toString());
}

function init_expandables(){
	$('.expandable').click(function(){
		$($(this).find('div')[1]).toggle(400,'swing');
	});
}

function set_gui_user(user){

	if(user){
		$('#purchases').load("user/" + user.pk + "/purchases", function(){
			init_expandables();
		});
		$('#username').html(user.fields.name);
		$('#credit').html(user.fields.credit);
		$('#barcode').html(user.fields.barcode);
		$('#user_id').html(user.pk);
		$('#usertabs').tabs("select", (user.fields.name.toLowerCase().charCodeAt(0)-'a'.charCodeAt(0))/2 +1);
		$('#user-'+user.pk).addClass('ui-selected');
		set_user_spec_buttons(true);
	}
}

function set_gui_user_by_id(id, barcode){
	passcode = get_selected_user_pc();

	$.getJSON("user/" + id, {'passcode': passcode, 'barcode':barcode}, function(user){
		set_gui_user(user[0]);
	})
	.error(function(jqxhr){
		if(jqxhr.status == 401){
			$('#purchases').load("passcode.html",function(){
				init_on_screen_keyboards();
				$('#pin_input').focus();
			});
		}
	});
}

function init_loading_dialog(){
	$('#loading').dialog({
		modal: true,
		autoOpen: false,
	})
	/*.ajaxStart(function(){
		$(this).dialog('open');
	})
	.ajaxStop(function(){
		$(this).dialog('close');
	}).removeClass('hidden')*/;
}

function init_on_screen_keyboards(){
	$(".osk_norm").keyboard({
		layout: "custom",
		openOn: "click",
		autoAccept: true,
		stickyShift: false,
		customLayout : {
			'default': [
				'` 1 2 3 4 5 6 7 8 9 0 - = {bksp}',
				'{sp:1} q w e r t y u i o p [ ] \\',
				'a s d f g h j k l ; \' ',
				'{shift} z x c v b n m , . / {shift}',
				'{cancel} {space} {accept}'
			],
			'shift': [
				'~ ! @ # $ % ^ & * ( ) _ + {bksp}',
				'{tab} Q W E R T Y U I O P { } |',
				'A S D F G H J K L : " {enter}',
				'{shift} Z X C V B N M < > ? {shift}',
				'{cancel} {space} {accept}'
			]
		},
	});


	$(".osk_mail").keyboard({
		layout: "custom",
		openOn: "click",
		autoAccept: true,
		stickyShift: false,
		customLayout : {
			'default': [
				' 1 2 3 4 5 6 7 8 9 0 -  {bksp}',
				'q w e r t y u i o p {sp:2}',
				'a s d f g h j k l {sp:2}',
				'{sp:3} z x c v b n m {sp:1} + @ . {sp:2}',
				'{cancel} {space} {accept}'
			],
			'shift': []
		},
	});

	$(".osk_bank").keyboard({
		layout: "custom",
		openOn: "click",
		autoAccept: true,
		stickyShift: false,
		customLayout : {
			'default': [
				'{sp:2} 1 2 3 {bksp}',
				      ' 4 5 6 ',
				'{sp:2} 7 8 9 {accept}',
				'  {sp:1} 0 {sp:1}',
				
			],
			'shift': []
		},
	});

	$(".osk_pin").keyboard({
		layout: "custom",
		openOn: "focus",
		accepted: function(e, keyboard, el){
			set_gui_user_pc(el.value);
			//keyboard.destroy();
			set_gui_user_by_id(get_selecting_user_id());
		},
		customLayout : {
			'default': [
				'{sp:2} 1 2 3 {bksp}',
				      ' 4 5 6 ',
				'{sp:2} 7 8 9 {accept}',
				'  {sp:1} 0 {sp:1}',
				
			],
			'shift': []
		},
	});




}


function init_buyline_dialog(){
	
}

function init_user_buttons(){
	$("#edituser").button()
		.button('disable')
		.click(function(){edit_user(get_selected_user_id(),get_selected_user_pc(), get_selected_user_bc());})
		.addClass('doubleheightbutton');
	$('#add').button()
		.click(function(){new_user()})
		.addClass('doubleheightbutton');
	$('#undo').button()
		.click(function(){undo(get_selected_user_id())})
		.button('disable')
		.addClass('doubleheightbutton');
	$("#buyline").button()
		.button('disable')
		.addClass('doubleheightbutton')
		.click(function(){
			if(get_selected_user_id() != ""){
				loadBuyLineDialog();
			}
		});	

}

function init_product_buttons(){
	$(".productbutton").button().button('disable');

	$(".productbutton").each(function(index){
		$(this).bind('click', function(){
			button_click($(this).attr('id'));
		});
	});
}

function init_userlist(){
	$("#usertabs").load("userlist.html", function(){
		init_selectables();
		init_tabs(); 
		
	});	
}

function init_timer(){
/* TODO: Enable me!
$.idleTimer(10 * 1000);
$(document).bind("idle.idleTimer", function(){
	reset();
});
*/
}

function init_csrf_token(){
	$(document).ajaxSend(function(event, xhr, settings) {
	    function getCookie(name) {
	        var cookieValue = null;
	        if (document.cookie && document.cookie != '') {
	            var cookies = document.cookie.split(';');
	            for (var i = 0; i < cookies.length; i++) {
	                var cookie = jQuery.trim(cookies[i]);
	                // Does this cookie string begin with the name we want?
	                if (cookie.substring(0, name.length + 1) == (name + '=')) {
	                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
	                    break;
	                }
	            }
	        }
	        return cookieValue;
	    }
	    function sameOrigin(url) {
	        // url could be relative or scheme relative or absolute
	        var host = document.location.host; // host + port
	        var protocol = document.location.protocol;
	        var sr_origin = '//' + host;
	        var origin = protocol + sr_origin;
	        // Allow absolute or scheme relative URLs to same origin
	        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
	            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
	            // or any other URL that isn't scheme relative or absolute i.e relative.
	            !(/^(\/\/|http:|https:).*/.test(url));
	    }
	    function safeMethod(method) {
	        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
	    }

	    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
	        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
	    }
	});
}

function init_barcode_submit(){
	$('#barcodeselect').keypress(function(e){
		if(e.which == 13){
			$('#barcodeselect').removeClass('error');
			e.preventDefault();
			var barcode = $('#barcodeselect').val();
			if(barcode == ""){
				return;
			}
			$('#barcodeselect').val("");
			$.getJSON('user/barcode', {'barcode': barcode}, function(user){
				set_gui_user(user[0]);
			})
			.error(function(jqxhr,txtstatus, error){
				if(jqxhr.status == 404){ //no such user
					$('#barcodeselect').addClass('ui-state-error');
				}else if(jqxhr.status == 409){ //multiple users
					alert(jqxhr.responseText);
				}
			});
		}
	});
}

function setup(){

	init_loading_dialog();
	init_product_buttons();
	init_user_buttons();
	init_userlist();
	init_timer();
	init_buyline_dialog();
	init_csrf_token();

}