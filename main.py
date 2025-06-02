from machine import Pin, UART
import machine
import time

# Pin(0, Pin.IN, Pin.PULL_UP)  # SDA
# Pin(1, Pin.IN, Pin.PULL_UP)  # SCL
uart1 = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
from ssd1306 import  oled, weight_oled

oled()

# Define GPIO pins
DT_PIN = 4  # Data pin (DOUT)
DT_PIN_2 = 8  # Data pin (DOUT)

SCK_PIN = 5  # Clock pin (PD_SCK)
SCK_PIN_2 = 9  # Clock pin (PD_SCK)

Button_pin = 29

# Initialize pins
dt = Pin(DT_PIN, Pin.IN)
sck = Pin(SCK_PIN, Pin.OUT)

dt_2 = Pin(DT_PIN_2, Pin.IN)
sck_2 = Pin(SCK_PIN_2, Pin.OUT)

Button_pin = Pin(Button_pin, Pin.IN)

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

# def uart_send(scale_1, scale_2):
#     try:
#         scale1 = b'Scale_1' + scale_1.to_bytes(2, 'big')
#         scale2 = b'Scale_2' + scale_2.to_bytes(2, 'big')
#         uart1.write(scale1 + scale2)
#         print("Sent:", scale1, scale2)
#         time.sleep_ms(1)
#
#     except Exception as e:
#         print("UART send error:", e)

# def uart_receive():
#     try:
#         # Read 18 bytes
#         data = uart1.read(18)
#
#         if data is None or len(data) < 18:
#             print("Incomplete data received:", data)
#             return None, None
#
#         if data.startswith(b'Scale_1') and b'Scale_2' in data:
#             scale1_bytes = data[7:9]
#             scale2_bytes = data[16:18]
#
#             scale_1 = int.from_bytes(scale1_bytes, 'big')
#             scale_2 = int.from_bytes(scale2_bytes, 'big')
#
#             print("Received scales:", scale_1, scale_2)
#             return scale_1, scale_2
#         else:
#             print("Invalid data format:", data)
#             return None, None
#
#     except Exception as e:
#         print("UART receive error:", e)
#         return None, None

def uart_send(scale_1, scale_2):
    try:
        # Convert to string with labels, separated by comma, ending with newline
        message = f"Scale_1:{scale_1}\r\n,Scale_2:{scale_2}\r\n"

        # Encode string to bytes for UART transmission
        uart1.write(message.encode('utf-8'))

        print("Sent string:", message.strip())
        time.sleep_ms(1)

    except Exception as e:
        print("UART send error:", e)


def uart_receive():
    try:
        # Read until newline (or fixed size if needed)
        data = uart1.readline()

        if data:
            decoded = data.decode('utf-8').strip()
            print("Received string:", decoded)

            # Split and parse values
            parts = decoded.split(',')
            scale_1 = int(parts[0].split(':')[1])
            scale_2 = int(parts[1].split(':')[1])

            return scale_1, scale_2
        else:
            print("No data received.")
            return None, None

    except Exception as e:
        print("UART receive error:", e)
        return None, None



def main():
    # Initialize HX711
    hx = HX711(dt, sck, gain=64)

    hx2 = HX711(dt_2, sck_2, gain=64)

    reset_done = True
    scale_list=[]
    scale_list1=[]
    try:
        # # Initial setup
        hx.power_up()
        hx.tare()
        print('Highaaaaaaaaaaaaa')

        hx2.power_up()
        hx2.tare()
        print("Setup complete. Starting calibration...")

        # Calibrate the scale
        # scaling_factor1 = calibrate(hx)
        # scaling_factor2 = calibrate(hx2)

        scaling_factor1 = 105
        scaling_factor2 = -107.5

        if (scaling_factor1 and  scaling_factor2) is None:
            print("Calibration failed. Exiting...")
            return

        # Set the scaling factor
        hx.scale = scaling_factor1
        hx2.scale = scaling_factor2
        print("Calibration complete. Starting continuous measurement...")
        # reset_done = True
        # oled() #ssD1306
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
                    scale_list.pop(0)
                print(scale_list)
                c = 0
                for i in scale_list:
                    c = c + i
                weight = int(c / len(scale_list))

                if len(scale_list1)>2:
                    scale_list1.pop(0)
                print(scale_list1)

                d = 0
                for i in scale_list1:
                    d=d+i
                weight2=int(d/len(scale_list1))
                # weight2 = int(hx2.get_weight(5))

                # Print weight
                print("Weight: {:.2f} grams".format(weight))
                print("Weight_2: {:.2f} grams".format(weight2))

                weight_oled(weight, weight2)

                # Power cycle to avoid buffer issues
                hx.power_down()
                hx.power_up()

                hx2.power_down()
                hx2.power_up()
                uart_send(weight, weight2)
                # uart_receive()
                print('Button_pin', Button_pin.value())
                if Button_pin.value() == 0:
                    machine.soft_reset()


            except KeyboardInterrupt:
                print("Exiting...")
                break
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

