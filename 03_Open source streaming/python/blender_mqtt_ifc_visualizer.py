import bpy
import paho.mqtt.client as mqtt
import threading


# ---------------------------------------------------------------------------
# MQTT CONFIGURATION
# ---------------------------------------------------------------------------

MQTT_BROKER = "mqtt.eclipseprojects.io"
MQTT_PORT = 8883
MQTT_USE_TLS = True

# Original prototype topics.
# These must match the topics used by the Arduino publisher and by the PMV script.
MQTT_TOPIC_SENSOR = "lfontanella/research/temperature_humidity"
MQTT_TOPIC_PMV = "lfontanella/research/pmv"


# ---------------------------------------------------------------------------
# BLENDER / IFC CONFIGURATION
# ---------------------------------------------------------------------------

# IFC space objects to be colored.
# These names must match the object names in the Blender/Bonsai scene.
OBJECTS_TO_COLOR = [
    "IfcSpace/13",
    "IfcSpace/14",
    "IfcSpace/15",
    "IfcSpace/11",
    "IfcSpace/10",
    "IfcSpace/09",
    "IfcSpace/12",
]

# Text objects used to display temperature and humidity.
# These names must be adapted to the specific Blender scene.
TEXT_OBJECT_TEMPERATURE = "Text_Temp13"
TEXT_OBJECT_HUMIDITY = "Text_Hum13"


# ---------------------------------------------------------------------------
# PMV VISUALIZATION SETTINGS
# ---------------------------------------------------------------------------

MATERIAL_ALPHA = 0.4

PMV_COLORS = {
    "cold": {
        "material_name": "MaterialBlu",
        "color": (0, 0, 1, MATERIAL_ALPHA),
    },
    "cool": {
        "material_name": "MaterialAzzurro",
        "color": (0, 1, 1, MATERIAL_ALPHA),
    },
    "comfort": {
        "material_name": "MaterialVerde",
        "color": (0, 1, 0, MATERIAL_ALPHA),
    },
    "warm": {
        "material_name": "MaterialArancione",
        "color": (1, 0.5, 0, MATERIAL_ALPHA),
    },
    "hot": {
        "material_name": "MaterialRosso",
        "color": (1, 0, 0, MATERIAL_ALPHA),
    },
}


def get_pmv_category(pmv_value):
    """
    Return a PMV category according to the visualization thresholds.

    This version fixes the uncovered ranges of the original prototype,
    for example values between 2 and 3, or between -3 and -2.
    """

    if pmv_value <= -3:
        return "cold"
    elif -3 < pmv_value < -1:
        return "cool"
    elif -1 <= pmv_value <= 1:
        return "comfort"
    elif 1 < pmv_value <= 3:
        return "warm"
    else:
        return "hot"


def get_or_create_material(material_name, color):
    """
    Create or reuse a Blender material and set its diffuse color.
    """

    material = bpy.data.materials.get(material_name)

    if not material:
        material = bpy.data.materials.new(name=material_name)

    material.diffuse_color = color

    return material


def apply_material_to_spaces(material):
    """
    Apply the selected material to the configured IFC space objects.
    """

    for obj_name in OBJECTS_TO_COLOR:
        obj = bpy.data.objects.get(obj_name)

        if obj:
            obj.data.materials.clear()
            obj.data.materials.append(material)
        else:
            print(f"Warning: object not found in Blender scene: {obj_name}")


# ---------------------------------------------------------------------------
# MQTT MESSAGE CALLBACKS
# ---------------------------------------------------------------------------

def on_message_pmv(client, userdata, msg):
    """
    Callback executed when a PMV value is received.
    The PMV value is used to color the selected IFC spaces.
    """

    try:
        pmv_value = float(msg.payload.decode("utf-8").strip())

        print("PMV received:", pmv_value)

        pmv_category = get_pmv_category(pmv_value)

        material_name = PMV_COLORS[pmv_category]["material_name"]
        color = PMV_COLORS[pmv_category]["color"]

        material = get_or_create_material(material_name, color)

        apply_material_to_spaces(material)

    except Exception as e:
        print("Error while processing PMV MQTT message:", e)


def on_message_temperature_humidity(client, userdata, msg):
    """
    Callback executed when temperature and relative humidity values are received.

    Expected payload format:

    temperature
    relative_humidity
    """

    try:
        message = msg.payload.decode("utf-8").strip().split("\n")

        temperature = float(message[0])
        humidity = float(message[1])

        print("Temperature received:", temperature)
        print("Relative humidity received:", humidity)

        update_text_with_temperature(temperature)
        update_text_with_humidity(humidity)

    except Exception as e:
        print("Error while processing temperature and humidity MQTT message:", e)


# ---------------------------------------------------------------------------
# BLENDER TEXT UPDATE FUNCTIONS
# ---------------------------------------------------------------------------

def update_text_with_temperature(temperature):
    """
    Update the Blender text object used to display temperature.
    """

    text_object = bpy.data.objects.get(TEXT_OBJECT_TEMPERATURE)

    if text_object:
        text_object.data.body = "{:.2f} °C".format(temperature)
    else:
        print(f"Warning: text object not found: {TEXT_OBJECT_TEMPERATURE}")


def update_text_with_humidity(humidity):
    """
    Update the Blender text object used to display relative humidity.
    """

    text_object_humidity = bpy.data.objects.get(TEXT_OBJECT_HUMIDITY)

    if text_object_humidity:
        text_object_humidity.data.body = "{:.2f} %".format(humidity)
    else:
        print(f"Warning: text object not found: {TEXT_OBJECT_HUMIDITY}")


# ---------------------------------------------------------------------------
# MQTT THREAD
# ---------------------------------------------------------------------------

def mqtt_thread():
    """
    MQTT listener running in a separate thread.

    This follows the structure of the original prototype.
    The script subscribes to the PMV topic and to the temperature/humidity topic.
    """

    client = mqtt.Client()

    if MQTT_USE_TLS:
        client.tls_set()

    print(f"Connecting to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    client.subscribe(MQTT_TOPIC_PMV)
    client.subscribe(MQTT_TOPIC_SENSOR)

    print(f"Subscribed to topic: {MQTT_TOPIC_PMV}")
    print(f"Subscribed to topic: {MQTT_TOPIC_SENSOR}")

    client.message_callback_add(MQTT_TOPIC_PMV, on_message_pmv)
    client.message_callback_add(MQTT_TOPIC_SENSOR, on_message_temperature_humidity)

    print("Starting MQTT listening loop...")
    client.loop_forever()


# ---------------------------------------------------------------------------
# START MQTT LISTENER
# ---------------------------------------------------------------------------

mqtt_listener_thread = threading.Thread(target=mqtt_thread)
mqtt_listener_thread.start()