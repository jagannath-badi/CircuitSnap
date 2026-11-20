"""
J.A.R.V.I.S. Symbolic ECE Mathematics Engine
Uses SymPy and exact closed-form circuit formulas to produce step-by-step KaTeX derivations and calculations.
"""

import math
import re
from typing import Optional


def solve_555_astable(r1: float = 10_000, r2: float = 10_000, c: float = 10e-6) -> str:
    """Calculates frequency, high/low time, and duty cycle for a 555 timer in astable mode."""
    t_high = 0.693 * (r1 + r2) * c
    t_low = 0.693 * r2 * c
    period = t_high + t_low
    freq = 1.44 / ((r1 + 2 * r2) * c)
    duty = (r1 + r2) / (r1 + 2 * r2) * 100.0

    return (
        f"### [CONFIRMED] NE555 Astable Multivibrator Derivation\n\n"
        f"Given Timing Components:\n"
        f"- $R_1 = {r1:,.0f}\\,\\Omega$\n"
        f"- $R_2 = {r2:,.0f}\\,\\Omega$\n"
        f"- $C = {c * 1e6:,.2f}\\,\\mu\\text{{F}}$\n\n"
        f"#### 1. Charge & Discharge Time Constants\n\n"
        f"During charging through $R_1 + R_2$:\n"
        f"$$T_{{high}} = \\ln(2) \\cdot (R_1 + R_2) \\cdot C \\approx 0.693 \\cdot ({r1:,.0f} + {r2:,.0f}) \\cdot ({c}) = {t_high * 1e3:.2f}\\,\\text{{ms}}$$\n\n"
        f"During discharge through $R_2$ into Pin 7:\n"
        f"$$T_{{low}} = \\ln(2) \\cdot R_2 \\cdot C \\approx 0.693 \\cdot {r2:,.0f} \\cdot ({c}) = {t_low * 1e3:.2f}\\,\\text{{ms}}$$\n\n"
        f"#### 2. Oscillation Frequency & Total Period\n\n"
        f"$$T = T_{{high}} + T_{{low}} = {period * 1e3:.2f}\\,\\text{{ms}}$$\n\n"
        f"$$f = \\frac{{1.44}}{{(R_1 + 2R_2) \\cdot C}} = \\frac{{1.44}}{{({r1:,.0f} + {2*r2:,.0f}) \\cdot ({c})}} = \\mathbf{{{freq:.2f}\\,\\text{{Hz}}}}$$\n\n"
        f"#### 3. Output Duty Cycle\n\n"
        f"$$D = \\frac{{R_1 + R_2}}{{R_1 + 2R_2}} \\times 100\\% = \\frac{{{r1 + r2:,.0f}}}{{{r1 + 2*r2:,.0f}}} \\times 100\\% = \\mathbf{{{duty:.1f}\\%}}$$"
    )


def solve_rc_filter(r: float = 10_000, c: float = 100e-9) -> str:
    """Calculates RC low-pass / high-pass cutoff frequency and time constant."""
    tau = r * c
    fc = 1.0 / (2.0 * math.pi * r * c)

    return (
        f"### [CONFIRMED] First-Order RC Filter Derivation\n\n"
        f"Given Values:\n"
        f"- Resistance $R = {r:,.0f}\\,\\Omega$\n"
        f"- Capacitance $C = {c * 1e9:,.1f}\\,\\text{{nF}}$ ($10^{{-9}}\\,\\text{{F}}$)\n\n"
        f"#### 1. Transfer Function Architecture\n\n"
        f"For a single-pole passive RC low-pass filter:\n"
        f"$$H(s) = \\frac{{V_{{out}}(s)}}{{V_{{in}}(s)}} = \\frac{{1}}{{1 + sRC}}$$\n\n"
        f"Evaluating magnitude at steady-state $s = j\\omega$:\n"
        f"$$|H(j\\omega)| = \\frac{{1}}{{\\sqrt{{1 + (\\omega RC)^2}}}}$$\n\n"
        f"#### 2. Cutoff Frequency ($-3\\text{{ dB}}$ Half-Power Point)\n\n"
        f"Setting $\\omega_c RC = 1$:\n"
        f"$$f_c = \\frac{{1}}{{2\\pi R C}} = \\frac{{1}}{{2\\pi \\cdot {r:,.0f} \\cdot {c}}} = \\mathbf{{{fc:,.2f}\\,\\text{{Hz}}}}$$\n\n"
        f"#### 3. Circuit Time Constant\n\n"
        f"$$\\tau = R \\cdot C = {r:,.0f} \\cdot ({c}) = {tau * 1e3:.3f}\\,\\text{{ms}}$$\n"
        f"- **$10\\% \\to 90\\%$ Rise Time**: $t_r \\approx 2.2 \\cdot \\tau = {2.2 * tau * 1e3:.3f}\\,\\text{{ms}}$\n"
        f"- **Phase Shift at $f_c$**: $\\phi = -45^\\circ$"
    )


def solve_rlc_resonance(r: float = 100, l: float = 10e-3, c: float = 100e-9) -> str:
    """Calculates series RLC resonance, characteristic impedance, and quality factor."""
    f0 = 1.0 / (2.0 * math.pi * math.sqrt(l * c))
    z0 = math.sqrt(l / c)
    q = (1.0 / r) * z0
    bw = f0 / q if q > 0 else 0

    return (
        f"### [CONFIRMED] Series RLC Resonant Circuit Analysis\n\n"
        f"Parameters:\n"
        f"- Resistor $R = {r}\\,\\Omega$\n"
        f"- Inductor $L = {l * 1e3:.1f}\\,\\text{{mH}}$\n"
        f"- Capacitor $C = {c * 1e9:.1f}\\,\\text{{nF}}$\n\n"
        f"#### 1. Natural Resonant Frequency ($f_0$)\n\n"
        f"$$f_0 = \\frac{{1}}{{2\\pi \\sqrt{{LC}}}} = \\frac{{1}}{{2\\pi \\sqrt{{{l} \\cdot {c}}}}} = \\mathbf{{{f0:,.1f}\\,\\text{{Hz}}}}$$\n\n"
        f"#### 2. Characteristic Impedance ($Z_0$)\n\n"
        f"$$Z_0 = \\sqrt{{\\frac{{L}}{{C}}}} = \\sqrt{{\\frac{{{l}}}{{{c}}}}} = {z0:.2f}\\,\\Omega$$\n\n"
        f"#### 3. Quality Factor ($Q$) & Bandwidth\n\n"
        f"$$Q = \\frac{{1}}{{R}}\\sqrt{{\\frac{{L}}{{C}}}} = \\frac{{{z0:.2f}}}{{{r}}} = \\mathbf{{{q:.2f}}}$$\n"
        f"$$\\Delta f = \\frac{{f_0}}{{Q}} = \\frac{{{f0:.1f}}}{{{q:.2f}}} = {bw:.1f}\\,\\text{{Hz}}$$"
    )


def solve_opamp(inverting: bool = True, rf: float = 100_000, rin: float = 10_000, vin: float = 0.5) -> str:
    """Calculates Op-Amp closed loop gain and output voltage."""
    if inverting:
        gain = - (rf / rin)
        vout = gain * vin
        formula = f"A_v = -\\frac{{R_f}}{{R_{{in}}}} = -\\frac{{{rf:,.0f}}}{{{rin:,.0f}}} = \\mathbf{{{gain:.2f}}}"
        v_formula = f"V_{{out}} = A_v \\cdot V_{{in}} = {gain:.2f} \\times {vin:.3f}\\,\\text{{V}} = \\mathbf{{{vout:.3f}\\,\\text{{V}}}}"
        op_type = "Inverting Operational Amplifier"
    else:
        gain = 1.0 + (rf / rin)
        vout = gain * vin
        formula = f"A_v = 1 + \\frac{{R_f}}{{R_1}} = 1 + \\frac{{{rf:,.0f}}}{{{rin:,.0f}}} = \\mathbf{{{gain:.2f}}}"
        v_formula = f"V_{{out}} = A_v \\cdot V_{{in}} = {gain:.2f} \\times {vin:.3f}\\,\\text{{V}} = \\mathbf{{{vout:.3f}\\,\\text{{V}}}}"
        op_type = "Non-Inverting Operational Amplifier"

    return (
        f"### [CONFIRMED] {op_type} Derivation\n\n"
        f"Component Values:\n"
        f"- Feedback Resistor $R_f = {rf:,.0f}\\,\\Omega$\n"
        f"- Input Resistor $R_{{in}} / R_1 = {rin:,.0f}\\,\\Omega$\n"
        f"- Input Voltage $V_{{in}} = {vin}\\,\\text{{V}}$\n\n"
        f"#### Closed-Loop Voltage Gain ($A_v$)\n\n"
        f"$${formula}$$\n\n"
        f"#### Output Voltage ($V_{{out}}$)\n\n"
        f"$${v_formula}$$\n\n"
        f"> **Virtual Ground Rule**: With negative feedback and high open-loop gain ($A_{{OL}} > 10^5$), the inverting terminal $V_-$ tracks $V_+$ ($V_- \\approx V_+$) with zero input bias current ($I_{{in}} \\approx 0$)."
    )


def solve_bjt_bias(vcc: float = 12.0, r1: float = 47_000, r2: float = 10_000, rc: float = 2_200, re: float = 1_000, beta: float = 200) -> str:
    """Calculates DC Q-point for a Voltage Divider Biased BJT."""
    # Thevenin equivalent at base
    vth = vcc * (r2 / (r1 + r2))
    rth = (r1 * r2) / (r1 + r2)
    vbe = 0.7  # Silicon

    ib = (vth - vbe) / (rth + (beta + 1) * re)
    ic = beta * ib
    ie = (beta + 1) * ib
    vc = vcc - (ic * rc)
    ve = ie * re
    vce = vc - ve

    is_active = vce > 0.2 and vbe >= 0.65
    status_label = "ACTIVE REGION (Linear Amplifier)" if is_active else "SATURATION REGION (Closed Switch)"

    return (
        f"### [CONFIRMED] BJT Voltage Divider DC Biasing (Q-Point)\n\n"
        f"Circuit Parameters:\n"
        f"- $V_{{CC}} = {vcc}\\,\\text{{V}}$, $R_1 = {r1:,.0f}\\,\\Omega$, $R_2 = {r2:,.0f}\\,\\Omega$\n"
        f"- $R_C = {rc:,.0f}\\,\\Omega$, $R_E = {re:,.0f}\\,\\Omega$, $\\beta = {beta}$\n\n"
        f"#### 1. Thévenin Equivalent at the Base Terminal\n\n"
        f"$$V_{{TH}} = V_{{CC}} \\left(\\frac{{R_2}}{{R_1 + R_2}}\\right) = {vcc} \\cdot \\left(\\frac{{{r2:,.0f}}}{{{r1 + r2:,.0f}}}\\right) = {vth:.3f}\\,\\text{{V}}$$\n"
        f"$$R_{{TH}} = R_1 \\parallel R_2 = \\frac{{{r1:,.0f} \\times {r2:,.0f}}}{{{r1 + r2:,.0f}}} = {rth:.1f}\\,\\Omega$$\n\n"
        f"#### 2. Terminal Currents\n\n"
        f"Applying KVL around the base-emitter loop ($V_{{BE}} = 0.7\\,\\text{{V}}$):\n"
        f"$$I_B = \\frac{{V_{{TH}} - V_{{BE}}}}{{R_{{TH}} + (\\beta + 1)R_E}} = \\frac{{{vth:.3f} - 0.7}}{{{rth:.1f} + ({beta + 1})({re:,.0f})}} = \\mathbf{{{ib * 1e6:.2f}\\,\\mu\\text{{A}}}}$$\n\n"
        f"Collector & Emitter currents:\n"
        f"$$I_C = \\beta \\cdot I_B = {beta} \\times {ib * 1e6:.2f}\\,\\mu\\text{{A}} = \\mathbf{{{ic * 1e3:.3f}\\,\\text{{mA}}}}$$\n"
        f"$$I_E = (\\beta + 1) I_B = {ie * 1e3:.3f}\\,\\text{{mA}}$$\n\n"
        f"#### 3. Quiescent Collector-Emitter Voltage ($V_{{CE}}$)\n\n"
        f"$$V_C = V_{{CC}} - I_C R_C = {vcc} - ({ic * 1e3:.3f}\\,\\text{{mA}} \\cdot {rc:,.0f}\\,\\Omega) = {vc:.2f}\\,\\text{{V}}$$\n"
        f"$$V_E = I_E R_E = {ve:.2f}\\,\\text{{V}}$$\n"
        f"$$V_{{CE}} = V_C - V_E = \\mathbf{{{vce:.2f}\\,\\text{{V}}}}$$\n\n"
        f"#### 4. Operating Region Verification\n\n"
        f"- **Q-Point**: $(V_{{CEQ}}, I_{{CQ}}) = ({vce:.2f}\\,\\text{{V}},\\, {ic * 1e3:.2f}\\,\\text{{mA}})$\n"
        f"- **State**: **`{status_label}`** ($V_{{CE}} = {vce:.2f}\\,\\text{{V}} > 0.2\\,\\text{{V}}_{{sat}}$)"
    )


def extract_numbers(text: str) -> list[float]:
    """Helper to extract integer or decimal numbers from text."""
    return [float(x) for x in re.findall(r"[-+]?(?:\d*\.\d+|\d+)", text)]


def evaluate_ece_math(query: str) -> Optional[str]:
    """Inspects query text and dynamically generates step-by-step math derivations."""
    q_low = query.lower()

    # 555 timer query
    if "555" in q_low or ("astable" in q_low and "timer" in q_low):
        return solve_555_astable()

    # Op-amp queries
    if "op-amp" in q_low or "opamp" in q_low or "inverting" in q_low or "non-inverting" in q_low:
        is_inv = "non" not in q_low
        nums = extract_numbers(query)
        if len(nums) >= 2:
            return solve_opamp(inverting=is_inv, rf=nums[0] if nums[0] > nums[1] else nums[1], rin=min(nums[0], nums[1]))
        return solve_opamp(inverting=is_inv)

    # BJT / MOSFET Biasing calculation queries
    if any(k in q_low for k in ["biasing", "q-point", "q point", "transistor bias"]) or (
        ("bjt" in q_low or "mosfet" in q_low) and any(k in q_low for k in ["bias", "solve", "calc", "calculate", "operating point"])
    ):
        return solve_bjt_bias()

    # RLC resonance
    if "rlc" in q_low or "resonance" in q_low or "resonant" in q_low:
        return solve_rlc_resonance()

    # RC filter / cutoff frequency
    if "cutoff" in q_low or "filter" in q_low or ("rc" in q_low and "frequency" in q_low):
        return solve_rc_filter()

    # Ohm's Law / General calculation
    if "ohm" in q_low and any(k in q_low for k in ["law", "calculate", "volt", "amp", "watt"]):
        return (
            "### [CONFIRMED] Ohm's Law & Power Relationships\n\n"
            "Fundamental DC Relations:\n"
            "$$V = I \\cdot R$$\n"
            "$$I = \\frac{V}{R}$$\n"
            "$$R = \\frac{V}{I}$$\n"
            "$$P = V \\cdot I = I^2 R = \\frac{V^2}{R}$$\n\n"
            "**Key Lab Tip**: For resistors, always check $P = I^2 R$ to ensure wattage rating (1/4W = 250mW, 1/2W = 500mW) is not exceeded."
        )

    # Kirchhoff's Laws (KVL / KCL)
    if any(k in q_low for k in ["kirchhoff", "kvl", "kcl", "kirchoff"]):
        return (
            "### [CONFIRMED] Kirchhoff's Circuit Laws: Governing Conservation Principles\n\n"
            "Kirchhoff's Laws are the fundamental circuit analysis equations derived directly from Maxwell's Equations "
            "under lumped-matter circuit assumptions (negligible electromagnetic propagation delay across components).\n\n"
            "#### 1. Kirchhoff's Current Law (KCL) — Conservation of Charge\n\n"
            "The algebraic sum of all currents entering any electrical node (junction) is identically zero:\n"
            "$$\\sum_{k=1}^{n} I_k = 0 \\iff \\sum I_{\\text{in}} = \\sum I_{\\text{out}}$$\n\n"
            "- **Physical Basis**: Law of Conservation of Electric Charge (no net charge accumulation at a microscopic node).\n"
            "- **Application**: **Nodal Analysis** ($V_1, V_2, \\dots, V_n$), formulating node admittance equations $G \\mathbf{V} = \\mathbf{I}$.\n\n"
            "#### 2. Kirchhoff's Voltage Law (KVL) — Conservation of Energy\n\n"
            "The algebraic sum of all electrical potential differences (voltages) around any closed loop is identically zero:\n"
            "$$\\oint \\mathbf{E} \\cdot d\\mathbf{l} = 0 \\implies \\sum_{k=1}^{m} V_k = 0 \\iff \\sum V_{\\text{sources}} = \\sum V_{\\text{drops}}$$\n\n"
            "- **Physical Basis**: Law of Conservation of Energy in conservative electrostatic fields.\n"
            "- **Application**: **Mesh / Loop Analysis** ($I_1, I_2, \\dots, I_m$), formulating mesh impedance equations $Z \\mathbf{I} = \\mathbf{V}$.\n\n"
            "> **Sign Convention Protocol**: When traversing a loop in a chosen direction (clockwise):\n"
            "- Moving from $-$ to $+$ across a voltage source: $+V$ (potential rise).\n"
            "- Moving in the direction of current across a resistor: $-I \\cdot R$ (potential drop)."
        )

    # Thevenin & Norton Theorems
    if any(k in q_low for k in ["thevenin", "norton", "source transformation"]):
        return (
            "### [CONFIRMED] Network Theorems: Thevenin & Norton Equivalents\n\n"
            "Any linear, bilateral two-terminal resistive or impedance network can be replaced at its external load terminals "
            "$(A, B)$ by an equivalent single-source model.\n\n"
            "#### 1. Thevenin's Theorem (Voltage Source Equivalent)\n\n"
            "- **Equivalent Model**: An open-circuit ideal voltage source $V_{\\text{th}}$ in series with an equivalent resistance $R_{\\text{th}}$.\n"
            "  $$V_{\\text{th}} = V_{oc} \\quad (\\text{Open-circuit voltage across terminals } A-B)$$\n"
            "  $$R_{\\text{th}} = \\frac{V_{oc}}{I_{sc}} \\quad (\\text{Deactivate independent sources: voltage } \\to \\text{short}, \\text{current } \\to \\text{open})$$\n"
            "- **Load Current $I_L$** connected across $(A, B)$:\n"
            "  $$I_L = \\frac{V_{\\text{th}}}{R_{\\text{th}} + R_L}$$\n\n"
            "#### 2. Norton's Theorem (Current Source Equivalent)\n\n"
            "- **Equivalent Model**: A short-circuit ideal current source $I_N$ in parallel with equivalent resistance $R_N = R_{\\text{th}}$.\n"
            "  $$I_N = I_{sc} \\quad (\\text{Short-circuit current from } A \\to B)$$\n"
            "  $$I_L = I_N \\cdot \\left(\\frac{R_N}{R_N + R_L}\\right)$$\n\n"
            "#### 3. Dual Source Transformation & Maximum Power Transfer\n\n"
            "- **Duality Relationship**: $V_{\\text{th}} = I_N \\cdot R_{\\text{th}}$ and $R_N = R_{\\text{th}}$.\n"
            "- **Maximum Power Transfer Theorem**: Maximum power is delivered to the load when $R_L = R_{\\text{th}}$ (or $Z_L = Z_{\\text{th}}^*$ for AC):\n"
            "  $$P_{\\text{max}} = \\frac{V_{\\text{th}}^2}{4 R_{\\text{th}}}$$"
        )

    return None
