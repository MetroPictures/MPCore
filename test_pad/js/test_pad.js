$(document).ready(function() {
	var buttons = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'];
	var generate_letters = function() {
		var l_buffer = [];
		var c_pickup = 65;

		for(var l=0; l<buttons.length; l++) {
			l_buffer.push([]);

			if(l == 0 || l > 8) {
				continue;
			}

			var l_length = (l == 6 || l == 8) ? 4 : 3;

			for(c=c_pickup; c < (c_pickup + l_length); c++) {
				l_buffer[l_buffer.length - 1].push(String.fromCharCode(c));
			}

			c_pickup += l_length;
		}

		return l_buffer;
	};

	var b_count = 0;
	var letters = generate_letters();

	var hup = "hang_up";
	var pup = "pick_up";

	$("#mp_receiver")
		.html(pup)
		.click(function() {
			if($(this).html() == hup) {
				next_state = pup;
			} else if($(this).html() == pup) {
				next_state = hup;
			}

			$.ajax({
				url : $(this).html(),
				context : this
			}).done(function(json) {
				console.info(json);				
				$(this).html(next_state);
			});
		});
	
	for(var i=0; i<4; i++) {
		var tr = $(document.createElement('tr'));
		for(var j=0; j<3; j++) {
			var html = "<p class=\"num\">" + buttons[b_count] + "</p>";
			if(letters[b_count].length != 0) {
				html += "<p class=\"lett\">" + letters[b_count].join("") + "</p>";
			}

			var td = $(document.createElement('td'));
			var a = $(document.createElement('a'))
				.html(html)
				.click(function() {
					var mapping = $($(this).find('.num')[0]).html();
					if(mapping == '*') {
						mapping = '12';
					} else if(mapping == '0') {
						mapping = '13';
					} else if(mapping == '#') {
						mapping = '14';
					} else {
						mapping = Number(mapping) + 2;

					}

					$.ajax({
						url : "mapping/" + mapping
					}).done(function(json) {
						console.info(json);
					});
				});

			$(td).append(a);
			$(tr).append(td);

			b_count ++;
		}

		$("#mp_main").append(tr);
	}
});