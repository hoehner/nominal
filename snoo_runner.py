import connect_python
import pyvisa
import time

NOISE_WARN_THRESHOLD = 300
NOISE_CRIT_THRESHOLD = 650
TEMP_THRESHOLD = 76
LOOP_HZ = 10.0  # run the loop at ~10 Hz
period = 1.0 / LOOP_HZ

rm = pyvisa.ResourceManager()

snoo = rm.open_resource("ASRL4::INSTR")
logger = connect_python.get_logger(__name__)


snoo.baud_rate = 115200
snoo.data_bits = 8
snoo.parity = pyvisa.constants.Parity.none
snoo.stop_bits = pyvisa.constants.StopBits.one
snoo.timeout = 500
snoo.read_termination = '\n'
snoo.write_termination = '\n'


def snoo_read(query: str) -> str:
    response = snoo.query(query).rstrip()
    return response


def snoo_cmd(cmd: str):
    snoo.query(cmd)


@connect_python.main
def main(client: connect_python.Client):
    client.clear_stream("cn_bed_temp")
    snoo_cmd("SNOO:WIGGLE OFF")
    try:
        while True:
            start = time.time()
            t = time.time()
            id = snoo_read("*IDN?")
            ping = snoo_read("PING?")
            bed_temp = snoo_read("SNOO:TEMP?")
            mic = snoo_read("SNOO:MIC?")
            fan = snoo_read("SNOO:FAN?")
            wiggle = snoo_read("SNOO:WIGGLE?")
            # snoo_cmd("SNOO:WIGGLE HIGH")
            logger.info(
                f"""ID: {id} | Ping: {ping} | Temp (F): {bed_temp} | Sound (Eng): {mic} | Fan: {fan} | Wiggle: {wiggle}"""
            )

            # stream bed temp
            client.stream("cn_bed_temp", start, float(bed_temp))

            # stream bed noise
            client.stream("cn_bed_noise", start, float(mic))

            # stream fan feedback
            if fan == "ON":
                fan_fb = 1
            else:
                fan_fb = 0
            client.set_value("cn_fan_fb", fan_fb)

            client.set_value("cn_wiggle_fb", wiggle)

            if client.get_value("auto_mode"):
                if float(bed_temp) > TEMP_THRESHOLD:
                    snoo_cmd("SNOO:FAN ON")
                else:
                    snoo_cmd("SNOO:FAN OFF")

                if float(mic) > NOISE_WARN_THRESHOLD:
                    if float(mic) > NOISE_CRIT_THRESHOLD:
                        snoo_cmd("SNOO:WIGGLE HIGH")
                    else:
                        snoo_cmd("SNOO:WIGGLE MED")
                else:
                    snoo_cmd("SNOO:WIGGLE OFF")

            else:
                if client.get_value("fan_state"):
                    snoo_cmd("SNOO:FAN ON")
                else:
                    snoo_cmd("SNOO:FAN OFF")
                snoo_cmd("SNOO:WIGGLE " + (client.get_value("wiggle_speed")))

            elapsed = time.time() - start
            time.sleep(max(0.0, period - elapsed))

    except Exception as e:
        print(e)
        snoo_cmd("SNOO:WIGGLE OFF")
        snoo_cmd("SNOO:FAN OFF")
        print("SNOO back to nominal position")


if __name__ == "__main__":
    main()
