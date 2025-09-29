from machine import Pin, UART
import machine
import time

time.sleep(8)
import _thread


uart1 = UART(0, baudrate=128000, tx=Pin(0), rx=Pin(1))
from ssd1306 import  oled, weight_oled

oled()

# Define GPIO pins
DT_PIN = 4  # Data pin (DOUT)
DT_PIN_2 = 8  # Data pin (DOUT)

SCK_PIN = 5  # Clock pin (PD_SCK)
SCK_PIN_2 = 9  # Clock pin (PD_SCK)

reset_done = None
counter = 0

Led_pin = 28
Led = Pin(Led_pin, Pin.OUT)

Button_pin = 29

Button_pin_1 = 11
Button_pin_2 = 12

# Initialize pins
dt = Pin(DT_PIN, Pin.IN)
sck = Pin(SCK_PIN, Pin.OUT)

dt_2 = Pin(DT_PIN_2, Pin.IN)
sck_2 = Pin(SCK_PIN_2, Pin.OUT)

Button_pin = Pin(Button_pin, Pin.IN,  Pin.PULL_UP)

Button_pin_1 = Pin(Button_pin_1, Pin.IN,  Pin.PULL_UP)
Button_pin_2 = Pin(Button_pin_2, Pin.IN,  Pin.PULL_UP)

class HX711:
    def __init__(self, dout, pd_sck, gain=64):
        self.dout = dout
        self.pd_sck = pd_sck
        self.offset = 0
        self.scale = 106  # Default scale factor
        self.gain = gain  # 128 for channel A, 64 for channel A, 32 for channel B

    def is_ready(self):
        return self.dout.value() == 0

    def read(self):
        """Read raw 24-bit value from HX711."""
        while not self.is_ready():
            pass

        count = 0
        for i in range(24):
            self.pd_sck.value(1)
            self.pd_sck.value(0)
            count = count << 1
            if self.dout.value():
                count += 1

        # Set gain/channel for next reading
        for i in range(self.gain == 128 and 1 or self.gain == 64 and 3 or 2):
            self.pd_sck.value(1)
            self.pd_sck.value(0)

        # Handle 2's complement
        if count & 0x800000:
            count -= 0x1000000

        return count

    def read_average(self, times=10):
        """Read average of multiple readings."""
        total = 0
        for _ in range(times):
            total += self.read()
        return total // times

    def tare(self, times=10):
        """Tare the scale by setting offset."""
        self.offset = self.read_average(times)
        print("Tare complete.")

    def get_weight(self, times=10):
        """Get weight in grams using scaling factor."""
        raw = self.read_average(times)
        return (raw - self.offset) / self.scale

    def power_down(self):
        """Power down HX711."""
        self.pd_sck.value(1)
        time.sleep_us(20)

    def power_up(self):
        """Power up HX711."""
        self.pd_sck.value(0)
        time.sleep_us(20)

hx = HX711(dt, sck, gain=64)

hx2 = HX711(dt_2, sck_2, gain=64)

def calibrate(a):
    """Calibrate the scale using a known weight."""
    print("Remove any weight from the scale and press Enter in the REPL to tare.")
    input()  # Wait for user input via REPL

    # Tare the scale
    a.tare()
    print("Tare complete. Place a known weight on the scale and enter its weight in grams.")


    try:
        known_weight = float(input("Enter the known weight (grams): "))
        print("Reading weight...")

        # Take an average of 10 readings
        raw_value = a.read_average(10) - a.offset
        print("Raw value (after offset):", raw_value)

        # Calculate scaling factor (raw_value / known_weight)
        scaling_factor = raw_value / known_weight
        print("Scaling factor:", scaling_factor)

        return scaling_factor
    except ValueError:
        print("Invalid input. Calibration failed.")
        return None

def uart_send(message):
    try:
        uart1.write(message.encode('utf-8'))

        print("Sent string:", message.strip())
        time.sleep_ms(1)

    except Exception as e:
        print("UART send error:", e)

def core_1():
    global uart_send

    while True:
        uart_send()
        time.sleep_ms(10)

def uart_receive(uart1):

    try:
        if uart1.any():

            decoded = uart1.readline().decode().strip()
            print("Received string:", decoded)

            if decoded == "@WHO":
                uart_send('@SCALE' + '\r\n')
                return None

            elif decoded == "@RESET":
                uart_send('@OK' + '\r\n')
                machine.soft_reset()


            elif decoded == "@scale_1_clean":
                uart_send('@OK' + '\r\n')
                hx.tare()


            elif decoded == "@scale_2_clean":
                uart_send('@OK' + '\r\n')
                hx2.tare()

            else:
                print("Invalid format:", decoded)
                uart_send('@ERROR' + '\r\n')

    except Exception as e:
        print("UART receive error:", e)
        return None

uart1.irq(trigger = UART.IRQ_RXIDLE, handler = uart_receive)

_thread.start_new_thread(uart_send, ())

def main():

    reset_done = True
    global counter

    scale_list=[]
    scale_list1=[]
    try:
        # # Initial setup
        hx.power_up()
        hx.tare()

        hx2.power_up()
        hx2.tare()
        print("Setup complete. Starting calibration...")

        # Calibrate the scale
        # scaling_factor1 = calibrate(hx)
        # scaling_factor2 = calibrate(hx2)

        scaling_factor1 = -105
        scaling_factor2 = -107.5

        if (scaling_factor1 and  scaling_factor2) is None:
            print("Calibration failed. Exiting...")
            return

        # Set the scaling factor
        hx.scale = scaling_factor1
        hx2.scale = scaling_factor2
        print("Calibration complete. Starting continuous measurement...")

        while True:
            if reset_done == True:
                hx.tare()
                hx2.tare()
                reset_done = False
            try:
                # Get weight (average of 5 readings)
                scale_list.append(int(hx.get_weight(1)))
                scale_list1.append(int(hx2.get_weight(1)))

                if len(scale_list)>2:
                    if scale_list[0] - scale_list[1] > 2000:
                        uart_send('@BOX_1 IS REMOVED' + '\r\n')
                        hx.tare()

                    scale_list.pop(0)
                print(scale_list)
                c = 0
                for i in scale_list:
                    c = c + i
                weight = int(c / len(scale_list))

                if len(scale_list1)>2:
                    if scale_list[0] - scale_list[1] > 2000:
                        uart_send('@BOX_2 IS REMOVED' + '\r\n')
                        hx2.tare()

                    scale_list1.pop(0)
                print(scale_list1)

                d = 0
                for i in scale_list1:
                    d=d+i
                weight2=int(d/len(scale_list1))

                weight_oled(weight, weight2)

                # Power cycle to avoid buffer issues
                hx.power_down()
                hx.power_up()

                hx2.power_down()
                hx2.power_up()

                message = f"@Scale_1:{weight}\r\n@Scale_2:{weight2}\r\n"

                uart_send(message)

                if Button_pin_1.value() == 0:
                    counter += 100
                    Led.value(not Led.value())
                    print(counter)

                    if counter >= 1000:
                        hx.tare()
                        counter = 0
                        Led.value(1)
                        time.sleep(2)
                        Led.value(0)
                        while Button_pin_1.value() == 0:
                            time.sleep(0.01)

                elif Button_pin_2.value() == 0:
                    counter += 100
                    Led.value(not Led.value())
                    print(counter)

                    if counter >= 1000:
                        hx2.tare()
                        counter = 0
                        Led.value(1)
                        time.sleep(2)
                        Led.value(0)
                        while Button_pin_2.value() == 0:
                            time.sleep(0.01)

                else:
                    counter = 0

                if Button_pin.value() == 0:
                    Led.value(1)
                    time.sleep(0.2)
                    Led.value(0)
                    time.sleep(0.2)
                    Led.value(1)
                    time.sleep(0.2)
                    Led.value(0)
                    time.sleep(0.2)
                    machine.soft_reset()

                time.sleep(0.1)

            except KeyboardInterrupt:
                print("Exiting...")

            except Exception as e:
                print("Error reading weight:", e)


    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print("Setup error:", e)
    finally:
        hx.power_down()
        hx2.power_down()


if __name__ == "__main__":
    main()

