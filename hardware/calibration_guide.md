# MPU-6050 Calibration & Vibration Signal Processing Guide 

## 1. Principles of Industrial Vibration Sensing
Industrial predictive maintenance standards (such as **ISO 10816-3**) evaluate machine vibration severity in **velocity RMS (mm/s)** over the frequency bandwidth from 10 Hz to 1,000 Hz.

MEMS accelerometers (like the MPU-6050) measure instantaneous **acceleration ($a$)** in units of $g$ ($1g \approx 9.80665\text{ m/s}^2$).

### Mathematical Conversion (Acceleration to Velocity):
For periodic sinusoidal motor vibration at rotational frequency $f$:
$$v(t) = \int a(t) \, dt$$
In the frequency domain:
$$V_{\text{peak}} = \frac{A_{\text{peak}}}{2 \pi f}$$
$$V_{\text{RMS}} = \frac{V_{\text{peak}}}{\sqrt{2}} \approx \frac{A_{\text{peak}} \times 9806.65}{2 \pi f \times 1.414}$$

For a standard 4-pole AC induction motor operating at 50 Hz line frequency ($f = 50\text{ Hz}$):
$$V_{\text{RMS}} (\text{mm/s}) \approx A_{\text{peak}} (g) \times 22.07$$

---

## 2. Zero-G Static Offset Calibration Procedure
Every silicon MEMS accelerometer possesses minor factory fabrication offsets. To nullify these offsets:

1. **Physical Setup**: Place the ESP32 and MPU-6050 sensor on a completely flat, rigid, vibration-free surface with the Z-axis pointing vertically upward.
2. **Sampling Run**: Run a 1,000-sample calibration loop:
   ```cpp
   float ax_offset = 0, ay_offset = 0, az_offset = 0;
   for (int i = 0; i < 1000; i++) {
       sensors_event_t a, g, temp;
       mpu.getEvent(&a, &g, &temp);
       ax_offset += a.acceleration.x;
       ay_offset += a.acceleration.y;
       az_offset += (a.acceleration.z - 9.80665); // Gravity compensation
       delay(2);
   }
   ax_offset /= 1000.0;
   ay_offset /= 1000.0;
   az_offset /= 1000.0;
   ```
3. Store `ax_offset`, `ay_offset`, and `az_offset` in non-volatile flash (ESP32 Preferences/EEPROM) and subtract them from all subsequent readings.

---

## 3. Digital Filtering Architecture
Factory environments are inundated with electrical high-frequency electromagnetic noise (from VFD switching and contactor arcs).

The firmware incorporates:
1. **Hardware Low-Pass Filter (DLPF)**: Configured in the MPU-6050 configuration register (`MPU6050_BAND_21_HZ`) to eliminate aliasing from frequencies above 21 Hz.
2. **Moving Average Filter**: A 15-sample sliding window averaging buffer that smooths mechanical micro-transients while preserving true mechanical imbalance or bearing distress signatures.

---

## 4. Hardware Limitations vs. Software Simulation Honesty Statement
> [!IMPORTANT]
> **Limitations of Low-Cost Consumer MEMS Sensors (MPU-6050):**
> 1. **Frequency Ceiling**: The MPU-6050 has an effective dynamic bandwidth below 1,000 Hz and a typical noise density of $400\,\mu g/\sqrt{\text{Hz}}$. Professional industrial piezoelectric accelerometers (e.g. Wilcoxon or PCB Piezotronics) operate up to 10 kHz to 20 kHz with sub-$10\,\mu g$ noise floors.
> 2. **High-Frequency Bearing Fault Detection**: Early bearing spalling (outer raceway BPFO frequencies > 2 kHz) cannot be captured accurately by the MPU-6050. It is suitable for gross unbalance, shaft misalignment, and structural looseness detection.
> 3. **Testing Transparency**: The core FactoryTwin software application includes simulated telemetry that models continuous factory dynamics. Physical hardware deployment requires mounting the MPU-6050 via stud or magnetic mount directly onto the bearing housing of an operating motor.
