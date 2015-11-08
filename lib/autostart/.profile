source ~/.mp_profile

PADDING_Y=5
PADDING_X=5
PANEL_WIDTH=40

function sculpture_pad_y {
	for i in $(seq $PADDING_Y); do
		echo ""
	done
}

function sculpture_pad_x {
	for i in $(seq $PADDING_X); do
		echo -en " "
	done
}

function sculpture_end_line {
	sculpture_pad_x
	printf "%0.s*" $(seq $PANEL_WIDTH)
	echo ""
}

function sculpture_blank_line {
	sculpture_pad_x
	printf "*"
	
	for b in $(seq $(($PANEL_WIDTH-2))); do
		echo -en " "
	done
	
	printf "*"
	echo ""
}

function sculpture_set_words {
	sculpture_pad_x
	printf "* $1"

	for b in $(seq $(($PANEL_WIDTH-${#1}-3))); do
		echo -en " "
	done

	printf "*"
	echo ""
}

sculpture_pad_y
sculpture_end_line
sculpture_blank_line
sculpture_set_words "$SCULPTURE_TITLE"
sculpture_blank_line
sculpture_blank_line
sculpture_set_words "CAMILLE HENROT x DEEPLAB (c) 2015"
sculpture_set_words "warez by Harlo Holmes (@harlo)"
sculpture_blank_line
sculpture_set_words $SCULPTURE_LINK
sculpture_blank_line
sculpture_blank_line
sculpture_end_line
sculpture_pad_y

