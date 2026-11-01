# Stage 7: Bill of Materials & Cost Analysis (P_307)
## Optional Industrial IoT Edge Sensing Node
**Currency**: Indian Rupee (INR - ₹)  
**Target Hardware**: ESP32 DevKit V1 Edge Node with MPU-6050 Accelerometer / Gyroscope

---

## 1. Prototype Component Procurement Breakdown

The following BOM outlines the components necessary to construct one physical vibration and temperature monitoring node for industrial rotating equipment:

| Item No. | Component Name | Technical Specification | Qty | Indicative Unit Price (INR) | Total Cost (INR) | Recommended Suppliers (India) |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **1** | **ESP32 Wi-Fi + BLE Microcontroller** | DevKit V1 30-Pin, Dual-Core Xtensa LX6 @ 240MHz, 520KB SRAM | 1 | ₹420 | ₹420 | Robu.in, ElectronicsComp |
| **2** | **6-Axis MEMS IMU Module** | GY-521 (InvenSense MPU-6050, $I^2C$ Bus, $\pm 2g$ to $\pm 16g$) | 1 | ₹150 | ₹150 | Robu.in, QuartzComponents |
| **3** | **Digital Temperature Sensor** | DS18B20 1-Wire Stainless Steel Waterproof Probe | 1 | ₹160 | ₹160 | Robu.in, ElectronicsComp |
| **4** | **1-Wire Bus Pullup Resistor** | 4.7kΩ 0.25W Metal Film Resistor | 1 | ₹2 | ₹2 | Local Electronics Retailer |
| **5** | **Edge Indicator LEDs** | 5mm High-Efficiency LEDs (1x Red Alarm, 1x Green Status) | 2 | ₹3 | ₹6 | Local Electronics Retailer |
| **6** | **Current Limiting Resistors** | 220Ω 0.25W Resistors | 2 | ₹2 | ₹4 | Local Electronics Retailer |
| **7** | **Prototyping Breadboard** | 400-Tie Points Solderless Breadboard with Power Rails | 1 | ₹95 | ₹95 | Robu.in, Amazon India |
| **8** | **Interconnect Wiring** | 20cm Dupont Jumper Wires (Male-to-Male & Male-to-Female) | 1 Pack | ₹60 | ₹60 | Robu.in |
| **9** | **Regulated Power Adapter** | 5V 2A USB Power Supply with Micro-USB Data Cable | 1 | ₹180 | ₹180 | Local Electronics Retailer |
| **10** | **Magnetic Machine Mount** | Neodymium Disc Magnet (N35 grade, for motor casing attachment) | 1 | ₹50 | ₹50 | QuartzComponents |
| **TOTAL** | **Estimated Hardware Edge Node Cost** | | | | **₹1,127** | *(Approx. ₹1,100 – ₹1,300 INR)* |

---

## 2. Pricing Assumptions and Supplier Analysis
1. **Source of Quotations**: The prices indicated above are compiled from prevailing retail catalog listings on prominent Indian maker platforms including **Robu.in (Macfos Ltd.)**, **ElectronicsComp.com**, **QuartzComponents.com**, and **Amazon India**.
2. **Exclusions**: Quoted amounts represent basic component costs and exclude Indian Goods & Services Tax (GST, typically 18%) and standard domestic shipping costs (typically ₹50–₹75 per consignment).
3. **Price Stability**: Component prices may fluctuate slightly based on silicon market availability and import duty variations.
4. **Volume Scaling**: For deployment across 4 machines simultaneously (a full 4-node factory cell), bulk purchasing reduces the unit microcontroller cost to ~₹360/board, bringing the aggregate 4-node deployment to ~₹3,900 INR.

---

## 3. Academic Prototype vs. Industrial Production Discrepancy
> [!IMPORTANT]
> **Engineering Honesty & Real-World Validation Notice:**
> - The consumer MPU-6050 breakout module used in academic lab prototyping costs ~₹150, which provides an accessible introduction to digital signal processing and I2C communication.
> - In real-world heavy industrial production (chemical refineries, power generation plants, automotive body shops), certified vibration sensors (e.g., IFM efector, Wilcoxon, SKF QuickCollect) cost between **₹25,000 to ₹1,25,000 INR per sensor**. These industrial sensors feature hermetically sealed 316L stainless steel enclosures, IP68/IP69K ratings, ATEX intrinsic safety certifications for explosive atmospheres, and piezoelectric quartz crystals calibrated up to 15 kHz.
> - The FactoryTwin application is designed so that whether telemetry originates from low-cost academic MEMS, simulated industrial digital twins, or high-end industrial Modbus/MQTT gateways, the downstream analytics, Isolation Forest scoring, and SCADA visualization remain completely uniform.
