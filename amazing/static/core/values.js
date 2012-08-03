function _(s){

	if(s.equals('')){
		return '';
	}else if(s.equals('Credits')){
		return 'Kruisjes';
	}else if(s.equals('credits')){
		return 'kruisjes';
	}else if(s.equals('user')){
		return 'gebruiker';
	}else if(s.equals('User')){
		return 'Gebruiker';
	}



	return s;

}