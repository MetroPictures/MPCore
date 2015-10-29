from Button import Button

def test_callback(gpio, level, tick):
	print "Button callback triggered!"
	print gpio, level, tick

button = Button(23, callback=test_callback)

raw_input("Press Enter when ready...")
print "Waiting for input"

while True:
	try:
		sleep(0.01)
	except KeyboardInterrupt:
		print "Interrupted!"

button.unlisten()
button.pig.stop()