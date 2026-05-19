import math
import paho.mqtt.client as mqtt


# ---------------------------------------------------------------------------
# MQTT CONFIGURATION
# ---------------------------------------------------------------------------

MQTT_BROKER = "mqtt.eclipseprojects.io"
MQTT_PORT = 1883

MQTT_TOPIC_SENSOR = "lfontanella/research/temperature_humidity"
MQTT_TOPIC_PMV = "lfontanella/research/pmv"


# ---------------------------------------------------------------------------
# PMV CONFIGURATION
# ---------------------------------------------------------------------------

AIR_VELOCITY = 0.1          # m/s
METABOLIC_RATE = 1.2       # met
CLOTHING_INSULATION = 0.5  # clo


# ---------------------------------------------------------------------------
# PMV CALCULATION
# ---------------------------------------------------------------------------

def calculate_pmv(ta, tr, v, rh, met, clo):
    """
    Calculate the Predicted Mean Vote (PMV).

    Parameters:
    ta  = air temperature [°C]
    tr  = mean radiant temperature [°C]
    v   = air velocity [m/s]
    rh  = relative humidity [%]
    met = metabolic rate [met]
    clo = clothing insulation [clo]
    """

    pa = rh * 10 * math.exp(16.6536 - 4030.183 / (ta + 235)) / 1000
    icl = 0.155 * clo
    m = met * 58.15
    w = 0
    mw = m - w

    if icl <= 0.078:
        fcl = 1 + 1.29 * icl
    else:
        fcl = 1.05 + 0.645 * icl

    hcf = 12.1 * math.sqrt(v)
    tcl = ta + (35.5 - ta) / (3.5 * (6.45 * icl + 0.1))

    for _ in range(100):
        tcl_old = tcl
        hc = max(2.38 * abs(tcl_old - ta) ** 0.25, hcf)

        tcl = (
            35.7
            - 0.028 * mw
            - icl
            * (
                3.96 * 10 ** -8 * fcl
                * ((tcl_old + 273.15) ** 4 - (tr + 273.15) ** 4)
                + fcl * hc * (tcl_old - ta)
            )
        ) / (1 + 0.155 * fcl * icl * hc)

        if abs(tcl - tcl_old) < 0.1:
            break

    pmv = (0.303 * math.exp(-0.036 * m) + 0.028) * (
        mw
        - 3.05 * 10 ** -3 * (5733 - 6.99 * mw - pa)
        - 0.42 * (mw - 58.15)
        - 1.7 * 10 ** -5 * m * (5867 - pa)
        - 0.0014 * m * (34 - ta)
        - 3.96 * 10 ** -8 * fcl * ((tcl + 273.15) ** 4 - (tr + 273.15) ** 4)
        - fcl * hc * (tcl - ta)
    )

    return pmv


# ---------------------------------------------------------------------------
# MQTT CALLBACK
# ---------------------------------------------------------------------------

def on_message(client, userdata, msg):
    """
    Callback executed when a message is received from the MQTT broker.

    Expected payload format:

    temperature
    relative_humidity

    Example:

    20.8
    52.0
    """

    try:
        message = msg.payload.decode("utf-8").strip()
        print(f"Message received on topic '{msg.topic}':")
        print(message)

        data = message.split("\n")

        ta = float(data[0])  # Air temperature [°C]
        rh = float(data[1])  # Relative humidity [%]

        # Prototype assumptions
        tr = ta
        v = AIR_VELOCITY
        met = METABOLIC_RATE
        clo = CLOTHING_INSULATION

        pmv = calculate_pmv(ta, tr, v, rh, met, clo)

        print(f"Temperature: {ta:.2f} °C")
        print(f"Relative humidity: {rh:.2f} %")
        print(f"PMV: {pmv:.2f}")

        client.publish(MQTT_TOPIC_PMV, f"{pmv:.2f}")
        print(f"PMV published on topic '{MQTT_TOPIC_PMV}'")

    except ValueError:
        print("Error: unable to convert received data to numeric values.")

    except IndexError:
        print("Error: invalid message format. Expected temperature and humidity on two lines.")

    except Exception as e:
        print(f"Error while processing MQTT message: {e}")


# ---------------------------------------------------------------------------
# MQTT CLIENT SETUP
# ---------------------------------------------------------------------------

client = mqtt.Client()
client.on_message = on_message

print(f"Connecting to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
client.connect(MQTT_BROKER, MQTT_PORT, 60)

print(f"Subscribing to topic: {MQTT_TOPIC_SENSOR}")
client.subscribe(MQTT_TOPIC_SENSOR)

print("Waiting for MQTT messages...")
client.loop_forever()