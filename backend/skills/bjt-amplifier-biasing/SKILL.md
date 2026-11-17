---
name: bjt-amplifier-biasing
description: DC Q-point analysis, emitter stabilization, load-line bounds, and small-signal hybrid-pi gain/impedance rules.
workflow: circuit_analysis
triggers:
  - bjt
  - transistor
  - q-point
  - operating point
  - emitter bias
  - voltage divider bias
  - load line
  - hybrid-pi
  - transconductance
  - common-emitter
---

# BJT Amplifier Biasing & Small-Signal Hybrid-Pi Analysis

## 1. DC Biasing & Q-Point Analysis
For a four-resistor voltage divider bias network ($R_1, R_2, R_C, R_E$):
- **Thévenin Equivalent Base Circuit**:
  $$V_{TH} = V_{CC} \cdot \frac{R_2}{R_1 + R_2}$$
  $$R_{TH} = R_1 \parallel R_2 = \frac{R_1 R_2}{R_1 + R_2}$$
- **Base-Emitter Loop KVL**:
  $$V_{TH} - I_B R_{TH} - V_{BE} - I_E R_E = 0$$
- **Collector Current $I_C$**:
  Since $I_E = (\beta + 1) I_B$ and $I_C \approx I_E$:
  $$I_{CQ} = \frac{V_{TH} - V_{BE}}{R_E + \frac{R_{TH}}{\beta + 1}}$$
  Where $V_{BE} \approx 0.7\text{ V}$ for silicon npn transistors at room temperature ($25^\circ\text{C}$).
- **Beta-Independence Criterion**:
  Design $R_E \ge 10 \cdot \frac{R_{TH}}{\beta + 1}$ or $R_2 \le 0.1 \cdot \beta R_E$ to stabilize the Q-point against thermal beta drift.
- **Collector-Emitter Voltage $V_{CEQ}$**:
  $$V_{CEQ} = V_{CC} - I_{CQ}(R_C + R_E)$$

## 2. Load-Line Bounds & Operating Limits
- **DC Load Line**:
  - Cutoff coordinate ($I_C = 0$): $V_{CE(cutoff)} = V_{CC}$
  - Saturation coordinate ($V_{CE} = 0$): $I_{C(sat)} = \frac{V_{CC}}{R_C + R_E}$
  - Active Region Condition: $V_{CE(sat)} \approx 0.2\text{ V} \le V_{CEQ} \le V_{CC}$
- **AC Load Line**:
  - Dynamic AC collector load: $r_L = R_C \parallel R_L$
  - If emitter resistor is unbypassed: $r_e' = R_E$; if fully bypassed by $C_E$: $r_e' = 0$.
  - AC load line slope: $m_{AC} = -\frac{1}{r_L + r_e'}$

## 3. Small-Signal Hybrid-$\pi$ Model
- **Thermal Voltage**: $V_T = \frac{kT}{q} \approx 25.86\text{ mV} \approx 26\text{ mV}$ at $300\text{ K}$.
- **Transconductance $g_m$**:
  $$g_m = \frac{I_{CQ}}{V_T} \approx \frac{I_{CQ}}{26\text{ mV}}$$
- **Base-Emitter Dynamic Resistance $r_\pi$**:
  $$r_\pi = \frac{\beta}{g_m} = \frac{\beta V_T}{I_{CQ}}$$
- **Early Output Resistance $r_o$**:
  $$r_o = \frac{V_A + V_{CEQ}}{I_{CQ}} \approx \frac{V_A}{I_{CQ}}$$
  Where $V_A$ is the Early voltage (typically $50\text{ V} - 150\text{ V}$).
- **Voltage Gain $A_v$ (Common-Emitter with Bypassed Emitter)**:
  $$A_v = -g_m \cdot (R_C \parallel R_L \parallel r_o) \approx -g_m \cdot (R_C \parallel R_L)$$
- **Input and Output Impedances**:
  $$Z_{in} = R_1 \parallel R_2 \parallel r_\pi$$
  $$Z_{out} = R_C \parallel r_o \approx R_C$$
