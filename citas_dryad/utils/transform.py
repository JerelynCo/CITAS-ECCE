import struct

## data value conversions
class DataTransformation():
	def unpack_U16(self, val):
		return float(struct.unpack("<H", val)[0])

	def decode_float32(self, val):
		return struct.unpack('f', val)[0]

	def conv_temp(self, val):
		dec_val = 0.00000003044 * pow(val, 3.0) - 0.00008038 * pow(val, 2.0) + val * 0.1149 - 30.449999999999999
		if dec_val < -10.0:
			dec_val = -10.0
		elif dec_val > 55.0:
			dec_val = 55.0
		return dec_val

	def conv_ec(self, val):
		if val > 1771:
			return 10.0
		dec_val = (val / 1771.0) * 10.0
		return dec_val

	def conv_light(self, val):
		dec_val = 16655.6019 * pow(val, -1.0606619)
		return dec_val

	def conv_moisture(self, val):
		dec_val_tmp = 11.4293 + (0.0000000010698 * pow(val, 4.0) - 0.00000152538 * pow(val, 3.0) + 0.000866976 * pow(val, 2.0) - 0.169422 * val)
		dec_val = 100.0 * (0.0000045 * pow(dec_val_tmp, 3.0) - 0.00055 * pow(dec_val_tmp, 2.0) + 0.0292 * dec_val_tmp - 0.053)
		if dec_val < 0.0:
			dec_val = 0.0
		elif dec_val > 60.0:
			dec_val = 60.0
		return dec_val


