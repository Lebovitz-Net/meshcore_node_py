from .buffer_reader import BufferReader

class CayenneLpp:
    LPP_DIGITAL_INPUT = 0
    LPP_DIGITAL_OUTPUT = 1
    LPP_ANALOG_INPUT = 2
    LPP_ANALOG_OUTPUT = 3
    LPP_GENERIC_SENSOR = 100
    LPP_LUMINOSITY = 101
    LPP_PRESENCE = 102
    LPP_TEMPERATURE = 103
    LPP_RELATIVE_HUMIDITY = 104
    LPP_ACCELEROMETER = 113
    LPP_BAROMETRIC_PRESSURE = 115
    LPP_VOLTAGE = 116
    LPP_CURRENT = 117
    LPP_FREQUENCY = 118
    LPP_PERCENTAGE = 120
    LPP_ALTITUDE = 121
    LPP_CONCENTRATION = 125
    LPP_POWER = 128
    LPP_DISTANCE = 130
    LPP_ENERGY = 131
    LPP_DIRECTION = 132
    LPP_UNIXTIME = 133
    LPP_GYROMETER = 134
    LPP_COLOUR = 135
    LPP_GPS = 136
    LPP_SWITCH = 142
    LPP_POLYLINE = 240

    @staticmethod
    def parse(data: bytes):
        buffer = BufferReader(data)
        telemetry = []

        while buffer.get_remaining_bytes_count() >= 2:
            channel = buffer.read_uint8()
            type_ = buffer.read_uint8()

            # stop parsing if channel and type are zero
            if channel == 0 and type_ == 0:
                break

            if type_ == CayenneLpp.LPP_GENERIC_SENSOR:
                value = buffer.read_uint32_be()
                telemetry.append({"channel": channel, "type": type_, "value": value})

            elif type_ == CayenneLpp.LPP_LUMINOSITY:
                lux = buffer.read_int16_be()
                telemetry.append({"channel": channel, "type": type_, "value": lux})

            elif type_ == CayenneLpp.LPP_PRESENCE:
                presence = buffer.read_uint8()
                telemetry.append({"channel": channel, "type": type_, "value": presence})

            elif type_ == CayenneLpp.LPP_TEMPERATURE:
                temperature = buffer.read_int16_be() / 10
                telemetry.append({"channel": channel, "type": type_, "value": temperature})

            elif type_ == CayenneLpp.LPP_RELATIVE_HUMIDITY:
                rh = buffer.read_uint8() / 2
                telemetry.append({"channel": channel, "type": type_, "value": rh})

            elif type_ == CayenneLpp.LPP_BAROMETRIC_PRESSURE:
                pressure = buffer.read_uint16_be() / 10
                telemetry.append({"channel": channel, "type": type_, "value": pressure})

            elif type_ == CayenneLpp.LPP_VOLTAGE:
                voltage = buffer.read_int16_be() / 100
                telemetry.append({"channel": channel, "type": type_, "value": voltage})

            elif type_ == CayenneLpp.LPP_CURRENT:
                current = buffer.read_int16_be() / 1000
                telemetry.append({"channel": channel, "type": type_, "value": current})

            elif type_ == CayenneLpp.LPP_PERCENTAGE:
                percentage = buffer.read_uint8()
                telemetry.append({"channel": channel, "type": type_, "value": percentage})

            elif type_ == CayenneLpp.LPP_CONCENTRATION:
                concentration = buffer.read_uint16_be()
                telemetry.append({"channel": channel, "type": type_, "value": concentration})

            elif type_ == CayenneLpp.LPP_POWER:
                power = buffer.read_uint16_be()
                telemetry.append({"channel": channel, "type": type_, "value": power})

            elif type_ == CayenneLpp.LPP_GPS:
                latitude = buffer.read_int24_be() / 10000
                longitude = buffer.read_int24_be() / 10000
                altitude = buffer.read_int24_be() / 100
                telemetry.append({
                    "channel": channel,
                    "type": type_,
                    "value": {
                        "latitude": latitude,
                        "longitude": longitude,
                        "altitude": altitude,
                    },
                })

            else:
                # unsupported type, stop parsing further
                return telemetry

        return telemetry
