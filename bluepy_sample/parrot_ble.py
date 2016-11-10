from bluepy.btle import DefaultDelegate, Peripheral, UUID
import struct
import datetime
import traceback
import numpy as np

## Constants ##
# Services
SERVICES = {
	"LIVE"			: "39e1fa0084a811e2afba0002a5d5c51b",
	"BATTERY"		: 0x180f,
	"DEVICE_INFO"		: 0x180a
}

# Sensors Characteristics (Old firmware)
SENSORS = {
	"SUNLIGHT"		: "39e1fa0184a811e2afba0002a5d5c51b",
	"SOIL_EC"		: "39e1fa0284a811e2afba0002a5d5c51b",
	"SOIL_TEMP"		: "39e1fa0384a811e2afba0002a5d5c51b",
	"AIR_TEMP"		: "39e1fa0484a811e2afba0002a5d5c51b",
	"SOIL_MOISTURE"	: "39e1fa0584a811e2afba0002a5d5c51b",
}

# Sensors Characteristics (New firmware)
CAL_SENSORS = {
	"SUNLIGHT"		: "39e1fa0184a811e2afba0002a5d5c51b",
	"SOIL_EC"		: "39e1fa0284a811e2afba0002a5d5c51b",
	"SOIL_TEMP"		: "39e1fa0384a811e2afba0002a5d5c51b",
	"AIR_TEMP"		: "39e1fa0484a811e2afba0002a5d5c51b",
	"VWC"			: "39e1fa0584a811e2afba0002a5d5c51b",
	"CAL_VWC"		: "39e1fa0984a811e2afba0002a5d5c51b",
	"CAL_AIR_TEMP"	: "39e1fa0a84a811e2afba0002a5d5c51b",
	"CAL_DLI"		: "39e1fa0b84a811e2afba0002a5d5c51b",
	"CAL_EA"		: "39e1fa0c84a811e2afba0002a5d5c51b",
	"CAL_ECB"		: "39e1fa0d84a811e2afba0002a5d5c51b",
	"CAL_EC_POROUS"	: "39e1fa0e84a811e2afba0002a5d5c51b",
}

# Control characteristics
CONTROLS = {
	"FIRMWARE_VER"		: 0x2a26,
	"LIVE_MODE_PERIOD"	: "39e1fa0684a811e2afba0002a5d5c51b",   
	"LED"				: "39e1fa0784a811e2afba0002a5d5c51b",
	"LAST_MOVE_DATE"	: "39e1fa0884a811e2afba0002a5d5c51b", 
	"BATTERY_LEVEL"		: 0x2a19
}

# Enable disable flags
ENABLE = "\x01"
DISABLE = "\x00"


## data value conversions
def unpack_U16(val):
	return float(struct.unpack("<H", val)[0])

def decode_float32(val):
	return struct.unpack('f', val)[0]

def conv_temp(val):
	dec_val = 0.00000003044 * pow(val, 3.0) - 0.00008038 * pow(val, 2.0) + val * 0.1149 - 30.449999999999999
	if dec_val < -10.0:
		dec_val = -10.0
	elif dec_val > 55.0:
		dec_val = 55.0
	return dec_val

def conv_ec(val):
	if val > 1771:
		return 10.0
	dec_val = (val / 1771.0) * 10.0
	return dec_val

def conv_light(val):
	dec_val = 16655.6019 * pow(val, -1.0606619)
	return dec_val

def conv_moisture(val):
	dec_val_tmp = 11.4293 + (0.0000000010698 * pow(val, 4.0) - 0.00000152538 * pow(val, 3.0) + 0.000866976 * pow(val, 2.0) - 0.169422 * val)
	dec_val = 100.0 * (0.0000045 * pow(dec_val_tmp, 3.0) - 0.00055 * pow(dec_val_tmp, 2.0) + 0.0292 * dec_val_tmp - 0.053)
	if dec_val < 0.0:
		dec_val = 0.0
	elif dec_val > 60.0:
		dec_val = 60.0
	return dec_val

# Parrot class	
class Parrot():	
	def __init__(self, device, name):
		self.name = name
		self.device = device
		self.n_read = 3		
		self.readings = np.array([])	

	# write to characteristic a value		
	def write(self, char, val):
		char.write(str.encode(val))

	# returns whether parrot flower is the new version or not
	def isNewFirmware(self, firmware_version):
		new_firmware_version = '1.1.0'
		ver_number = firmware_version.decode("utf-8").split("_")[1].split("-")[1]
		return ver_number == new_firmware_version

	# returns dictionary of sensor readings from parrot flower 
	def read_sensors(self, live_service, battery_service, isNewFirmware):
		timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		battery_level_ch = battery_service.getCharacteristics(UUID(CONTROLS["BATTERY_LEVEL"]))[0]
		battery_level = 0
		
		try:
			# conversion from byte to decimal
			battery_level = ord(battery_level_ch.read())
		except Exception as err:
			traceback.print_tb(err.__traceback__)

		if isNewFirmware:
			# format of reading for new version	
			reading = {"TIMESTAMP":timestamp, "SUNLIGHT":None, "SOIL_EC": None, "SOIL_TEMP": None, "AIR_TEMP": None, "VWC": None, "CAL_VWC":None, "CAL_AIR_TEMP":None, "CAL_DLI":None, "CAL_EA":None, "CAL_ECB": None, "CAL_EC_POROUS":None, "BATTERY": battery_level}
			# iterate over the calibrated sensors characteristics
			for key, val in CAL_SENSORS.items():
				char = live_service.getCharacteristics(UUID(val))[0]	
				if char.supportsRead(): 
					if key == "SUNLIGHT":
						reading[key] = conv_light(unpack_U16(char.read()))
					elif key == "SOIL_EC":
						reading[key] = conv_ec(unpack_U16(char.read()))
					elif key in ["AIR_TEMP", "SOIL_TEMP"]:
						reading[key] = conv_temp(unpack_U16(char.read()))
					elif key == "VWC":
						reading[key] = conv_moisture(unpack_U16(char.read()))
					else:
						reading[key] = decode_float32(char.read())
			
		else:	
			# format of reading for old version
			reading = {"TIMESTAMP":timestamp, "SUNLIGHT":None, "SOIL_EC":None, "AIR_TEMP": None, "SOIL_TEMP": None, "VWC": None, "BATTERY": battery_level}
			# iterate over the old characteristics
			for key, val in SENSORS.items():
				char = live_service.getCharacteristics(UUID(val))[0]	
				if char.supportsRead(): 
					if key == "SUNLIGHT":
						reading[key] = conv_light(unpack_U16(char.read()))
					elif key == "SOIL_EC":
						reading[key] = conv_ec(unpack_U16(char.read()))
					elif key in ["AIR_TEMP", "SOIL_TEMP"]:
						reading[key] = conv_temp(unpack_U16(char.read()))
					elif key == "VWC":
						reading[key] = conv_moisture(unpack_U16(char.read()))
		return reading	

	def get_readings(self):
		return self.readings	

	def start(self): 
		print("Attempting to connect to {} [{}]".format(self.name, self.device.addr))
		
		# variable to hold peripheral device
		p = None
		
		# retry connection until connected
		while p is None:
			try:
				p = Peripheral(self.device, "random")
			except Exception as err:
				print("Caught exception.. Retrying connection..")
				traceback.print_tb(err.__traceback__)

		print("Connected..")	
		
		# getting firmware version of parrotflower		
		device_info_service = p.getServiceByUUID(UUID(SERVICES["DEVICE_INFO"]))
		firmware_ver_ch = device_info_service.getCharacteristics(UUID(CONTROLS["FIRMWARE_VER"]))[0]
		
		# getting live services and controlling led and live measure period
		live_service = p.getServiceByUUID(UUID(SERVICES["LIVE"]))  
		led_control_ch = live_service.getCharacteristics(UUID(CONTROLS["LED"]))[0]
		live_measure_ch = live_service.getCharacteristics(UUID(CONTROLS["LIVE_MODE_PERIOD"]))[0]
	
		# turning on live measure period, 1s
		self.write(live_measure_ch, ENABLE)
		
		# getting pf battery service
		battery_service = p.getServiceByUUID(UUID(SERVICES["BATTERY"]))
		
		print("Starting sensor readings...")	
		# turning on led indicator
		self.write(led_control_ch, ENABLE)
		
		
		while self.n_read != 0:
			self.readings = np.append(self.readings, self.read_sensors(live_service, battery_service, self.isNewFirmware(firmware_ver_ch.read())))
			self.n_read -= 1
	
		# turning off led indicator
		self.write(led_control_ch, DISABLE)

		# disconnecting peripheral
		p.disconnect()
