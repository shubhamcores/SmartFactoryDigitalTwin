# Hardware Circuit Diagram & Wiring Specification (P_307)

## 1. Overview
This hardware extension provides edge telemetry acquisition using an **ESP32 DevKit V1** microcontroller connected to an **MPU-6050 6-Axis IMU** accelerometer/gyroscope module.

## 2. Pinout Interconnection Table

| Component | Pin Label | ESP32 GPIO Pin | Description |
| :--- | :--- | :--- | :--- |
| **MPU-6050** | VCC | 3V3 (or 5V if module has AMS1117 regulator) | Logic & Sensor Power Supply (3.3V recommended) |
| **MPU-6050** | GND | GND | System Common Ground |
| **MPU-6050** | SCL | GPIO 22 | I2C Serial Clock (Wire bus) |
| **MPU-6050** | SDA | GPIO 21 | I2C Serial Data (Wire bus) |
| **MPU-6050** | AD0 | GND | I2C Address select (GND = `0x68`, 3.3V = `0x69`) |
| **MPU-6050** | INT | GPIO 19 (Optional) | Data Ready Interrupt |
| **Red LED** | Anode (+) | GPIO 4 (via 220Ω resistor) | Physical Edge Over-threshold Alarm Indicator |
| **Red LED** | Cathode (-) | GND | Ground |
| **Built-in LED** | Internal | GPIO 2 | WiFi / MQTT Connectivity Blink Code |

## 3. Circuit Schematic (ASCII Diagram)

```
        +-------------------------------------------------+
        |                 ESP32 DevKit V1                 |
        |                                                 |
        |   [3V3] ----------------+                       |
        |   [GND] -------------+  |                       |
        |   [GPIO 21 (SDA)] ---|--|-------+               |
        |   [GPIO 22 (SCL)] ---|--|----+  |               |
        |   [GPIO 4] ----------|--|----|--|---+           |
        +----------------------|--|----|--|---|-----------+
                               |  |    |  |   |
                               |  |    |  |  [220 Ohm]
                               |  |    |  |   |
                               |  |    |  |  (Red LED)
                               |  |    |  |   |
                               |  +----|--|---+
                               |  |    |  |
                        +------|--|----+--|-------+
                        |     VCC GND SCL SDA     |
                        |                         |
                        |      MPU-6050 IMU       |
                        |        Module           |
                        |                         |
                        |      AD0  INT           |
                        +-------|-----------------+
                                |
                                +--- GND (Sets I2C Addr to 0x68)
```

## 4. Hardware Power Specifications
- **Operating Voltage**: 5.0V via Micro-USB (ESP32 on-board LDO generates 3.3V).
- **Peak Current (WiFi TX)**: ~240 mA (ensure USB port or external adapter provides at least 500 mA).
- **I2C Bus Pullups**: Most commercially sold breakout modules (e.g. GY-521) already integrate 4.7kΩ pull-up resistors on SDA and SCL to 3.3V. If using bare breakout chips, attach external 4.7kΩ pull-up resistors from SDA/SCL to 3.3V.
