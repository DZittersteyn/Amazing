function get_selected_user_id(){
		return $('.ui-selected span.hidden').first().text();
}


function clear_selected(){
	$('#username').html("");
	$('#credit').html("");
	$('.ui-selectee').removeClass('ui-selected');
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
	
	$("#usertabs").tabs().bind("tabsselect",function(){
		clear_selected();
	});
}


function set_gui_user(id){
	$.getJSON("user/" + id, function(user){
		$('#username').html(user[0].fields.name);
		$('#credit').html(user[0].fields.credit);
	});

}

function init_loading_dialog(){
	$('#loading').dialog({
		modal: true,
		autoOpen: false,
	})
	.ajaxStart(function(){
		$(this).dialog('open');
	})
	.ajaxStop(function(){
		$(this).dialog('close');
	});
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
				' 7 8 9 ',
				' {sp:1} 0 {sp:1}',
				' {accept}'
			],
			'shift': []
		},
	});
}


function init_nocredit_dialog(){
	$('#noCredit').dialog({
		modal: true,
		autoOpen: false,
		buttons: {
			Ok: function(){
				$(this).dialog('close');
			}
		}
	})
}

function init_buyline_dialog(){
	$('#dialog_buyline').dialog({
		modal: true,
		autoOpen: false,
		minWidth: 400,
		minHeight: 120,
		buttons: {
			Contant: function(){
				$.post('user/' + get_selected_user_id(), {'type':'credit',
												 'credittype':'CASH',
												    'amount' : $("#numLines").slider('value')
												})
				.complete(function(){
					setUser(get_selected_user_id());
					$('#dialog_buyline').dialog('close');
				});
			},
			Machtiging: function(){
				$.post('user/' + get_selected_user_id(), {'type':'credit',
												 'credittype':'DIGITAL', 
												     'amount': $("#numLines").slider('value') 
												 })
				.complete(function(){
					setUser(get_selected_user_id());
					$('#dialog_buyline').dialog('close');
				});
			},
			Annuleer: function(){
				$(this).dialog('close');
			}
		}
	});


	$('#numLines').slider({
		range:"min",
		min: 0,
		value: 1,
		max: 10,
		slide: function(event, ui){
			$("#txtNumLines").html(ui.value);
			$("#price").html(ui.value * 5);
			if(ui.value != 1){
				$("#denom").html("s");
			}else{
				$("#denom").html("");
			}
			$("#baas").html("&nbsp;");
		
			if(ui.value == 10){
				$("#baas").html("ALS EEN BAAS");
			}
			if(ui.value == 0){
				$("#baas").html("Nope.");
			}
		},
	});
}




function init_user_dialog(){
	$('#newUser').dialog({
		modal: true,
		autoOpen: false,
		minWidth: 750,
		minHeight: 310,
		buttons: {	

		},
	});
}

function setup(){
	init_loading_dialog();

	$(".productbutton").button();
	$("#buyline").button();
	$("#edituser").button()
		.click(function(){edit_user(get_selected_user_id())})
	$('#add').button()
		.click(function(){new_user()});

	$("#tabscontainer").load("userlist.html", function(){
		init_selectables();
		init_tabs(); 
		$(".productbutton").each(function(index){
			$(this).bind('click', function(){
				button_click($(this).attr('id'));
			});
		});
		$("#buyline").bind('click', function(){
			if(get_selected_user_id() != ""){
				$('#dialog_buyline').dialog('open');
			}
		})
	});

	init_user_dialog();
	init_on_screen_keyboards();
	init_buyline_dialog();
	init_nocredit_dialog();
	
}