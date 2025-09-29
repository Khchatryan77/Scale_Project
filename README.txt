PROTOCOL UART 
- BAUDRATE = 128000
- DATABITS = 8
- PARITY = NONE
- STOP BIT 1

RECEIVED COMMANDS. 

 - @WHO 
	- RESPONSE SEND '@SCALE' + '\r\n'

 - @RESET 
	- RESPONSE SEND '@OK' + '\r\n'

 - @scale_1_clean

	- RESPONSE SEND '@OK' + '\r\n'

 - @scale_2_clean

	- RESPONSE SEND '@OK' + '\r\n'

 - ANKNOWN COMMAND
 
	- RESPONSE SEND '@ERROR' + '\r\n'

When measurement difference is larger than 2000g UART SEND. 
 
	IN FIRST SCALE 
- '@BOX_1 IS REMOVED' + '\r\n'

	IN SECOND SCALE
- '@BOX_2 IS REMOVED' + '\r\n'