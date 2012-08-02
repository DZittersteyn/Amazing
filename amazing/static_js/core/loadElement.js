function loadNewUserDialog(){
	$.get('newUser.html',function (data){
		$('body').append(data);
	})
	.success(function(){
		$('#edit_pk').val("");
		$('#edit_name').val("");
		$('#edit_address').val("");
		$('#edit_city').val("");
		$('#edit_bank_account').val("");
		$('#edit_email').val("");
		$('#edit_barcode').val("");
		$('#edit_pin').val("");
		$('#edit_pin').attr("hidden",true);
		//$('#has_pin').attr("checked", false);
		$('#has_pin').button().click(function(){
			if($('#has_pin').attr("checked") == "checked"){
				$('#edit_pin').attr("hidden",false);
			}else{
				$('#edit_pin').attr("hidden",true);
			}
		});

		$('#newUser').dialog({			
			close: function(){
				unloadEditUserDialog();
			},
			modal:true,
			autoOpen: false,
		    minWidth: 740,
		    title: 'Nieuwe gebruiker',
		    buttons: [{
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
							'has_passcode': $('#edit_pin').val() == "" ? "False" : "True",
							'passcode': $('#has_pin').prop("checked")?CryptoJS.SHA1($('#edit_pin').val()).toString():get_selected_user_pc(),															
						}).success(function(data){
							//init_userlist();
							unloadEditUserDialog();
							set_gui_user_by_id(data);
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
			$.getJSON("user/" + id,{"passcode": get_selected_user_pc()}, function(user){
				$('#edit_pk').val(user[0].pk);
				$('#edit_name').val(user[0].fields.name);
				$('#edit_address').val(user[0].fields.address);
				$('#edit_city').val(user[0].fields.city);
				$('#edit_bank_account').val(user[0].fields.bank_account);
				$('#edit_email').val(user[0].fields.email);
				$('#edit_barcode').val(user[0].fields.barcode);
				$('#edit_pin').val("");
				$('#edit_pin').attr("hidden",true);
				//$('#has_pin').attr("checked", false);
				$('#has_pin').button().click(function(){
					if($('#has_pin').attr("checked") == "checked"){
						$('#edit_pin').attr("hidden",false);
					}else{
						$('#edit_pin').attr("hidden",true);
					}
				});

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
									'has_passcode': $('#edit_pin').val() == "" ?"False":"True",
									'passcode': $('#has_pin').prop("checked")?CryptoJS.SHA1($('#edit_pin').val()).toString():get_selected_user_pc(),															
								}).success(function(data){
									//init_userlist();
									unloadEditUserDialog();
									set_gui_user_by_id(data);
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

function reloadLI(transid,id){
	$("#purchaseli-"+transid).load("transactionli-" + transid + ".html", function(){
		$(this).find('.checkboxwlabel').button().click(function(){
			$.post("transaction/" + transid + ".html",{'valid': $(this).prop("checked")})
			.complete(function(){
				set_gui_user_by_id(id);		
				reloadLI(transid, id);
			}).error(function(jqxhr){
				if(jqxhr.status = 409){
					alert("Onvoldoende Credits!")
				}
			});
		});
	});	
}

function loadUndoDialog(id){
	if(id){
		$.get('undodialog_'+id+'.html',function (data){
			$('body').append(data);
		})
		.success(function(){
			$('#expandOld').click(function(){
				$(this).next().slideToggle(400,'swing');
				$('#plusminus').toggleClass('plus');
			});


			$("#undoDialog li").each(function(){
				pattern = /purchaseli-(\d+)/;
				match = pattern.exec($(this).attr('id'));
				if(match){
					var transid = match[1];
					if($(this).parent('#undoDialogPurchaseList').length){
						$(this).find('.checkboxwlabel').button().click(function(){
							$.post("transaction/" + transid + ".html",{'valid': $(this).prop("checked")})
							.complete(function(){
								set_gui_user_by_id(id);		
								reloadLI(transid, id);
							}).error(function(jqxhr){
								if(jqxhr.status = 409){
									alert("Onvoldoende Credits!")
								}
							});
						});
					} else {
						$(this).find('.checkboxwlabel').button({disabled: true});;
					}
				}
			});







			$('#undoDialog').dialog({			
				close: function(){
					unloadUndoDialog();
				},
				resizable: false,
				modal: true,
				autoOpen: false,
			    width: 570,
			    height: 630,
			    title: 'Transactieoverzicht' + ' ' + $('#undo_user').html() ,
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
				/*Contant: function(){
					$.post('user/' + get_selected_user_id(), {'type':'credit',
													 'credittype':'CASH',
													    'amount' : $("#numLines").slider('value')
													})
					.complete(function(){
						set_gui_user_by_id(get_selected_user_id());
						unloadBuyLineDialog();
					});
				},*/
				Machtiging: function(){
					$.post('user/' + get_selected_user_id(), {'type':'credit',
													 'credittype':'DIGITAL', 
													     'amount': $("#numLines").slider('value') 
													 })
					.complete(function(){
						set_gui_user_by_id(get_selected_user_id());
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


