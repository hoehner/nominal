import pyvisa
import time

rm = pyvisa.ResourceManager()

snoo = rm.open_resource('ASRL4::INSTR')

snoo.baud_rate = 115200
snoo.data_bits = 8
snoo.parity = pyvisa.constants.Parity.none
snoo.stop_bits = pyvisa.constants.StopBits.one
snoo.timeout = 500


def snoo_query(query: str) -> str:
    snoo.write(query)
    response = snoo.read().rstrip()
    return response

def snoo_cmd(cmd: str):
    snoo.write(cmd)
    snoo.read().rstrip()

def main():
    snoo_cmd("SNOO:FAN 90")
    try:
        i = 1
        delta_deg = 10
        while True:
            id = snoo_query("*IDN?")
            ping = snoo_query("PING?")
            temp = snoo_query("SNOO:TEMP?")
            mic = snoo_query("SNOO:MIC?")
            fan = snoo_query("SNOO:FAN?")
            wiggle = snoo_query("SNOO:WIGGLE?")
            print(f'''ID: {id} | Ping: {ping} | Temp (F): {temp} | Sound (Eng): {mic} | Fan: {fan} | Wiggle: {wiggle}''')
            
            # snoo_cmd("SNOO:FAN " + str(90 + (delta_deg * i)))
            i *= -1        # invert the wiggle delta for the next iteration

            time.sleep(.1)

    except KeyboardInterrupt:
        snoo_cmd("SNOO:FAN 90")
        print("SNOO back to nominal position")

if __name__ == "__main__":
    main()