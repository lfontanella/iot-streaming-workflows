"""
hbim_conservation_threshold_alerts_template.py

Sanitized template derived from the original research prototype.

Purpose:
- Receive environmental data through MQTT.
- Compare received values with conservation-oriented thresholds.
- Update colors and text labels in a Blender/Bonsai HBIM scene.
- Show popup alerts when thresholds are exceeded.
- Record threshold exceedances in a local CSV log.

Research context:
This script documents a heritage-oriented HBIM workflow developed to support facility management and preventive conservation through threshold-based alerts.

Security and privacy note:
- The real HBIM/IFC model is not included in the public repository.
- Real monitoring data are not included.
- Real alert logs are not included.
- Real MQTT credentials or private broker configurations must not be committed.
- Object names, thresholds and topic names must be adapted locally.

Author: Luca Fontanella
"""

import bpy
import paho.mqtt.client as mqtt
import threading
import csv
from datetime import datetime
from pathlib import Path
import ssl


# ---------------------------------------------------------------------------
# LOCAL PATHS
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
WORKFLOW_DIR = SCRIPT_DIR.parent

# Local CSV log folder.
# CSV files generated during real tests must not be committed if they contain sensitive monitoring or case-study information.
LOG_DIR = WORKFLOW_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

ALERT_LOG_FILE = LOG_DIR / "threshold_alerts_log.csv"


# ---------------------------------------------------------------------------
# MQTT CONFIGURATION
# ---------------------------------------------------------------------------

# Demonstration broker.
# For real monitoring scenarios, use a private and properly secured broker.
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 8883
MQTT_USE_TLS = True

# This follows the logic of the original prototype, but topic names should be replaced locally according to the actual monitoring setup.
#
# Each topic can be associated with:
# - a monitored parameter;
# - a list of target objects in the Blender/Bonsai scene.
#
# The object names below are examples and must be adapted to the local HBIM model.
MQTT_TOPICS = {
    "gallerie/demo/room_temperature": {
        "parameter": "temperature",
        "targets": ["IfcSpace/01", "IfcSpace/02", "IfcSpace/03", "IfcSpace/04"],
    },
    "gallerie/demo/canvas_left_temperature": {
        "parameter": "temperature",
        "targets": ["Artwork_Canvas_Left_01", "Artwork_Canvas_Left_02", "Artwork_Canvas_Left_03"],
    },
    "gallerie/demo/canvas_right_temperature": {
        "parameter": "temperature",
        "targets": ["Artwork_Canvas_Right_01", "Artwork_Canvas_Right_02", "Artwork_Canvas_Right_03"],
    },
    "gallerie/demo/marble_sculptures_temperature": {
        "parameter": "temperature",
        "targets": ["Artwork_Marble_01", "Artwork_Marble_02", "Artwork_Marble_03"],
    },
}


# ---------------------------------------------------------------------------
# THRESHOLD CONFIGURATION
# ---------------------------------------------------------------------------

# Default threshold used when no material-specific threshold is defined.
# These values are illustrative placeholders and must be validated by qualified  conservation experts before any operational use.
DEFAULT_TEMPERATURE_THRESHOLD = 24.0

# Material-specific example thresholds.
# Replace these values locally with validated conservation thresholds.
MATERIAL_THRESHOLDS = {
    "generic_space": {
        "temperature_max": 24.0,
        "label": "Room temperature alert",
    },
    "canvas": {
        "temperature_max": 24.0,
        "label": "Canvas / painting temperature alert",
    },
    "marble": {
        "temperature_max": 26.0,
        "label": "Marble sculpture temperature alert",
    },
}

# Associate Blender/Bonsai objects with material categories.
# These are placeholder object names. They must be adapted to the local HBIM scene.
OBJECT_MATERIAL_CATEGORY = {
    "IfcSpace/01": "generic_space",
    "IfcSpace/02": "generic_space",
    "IfcSpace/03": "generic_space",
    "IfcSpace/04": "generic_space",

    "Artwork_Canvas_Left_01": "canvas",
    "Artwork_Canvas_Left_02": "canvas",
    "Artwork_Canvas_Left_03": "canvas",
    "Artwork_Canvas_Right_01": "canvas",
    "Artwork_Canvas_Right_02": "canvas",
    "Artwork_Canvas_Right_03": "canvas",

    "Artwork_Marble_01": "marble",
    "Artwork_Marble_02": "marble",
    "Artwork_Marble_03": "marble",
}

# Optional text labels in the Blender/Bonsai scene.
# These are placeholder names and must be adapted locally.
TEXT_MAPPING = {
    "IfcSpace/01": "Text_T01",
    "IfcSpace/02": "Text_T02",
    "IfcSpace/03": "Text_T03",
    "IfcSpace/04": "Text_T04",
}


# ---------------------------------------------------------------------------
# VISUALIZATION CONFIGURATION
# ---------------------------------------------------------------------------

MATERIAL_ALPHA = 0.5

MATERIAL_COLORS = {
    "MaterialCold": (0.0, 0.0, 1.0, MATERIAL_ALPHA),
    "MaterialOk": (0.0, 1.0, 0.0, MATERIAL_ALPHA),
    "MaterialWarning": (1.0, 0.5, 0.0, MATERIAL_ALPHA),
    "MaterialAlert": (1.0, 0.0, 0.0, MATERIAL_ALPHA),
}


# ---------------------------------------------------------------------------
# GLOBAL POPUP QUEUE
# ---------------------------------------------------------------------------

# MQTT callbacks run in a separate thread. The popup is triggered through a Blender timer to avoid directly invoking UI operators from the MQTT thread.
pending_popup_messages = []


# ---------------------------------------------------------------------------
# CSV LOG
# ---------------------------------------------------------------------------

def log_alert_to_csv(target_object, measured_value, parameter, threshold, alert_type):
    """
    Write an alert event to a local CSV file.

    The generated CSV file is a local output and must not be committed if it
    contains sensitive data.
    """

    file_exists = ALERT_LOG_FILE.exists()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(ALERT_LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "target_object",
                "parameter",
                "measured_value",
                "threshold",
                "alert_type",
            ])

        writer.writerow([
            now,
            target_object,
            parameter,
            f"{measured_value:.2f}",
            f"{threshold:.2f}",
            alert_type,
        ])


# ---------------------------------------------------------------------------
# MATERIALS AND COLORS
# ---------------------------------------------------------------------------

def get_material_name_from_temperature(temperature, threshold):
    """
    Return the material name according to the measured temperature and threshold.
    """

    if temperature > threshold:
        return "MaterialAlert"

    if temperature > threshold - 1.0:
        return "MaterialWarning"

    if temperature < 19.5:
        return "MaterialCold"

    return "MaterialOk"


def get_or_create_material(material_name):
    """
    Create or reuse a Blender material.
    """

    material = bpy.data.materials.get(material_name)

    if not material:
        material = bpy.data.materials.new(name=material_name)

    material.diffuse_color = MATERIAL_COLORS[material_name]

    return material


def apply_material_to_object(object_name, material_name):
    """
    Apply a material to a Blender/Bonsai object.
    """

    obj = bpy.data.objects.get(object_name)

    if not obj:
        print(f"Warning: object not found in Blender scene: {object_name}")
        return

    if not hasattr(obj.data, "materials"):
        print(f"Warning: object has no material slots: {object_name}")
        return

    material = get_or_create_material(material_name)

    obj.data.materials.clear()
    obj.data.materials.append(material)


def update_text_with_temperature(temperature, text_object_name):
    """
    Update a Blender text object with the measured temperature.
    """

    text_obj = bpy.data.objects.get(text_object_name)

    if text_obj and text_obj.type == "FONT":
        text_obj.data.body = f"{temperature:.2f} °C"
    elif text_obj:
        print(f"Warning: object is not a text object: {text_object_name}")
    else:
        print(f"Warning: text object not found: {text_object_name}")


# ---------------------------------------------------------------------------
# THRESHOLD LOGIC
# ---------------------------------------------------------------------------

def get_threshold_for_object(object_name, parameter):
    """
    Return the threshold associated with the object and monitored parameter.
    """

    material_category = OBJECT_MATERIAL_CATEGORY.get(object_name, "generic_space")
    threshold_config = MATERIAL_THRESHOLDS.get(
        material_category,
        MATERIAL_THRESHOLDS["generic_space"],
    )

    if parameter == "temperature":
        return threshold_config.get(
            "temperature_max",
            DEFAULT_TEMPERATURE_THRESHOLD,
        )

    return DEFAULT_TEMPERATURE_THRESHOLD


def get_alert_label_for_object(object_name):
    """
    Return the alert label associated with the object material category.
    """

    material_category = OBJECT_MATERIAL_CATEGORY.get(object_name, "generic_space")
    threshold_config = MATERIAL_THRESHOLDS.get(
        material_category,
        MATERIAL_THRESHOLDS["generic_space"],
    )

    return threshold_config.get("label", "Environmental threshold alert")


def process_temperature_for_targets(temperature, targets):
    """
    Update target objects and collect alert messages when thresholds are exceeded.
    """

    alert_messages = []

    for target_object in targets:
        threshold = get_threshold_for_object(target_object, "temperature")
        material_name = get_material_name_from_temperature(temperature, threshold)

        apply_material_to_object(target_object, material_name)

        if target_object in TEXT_MAPPING:
            update_text_with_temperature(temperature, TEXT_MAPPING[target_object])

        if temperature > threshold:
            alert_label = get_alert_label_for_object(target_object)

            log_alert_to_csv(
                target_object=target_object,
                measured_value=temperature,
                parameter="temperature",
                threshold=threshold,
                alert_type=alert_label,
            )

            alert_messages.append(
                f"{target_object}: {temperature:.2f} °C > {threshold:.2f} °C"
            )

    return alert_messages


# ---------------------------------------------------------------------------
# UI PANEL
# ---------------------------------------------------------------------------

class OBJECT_PT_conservation_alert_panel(bpy.types.Panel):
    bl_label = "Conservation Alerts"
    bl_idname = "OBJECT_PT_conservation_alert_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sensor"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        if scene.conservation_alert_active:
            layout.label(text=scene.conservation_alert_message, icon="ERROR")
        else:
            layout.label(text="No active alerts", icon="CHECKMARK")


# ---------------------------------------------------------------------------
# POPUP OPERATOR
# ---------------------------------------------------------------------------

class WM_OT_conservation_popup(bpy.types.Operator):
    bl_idname = "wm.conservation_popup"
    bl_label = "Conservation Alert"

    message: bpy.props.StringProperty()

    def draw(self, context):
        layout = self.layout

        for line in self.message.split("\n"):
            layout.label(text=line)

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=420)


# ---------------------------------------------------------------------------
# TIMER FUNCTIONS
# ---------------------------------------------------------------------------

def check_popup_timer():
    """
    Trigger pending popups from Blender's main thread.
    """

    if pending_popup_messages:
        message = pending_popup_messages.pop(0)
        bpy.ops.wm.conservation_popup("INVOKE_DEFAULT", message=message)

    return 0.5


def update_scene_alert_state(alert_messages):
    """
    Update the Blender side panel state.
    """

    scene = bpy.context.scene

    if alert_messages:
        scene.conservation_alert_active = True
        scene.conservation_alert_message = "ALERT: threshold exceeded"

        popup_message = "High environmental value:\n" + "\n".join(alert_messages)
        pending_popup_messages.append(popup_message)

    else:
        scene.conservation_alert_active = False
        scene.conservation_alert_message = ""


# ---------------------------------------------------------------------------
# MQTT CALLBACK
# ---------------------------------------------------------------------------

def on_message_environmental_value(client, userdata, msg):
    """
    MQTT callback.

    Expected payload:
    - a single numerical value representing temperature in °C.

    Example:
    27.40
    """

    try:
        payload = msg.payload.decode("utf-8").strip()
        temperature = float(payload)

        print(f"[MQTT] Received temperature: {temperature:.2f} °C")
        print(f"[MQTT] Topic: {msg.topic}")

        topic_config = MQTT_TOPICS.get(msg.topic)

        if not topic_config:
            print(f"Warning: topic not configured: {msg.topic}")
            return

        parameter = topic_config.get("parameter", "temperature")
        targets = topic_config.get("targets", [])

        if parameter != "temperature":
            print(f"Warning: unsupported parameter in this template: {parameter}")
            return

        alert_messages = process_temperature_for_targets(
            temperature=temperature,
            targets=targets,
        )

        # Update UI from Blender main thread.
        bpy.app.timers.register(
            lambda: _timer_update_alert_state(alert_messages),
            first_interval=0.1,
        )

    except Exception as error:
        print(f"Error in MQTT callback: {error}")


def _timer_update_alert_state(alert_messages):
    """
    Wrapper used to update the Blender UI from a timer.
    """

    update_scene_alert_state(alert_messages)
    return None


# ---------------------------------------------------------------------------
# MQTT THREAD
# ---------------------------------------------------------------------------

def mqtt_thread():
    """
    Start MQTT listener.

    This template follows the original research prototype structure, with an
    MQTT client running in a background thread.
    """

    client = mqtt.Client()

    if MQTT_USE_TLS:
        # Demonstration configuration.
        # For operational use, configure certificate verification properly.
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.tls_insecure_set(True)

    print(f"Connecting to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    for topic in MQTT_TOPICS.keys():
        client.subscribe(topic)
        client.message_callback_add(topic, on_message_environmental_value)
        print(f"Subscribed to topic: {topic}")

    print("MQTT listener started.")
    client.loop_forever()


# ---------------------------------------------------------------------------
# REGISTRATION
# ---------------------------------------------------------------------------

def ensure_scene_properties():
    """
    Create custom scene properties used by the UI panel.
    """

    bpy.types.Scene.conservation_alert_active = bpy.props.BoolProperty(
        name="Conservation Alert Active",
        default=False,
    )

    bpy.types.Scene.conservation_alert_message = bpy.props.StringProperty(
        name="Conservation Alert Message",
        default="",
    )


def register():
    """
    Register Blender classes, timers and MQTT thread.
    """

    ensure_scene_properties()

    bpy.utils.register_class(OBJECT_PT_conservation_alert_panel)
    bpy.utils.register_class(WM_OT_conservation_popup)

    bpy.app.timers.register(check_popup_timer)

    threading.Thread(
        target=mqtt_thread,
        daemon=True,
    ).start()


def unregister():
    """
    Unregister Blender classes.
    """

    bpy.utils.unregister_class(OBJECT_PT_conservation_alert_panel)
    bpy.utils.unregister_class(WM_OT_conservation_popup)


# Execute registration when the script is run inside Blender.
register()