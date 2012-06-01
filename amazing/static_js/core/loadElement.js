function loadNewUserDialog(){
	$.get('newUser.html',function (data){
		$('body').append(data);
	})
	.success(function(){
		$('#edit_name').val("");
		$('#edit_address').val("");
		$('#edit_city').val("");
		$('#edit_bank_account').val("");
		$('#edit_email').val("");
		$('#edit_barcode').val("");
		$('#newUser').dialog({
			close: function(){
				unloadNewUserDialog();
			},
			modal:true,
			autoOpen: false,
			minWidth: 740,
			title: 'Nieuwe gebruiker',
			buttons:  [{
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
									'has_passcode': $('#has_pin').attr('checked')?true:false,
									'passcode': $('#edit_pin').val(),																									
								}).success(function(data){
									//init_userlist();
									unloadNewUserDialog();
									set_gui_user(data);
								});
							}
						},
					},
					{
						text: "Annuleer",
						click: function(){
							unloadNewUserDialog();
						},
					}],
		});
		init_on_screen_keyboards();
		$('#newUser').dialog('open').removeClass('hidden');	
	});
}

function unloadNewUserDialog(){
	$('#newUser').remove();
}

function loadEditUserDialog(id){
	if(id){
		$.get('newUser.html',function (data){
			$('body').append(data);
		})
		.success(function(){
			$.getJSON("user/" + id, function(user){
				console.log(user[0].pk);
				$('#edit_pk').val(user[0].pk);
				$('#edit_name').val(user[0].fields.name);
				$('#edit_address').val(user[0].fields.address);
				$('#edit_city').val(user[0].fields.city);
				$('#edit_bank_account').val(user[0].fields.bank_account);
				$('#edit_email').val(user[0].fields.email);
				$('#edit_barcode').val(user[0].fields.barcode);
				$('#edit_pin').val(user[0].fields.passcode);
				if(!user[0].fields.has_passcode){
					$('#edit_pin').attr("hidden",true);
				}
				$('#has_pin').attr("checked", user[0].fields.has_passcode);

				$('#has_pin').change(function(obj){
					console.log("flip");
					if($('#has_pin').attr("checked") == "checked"){
						$('#edit_pin').attr("hidden",false);
					}else{
						$('#edit_pin').attr("hidden",true);
					}
				})

				$('#newUser').dialog({			
					close: function(){
						unloadEditUserDialog();
					},
					modal:true,
					autoOpen: false,
				    minWidth: 740,
				    title: 'Wijzig gebruiker',
				    buttons: [{
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
									'has_passcode': $('#has_pin').attr('checked')?"True":"False",
									'passcode': $('#edit_pin').val(),															
								}).success(function(data){
									//init_userlist();
									unloadEditUserDialog();
									set_gui_user(data);
								});
							}
						},
					},
					{
						text: "Annuleer",
						click: function(){
							unloadEditUserDialog();
						},
					}]
				});

				init_on_screen_keyboards();
				$('#newUser').dialog('open').removeClass('hidden');
			});
		});
	}
}

function unloadEditUserDialog(){
	$('#newUser').remove();
}


function loadUndoDialog(id){
	if(id){
		$.get('undodialog_'+id+'.html',function (data){
			$('body').append(data);
		})
		.success(function(){

			//$('#undoDialogPurchaseList').selectable();
			$('.checkboxwlabel').button();
			$('#undoDialog').dialog({			
				close: function(){
					unloadUndoDialog();
				},
				modal:true,
				autoOpen: false,
			    width: 500,
			    height:600,
			    title: 'Transactieoverzicht',
			    buttons: [{
					text: "Sluiten",
					click: function(){
						unloadUndoDialog();
					},
				},],
			});
			
			$('#undoDialog').dialog('open').removeClass('hidden');

		});
	}
}

function unloadUndoDialog(){
	$('#undoDialog').remove();
}


function loadBuyLineDialog(){
	$.get('buyLine.html',function (data){
		$('body').append(data);
	})
	.success(function(){
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

		$('#buyLine_dialog').dialog({
			modal: true,
			autoOpen: false,
			minWidth: 400,
			minHeight: 120,
			close: function(){
				unloadBuyLineDialog();
			},
			buttons: {
				Contant: function(){
					$.post('user/' + get_selected_user_id(), {'type':'credit',
													 'credittype':'CASH',
													    'amount' : $("#numLines").slider('value')
													})
					.complete(function(){
						set_gui_user(get_selected_user_id());
						unloadBuyLineDialog();
					});
				},
				Machtiging: function(){
					$.post('user/' + get_selected_user_id(), {'type':'credit',
													 'credittype':'DIGITAL', 
													     'amount': $("#numLines").slider('value') 
													 })
					.complete(function(){
						set_gui_user(get_selected_user_id());
						unloadBuyLineDialog();
					});
				},
				Annuleer: function(){
					unloadBuyLineDialog()
				}
			}
		}).dialog('open');


	});
}

function unloadBuyLineDialog(){
	$('#buyLine_dialog').remove();
}

function loadNoCreditDialog(){
	$.get('noCredit.html',function (data){
		$('body').append(data);
	})
	.success(function(){
		$('#noCredit').dialog({
			modal: true,
			autoOpen: false,
			buttons: {
				Ok: function(){
					unloadNoCreditDialog();
				}
			},
			close: function(){
				unloadNoCreditDialog();
			}
		}).dialog('open').removeClass('hidden');
	});
}

function unloadNoCreditDialog(){
	$('#noCredit').remove();
}

function loadTransactionManagerDialog(){
}