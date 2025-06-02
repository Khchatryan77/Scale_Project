import utime
from machine import Pin, I2C
from framebuf import FrameBuffer, MONO_VLSB


# Initialize I2C
i2c = I2C(1, scl=Pin(27), sda=Pin(26), freq=400000)

# SSD1306 I2C address
addr = 0x3C  # Update if scan shows different address (e.g., 0x3D)

# Send command helper
def send_cmd(cmd):
    i2c.writeto(addr, bytes([0x00, cmd]))  # 0x00 = command byte
    utime.sleep_ms(1)


# Initialize SSD1306
send_cmd(0xAE)  # Display off
send_cmd(0xA8); send_cmd(0x3F)  # Set multiplex
send_cmd(0xD5); send_cmd(0x80)  # Display clock
send_cmd(0x8D); send_cmd(0x14)  # Charge pump
send_cmd(0x20); send_cmd(0x00)  # Memory mode
send_cmd(0xA1)  # Segment remap
send_cmd(0xC8)  # Scan direction
send_cmd(0xDA); send_cmd(0x02)  # COM pins
send_cmd(0x81); send_cmd(0xCF)  # Contrast
send_cmd(0xD9); send_cmd(0xF1)  # Precharge
send_cmd(0xDB); send_cmd(0x40)  # VCOMH
send_cmd(0xA4)  # Display RAM
send_cmd(0xA6)  # Normal display
send_cmd(0xAF)  # Display on

# Initialize framebuffer
buffer = bytearray(128 * 32 // 8)
fb = FrameBuffer(buffer, 128, 32, MONO_VLSB)


def oled():
    fb.fill(0)
    i2c.writeto_mem(addr, 0x40, buffer)
    utime.sleep(0.5)
    print('Initalization')


    fb.text("Initialization", 0, 0,  1)
    fb.text("Starting...", 0, 16,  1)
    # fb.line(127,0,0,31,1)
    i2c.writeto_mem(addr, 0x40, buffer)
    utime.sleep(0.5)


def weight_oled(input, input2):
    fb.fill(0)
    i2c.writeto_mem(addr, 0x40, buffer)
    utime.sleep_ms(10)
    print('Weight Load CLean')

    fb.text("Scale_1: "+ str(input) + "g" , 0, 0, 1)
    fb.text("Scale_2: " + str(input2) + "g", 0, 20, 1)
    i2c.writeto_mem(addr, 0x40, buffer)
    utime.sleep_ms(10)
    return print('Weight Load Measure')

    # fb.text("Count: "+ str(input2) + "g" , 0, 20, 1)
    # i2c.writeto_mem(addr, 0x40, buffer)
    # utime.sleep_ms(10)
    # return print('Weight Load Measure')


