---
name: laplace-signals-systems
description: Bilateral and unilateral Laplace transform pairs, Region of Convergence (ROC) rules, Initial/Final Value Theorem pole conditions, and transfer function stability.
workflow: calculation
triggers:
  - laplace
  - laplace transform
  - roc
  - region of convergence
  - transfer function
  - initial value theorem
  - final value theorem
  - poles and zeros
  - bibo stability
  - s-domain
---

# Laplace Transforms, S-Domain Impedance & System Stability

## 1. Transform Definitions & Region of Convergence (ROC)
- **Unilateral Laplace Transform**:
  $$F(s) = \mathcal{L}\{f(t)\} = \int_{0^-}^{\infty} f(t) e^{-st} \, dt, \quad s = \sigma + j\omega$$
- **ROC Properties**:
  - The ROC in the complex s-plane consists of vertical strips parallel to the $j\omega$ axis.
  - The ROC contains **no poles**.
  - **Causal Signals**: The ROC is a right-half plane $\text{Re}(s) > \sigma_{max}$, bounded by the rightmost pole.
  - **Anti-Causal Signals**: The ROC is a left-half plane $\text{Re}(s) < \sigma_{min}$, bounded by the leftmost pole.
  - **BIBO Stability Criterion**: An LTI continuous-time system is Bounded-Input Bounded-Output (BIBO) stable if and only if the ROC of its transfer function $H(s)$ includes the imaginary axis ($j\omega$ axis, $\sigma = 0$). For causal systems, this requires all poles to lie strictly in the open left-half s-plane ($\text{Re}(p_k) < 0$).

## 2. Fundamental Laplace Transform Pairs
- Unit Impulse: $\mathcal{L}\{\delta(t)\} = 1$, all $s$.
- Unit Step: $\mathcal{L}\{u(t)\} = \frac{1}{s}$, $\text{Re}(s) > 0$.
- Power / Ramp: $\mathcal{L}\{t^n u(t)\} = \frac{n!}{s^{n+1}}$, $\text{Re}(s) > 0$.
- Exponential Decay: $\mathcal{L}\{e^{-at} u(t)\} = \frac{1}{s + a}$, $\text{Re}(s) > -a$.
- Damped Sine: $\mathcal{L}\{e^{-at} \sin(\omega_0 t) u(t)\} = \frac{\omega_0}{(s+a)^2 + \omega_0^2}$, $\text{Re}(s) > -a$.
- Damped Cosine: $\mathcal{L}\{e^{-at} \cos(\omega_0 t) u(t)\} = \frac{s + a}{(s+a)^2 + \omega_0^2}$, $\text{Re}(s) > -a$.

## 3. Boundary Value Theorems
- **Initial Value Theorem (IVT)**:
  $$\lim_{t \to 0^+} f(t) = \lim_{s \to \infty} s F(s)$$
  Applies to strictly proper or proper rational functions without impulse at $t=0$.
- **Final Value Theorem (FVT)**:
  $$\lim_{t \to \infty} f(t) = \lim_{s \to 0} s F(s)$$
  **Mandatory Pole Condition**: The FVT is valid **if and only if** all poles of $s F(s)$ lie strictly in the open left-half s-plane ($\text{Re}(s) < 0$).
  *Caution*: If $F(s)$ has poles on the imaginary axis (e.g. sinusoidal oscillator $F(s) = \frac{\omega}{s^2 + \omega^2}$), the time-domain signal oscillates indefinitely; applying FVT blindly yields $0$, which is physically false!

## 4. Passive Component S-Domain Equivalents
- **Resistor**: $Z_R(s) = R$, $V(s) = R I(s)$
- **Inductor**: $Z_L(s) = sL$; with initial current $i_L(0^-)$, represented by series impedance $sL$ with series voltage source $+L i_L(0^-)$ (or parallel current source $\frac{i_L(0^-)}{s}$).
- **Capacitor**: $Z_C(s) = \frac{1}{sC}$; with initial voltage $v_C(0^-)$, represented by series impedance $\frac{1}{sC}$ with series voltage source $\frac{v_C(0^-)}{s}$.
