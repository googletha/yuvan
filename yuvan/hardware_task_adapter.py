from yuvan.iot_device_controller import IoTDeviceController

class HardwareTaskAdapter:
    def __init__(self):
        self.iot_controller = IoTDeviceController()

    def process_hardware_command(self, command):
        # Example: "turn on the lights"
        if "turn on" in command and "lights" in command:
            return self.iot_controller.control_device("lights", "on")
        elif "turn off" in command and "lights" in command:
            return self.iot_controller.control_device("lights", "off")
        else:
            return "Unknown hardware command." 