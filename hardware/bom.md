# Hardware Bill of Materials (BOM) & Cost Estimation (P_307)

## 1. Component Procurement List

The following bill of materials covers the optional physical hardware prototype for monitoring one industrial motor drive node using the ESP32 edge microcontroller.

| S.No | Item Description | Part / Model | Quantity | Indicative Unit Price (INR) | Total Price (INR) | Common Indian Suppliers |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | **Microcontroller Board** | ESP32 DevKit V1 (30-pin, Dual Core 240MHz, WiFi + BLE) | 1 | ₹380 - ₹450 | ₹420 | Robu.in, ElectronicsComp, Amazon IN |
| 2 | **6-Axis IMU Sensor Module** | GY-521 (InvenSense MPU-6050 Accelerometer / Gyroscope) | 1 | ₹120 - ₹180 | ₹150 | Robu.in, QuartzComponents |
| 3 | **Digital Temperature Probe** | DS18B20 Waterproof Probe (1-Wire Stainless Steel Cap) | 1 | ₹140 - ₹190 | ₹160 | Robu.in, ElectronicsComp |
| 4 | **Pull-up Resistor for 1-Wire** | 4.7kΩ 1/4W Metal Film Resistor | 1 | ₹2 | ₹2 | Local Electronics Store |
| 5 | **Status & Alarm Indicators** | 5mm Diffused LEDs (Red & Green) | 2 | ₹3 | ₹6 | Local Electronics Store |
| 6 | **Current Limiting Resistors**| 220Ω 1/4W Resistors | 2 | ₹2 | ₹4 | Local Electronics Store |
| 7 | **Prototyping Breadboard** | 400-Point Solderless Breadboard | 1 | ₹80 - ₹110 | ₹95 | Robu.in, Amazon IN |
| 8 | **Jumper Wires** | Premium Dupont Jumper Wires (M-M, M-F, 20cm Pack) | 1 Pack (20 pcs) | ₹60 | ₹60 | Robu.in |
| 9 | **Power Supply / Cable** | 5V 2A USB Adapter with Micro-USB Cable | 1 | ₹150 - ₹220 | ₹180 | Local Retailer / Amazon IN |
| 10 | **Sensor Mounting Base** | Neodymium Disc Magnet (for Motor Casing Attachment) | 1 | ₹40 - ₹60 | ₹50 | QuartzComponents / Robu |
| **TOTAL** | **Estimated Prototype Bill of Materials Cost** | | | | **₹1,127** | *(Approx. ₹1,100 – ₹1,300 INR)* |

---

## 2. Pricing Assumptions and Supplier Clarifications
> [!NOTE]
> **Pricing Disclaimer:**
> - Prices listed above represent retail indicative market prices in India (INR) across hobbyist and educational robotics suppliers (e.g., Robu.in, ElectronicsComp.com, Quartz Components, Amazon India) as of standard recent academic procurement cycles.
> - Prices do not include GST (typically 18%) or courier delivery charges (typically ₹50–₹80 per order).
> - These estimates are provided as a budgeting reference for university lab projects; no commercial affiliation or vendor sponsorship is implied.

---

## 3. Industrial Production vs. Academic Prototype Comparison

| Feature | Academic Prototype (This BOM) | Industrial Certified IoT Node (e.g. SKF, Banner, IFM) |
| :--- | :--- | :--- |
| **Sensor Type** | Consumer MEMS (MPU-6050) | Industrial Piezoelectric Quartz Accelerometer |
| **Bandwidth** | 0 – 1,000 Hz | 0 – 15,000 Hz |
| **Ingress Protection** | Solderless Breadboard / 3D Printed Box | IP67 / IP68 Stainless Steel Cast Enclosure |
| **Vibration Dynamic Range** | $\pm 2g$ to $\pm 16g$ | $\pm 50g$ to $\pm 500g$ |
| **Communication** | WiFi 2.4 GHz (802.11 b/g/n) | Industrial Ethernet, RS-485 Modbus RTU, WirelessHART, LoRaWAN |
| **Cost Range** | ~₹1,150 ($14 USD) | ₹25,000 – ₹1,20,000 ($300 – $1,500 USD) |
