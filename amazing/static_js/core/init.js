function get_selected_user_id(){
		return $('.ui-selected').attr("id").split('-')[1];
}

function set_user_spec_buttons(enable){
	if(enable){
		$('#buyline').button('enable');
		$('#undo').button('enable');
		$('#edituser').button('enable');
		$('#CANDYBIG').button('enable');
		$('#CANDYSMALL').button('enable');
		$('#BEER').button('enable');
		$('#CAN').button('enable');
		$('#SOUP').button('enable');
		$('#BREAD').button('enable');
		$('#SAUSAGE').button('enable'); 
		$('#BAPAO').button('enable');

	}else{
		$('#buyline').button('disable');
		$('#undo').button('disable');
		$('#edituser').button('disable');
		$('#CANDYBIG').button('disable');
		$('#CANDYSMALL').button('disable');
		$('#BEER').button('disable');
		$('#CAN').button('disable');
		$('#SOUP').button('disable');
		$('#BREAD').button('disable');
		$('#SAUSAGE').button('disable'); 
		$('#BAPAO').button('disable');
		
	}
}

function clear_selected(){
	$('#username').html("");
	$('#credit').html("");
	set_user_spec_buttons(false);
	$('.ui-selectee').removeClass('ui-selected');
	$('#purchases').html('');
}

function init_tabs(){
	$("#usertabs").tabs().addClass('ui-tabs-vertical ui-helper-clearfix');

	$("#usertabs li.tab").removeClass('ui-corner-top').addClass('ui-corner-left');

}

function init_selectables(){
	$( ".selectable" ).selectable();
	$( ".selection" ).addClass('ui-corner-bottom');
	$( ".selection" ).addClass('ui-corner-top');

	$(".selectable").bind("selectableselected", function() {
		set_gui_user(get_selected_user_id());			
	});
	
	$('.selectable').bind('selectableunselected', function(){
		clear_selected();
	});

	$("#usertabs").tabs().bind("tabsselect",function(){
		clear_selected();
	});
}

function set_gui_user(id, password){

}


function set_gui_user(id){
	$.getJSON("user/" + id, function(user){
		if(user[0].fields.passcode){
			
		}else{

			$('#username').html(user[0].fields.name);
			$('#credit').html(user[0].fields.credit);
			$('#usertabs').tabs("select", (user[0].fields.name.toLowerCase().charCodeAt(0)-'a'.charCodeAt(0))/2 +1);
			$('#user-'+id).addClass('ui-selected');
			set_user_spec_buttons(true);
			$('#purchases').load("user/" + id + "/purchases");
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
}


function init_buyline_dialog(){
	
}

function init_user_buttons(){
	$("#edituser").button()
		.button('disable')
		.click(function(){edit_user(get_selected_user_id())})
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
	$("#tabscontainer").load("userlist.html", function(){
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

function setup(){
	init_loading_dialog();
	init_product_buttons();
	init_user_buttons();
	init_userlist();
	init_timer();
	init_buyline_dialog();
	init_csrf_token();

}