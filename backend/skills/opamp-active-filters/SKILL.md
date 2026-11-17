---
name: opamp-active-filters
description: Sallen-Key and active LPF/HPF/BPF cutoff equations, quality factor Q, gain-bandwidth product (GBW) limits, and slew-rate distortion checks.
workflow: circuit_analysis
triggers:
  - opamp
  - op-amp
  - active filter
  - sallen-key
  - low-pass filter
  - high-pass filter
  - band-pass filter
  - cutoff frequency
  - quality factor
  - gbw
  - slew rate
---

# Active Op-Amp Filters: Sallen-Key Topologies & Real-World Limits

## 1. First-Order Active Filters
- **Inverting Active Low-Pass Filter (LPF)**:
  $$H(s) = -\frac{R_f}{R_{in}} \cdot \frac{1}{1 + s R_f C_f}$$
  - DC Gain: $A_{v0} = -\frac{R_f}{R_{in}}$
  - $-3\text{ dB}$ Cutoff Frequency: $f_c = \frac{1}{2\pi R_f C_f}$
- **Non-Inverting Active Low-Pass Filter**:
  $$H(s) = \left(1 + \frac{R_2}{R_1}\right) \cdot \frac{1}{1 + s R C}$$
  - Cutoff Frequency: $f_c = \frac{1}{2\pi R C}$

## 2. Second-Order Sallen-Key Filter Topology
General 2nd-order transfer function form:
$$H(s) = \frac{K \cdot \omega_0^2}{s^2 + \frac{\omega_0}{Q} s + \omega_0^2}$$
Where $K$ is the passband gain, $\omega_0$ is the undamped natural angular frequency, and $Q$ is the quality factor.

- **Low-Pass Sallen-Key Component Equations**:
  $$\omega_0 = \frac{1}{\sqrt{R_1 R_2 C_1 C_2}}, \quad f_0 = \frac{1}{2\pi \sqrt{R_1 R_2 C_1 C_2}}$$
  $$Q = \frac{\sqrt{R_1 R_2 C_1 C_2}}{C_2(R_1 + R_2) + R_1 C_1(1 - K)}$$
- **Equal-Component Design ($R_1 = R_2 = R$, $C_1 = C_2 = C$)**:
  - Cutoff frequency: $f_c = \frac{1}{2\pi R C}$
  - Non-inverting gain: $K = 1 + \frac{R_b}{R_a}$
  - Quality factor: $Q = \frac{1}{3 - K}$
  - **Butterworth Maximally Flat Filter ($Q = \frac{1}{\sqrt{2}} \approx 0.707$)**:
    $$3 - K = \sqrt{2} \implies K = 3 - \sqrt{2} \approx 1.586 \implies \frac{R_b}{R_a} = 0.586$$
  - **Stability Boundary**:
    If $K \ge 3$, then $3 - K \le 0 \implies Q \to \infty$ or negative damping, causing spontaneous sustained oscillations.

## 3. Real Op-Amp Imperfection & Distortion Constraints
- **Gain-Bandwidth Product (GBW / Unity Gain Frequency $f_T$)**:
  - Real operational amplifiers exhibit open-loop pole rolloff.
  - Required condition to avoid passband frequency peeling and excess phase lag:
    $$f_T \ge 100 \cdot Q \cdot f_c \quad \text{or at minimum} \quad f_T \ge 10 \cdot K \cdot f_c$$
  - Example: For an active filter with $f_c = 100\text{ kHz}$ and $K = 2$, choose an op-amp with $f_T \ge 2\text{ MHz}$ (e.g. TL072 with $3\text{ MHz}$, not LM741 with $1\text{ MHz}$).
- **Slew-Rate (SR) Distortion & Full-Power Bandwidth**:
  - The maximum rate of output voltage change is constrained by the internal compensation capacitor charging current:
    $$SR = \left.\frac{dv_{out}}{dt}\right|_{max}$$
  - Full-Power Bandwidth for sinusoidal output with peak voltage $V_p$:
    $$f_{max} = \frac{SR}{2\pi V_p}$$
  - Distortion Criterion: If the signal frequency $f > f_{max}$, the output wave slew-limits, visibly degenerating from a sine into a triangle wave.
