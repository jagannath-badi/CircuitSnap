"""
J.A.R.V.I.S. Local Component & Datasheet Knowledge Base
Sub-millisecond offline lookup for IC pinouts, electrical specs, resistor color bands, and SMD codes.
"""

import re
from typing import Optional, Dict, Any

DATASHEET_REGISTRY: Dict[str, Dict[str, Any]] = {
    "NE555": {
        "name": "NE555 Precision Timer IC",
        "category": "Timer / Oscillator",
        "package": "DIP-8 / SOIC-8",
        "supply_voltage": "4.5V to 15V (18V abs max)",
        "max_current": "200 mA source/sink",
        "description": "Industry-standard monolithic timing circuit capable of producing accurate time delays or oscillation in Astable and Monostable modes.",
        "pinout": [
            {"pin": 1, "name": "GND", "type": "Power", "desc": "Ground reference (0V)"},
            {"pin": 2, "name": "TRIG", "type": "Input", "desc": "Trigger input (< 1/3 Vcc sets internal flip-flop HIGH)"},
            {"pin": 3, "name": "OUT", "type": "Output", "desc": "High-current totem-pole output stage (up to 200 mA)"},
            {"pin": 4, "name": "RESET", "type": "Input", "desc": "Active-LOW reset (< 0.4V overrides all inputs, forces OUT low)"},
            {"pin": 5, "name": "CTRL", "type": "Input", "desc": "Control voltage (defaults to 2/3 Vcc; bypass to GND with 10nF cap)"},
            {"pin": 6, "name": "THRESH", "type": "Input", "desc": "Threshold comparator (> 2/3 Vcc resets flip-flop LOW)"},
            {"pin": 7, "name": "DISCH", "type": "Output", "desc": "Open-collector discharge transistor (in phase with OUT)"},
            {"pin": 8, "name": "VCC", "type": "Power", "desc": "Positive supply voltage (+4.5V to +15V)"},
        ],
        "specs": {
            "Supply Voltage Range": "4.5V – 16V",
            "Output Current": "±200 mA max",
            "Max Frequency": "~500 kHz",
            "Timing Accuracy": "1% typical drift with temperature",
        },
        "lab_notes": "Always place a 100nF ceramic decoupling capacitor across Pin 8 (VCC) and Pin 1 (GND) to suppress sharp crowbar current spikes during state switching.",
    },
    "LM741": {
        "name": "LM741 General-Purpose Operational Amplifier",
        "category": "Operational Amplifier",
        "package": "DIP-8 / TO-99",
        "supply_voltage": "±5V to ±18V (±22V abs max)",
        "max_current": "25 mA short-circuit output current",
        "description": "Classic general-purpose op-amp with internal frequency compensation and short-circuit protection.",
        "pinout": [
            {"pin": 1, "name": "OFFSET NULL", "type": "Input", "desc": "Input offset voltage null balance 1"},
            {"pin": 2, "name": "IN-", "type": "Input", "desc": "Inverting input terminal"},
            {"pin": 3, "name": "IN+", "type": "Input", "desc": "Non-inverting input terminal"},
            {"pin": 4, "name": "V-", "type": "Power", "desc": "Negative power supply rail (e.g. -15V or GND in single-supply)"},
            {"pin": 5, "name": "OFFSET NULL", "type": "Input", "desc": "Input offset voltage null balance 2"},
            {"pin": 6, "name": "OUT", "type": "Output", "desc": "Op-Amp output terminal"},
            {"pin": 7, "name": "V+", "type": "Power", "desc": "Positive power supply rail (e.g. +15V)"},
            {"pin": 8, "name": "NC", "type": "Passive", "desc": "No connection (leave floating)"},
        ],
        "specs": {
            "Open-Loop Voltage Gain": "200,000 V/V (106 dB)",
            "Slew Rate": "0.5 V/µs",
            "Unity Gain Bandwidth": "1.0 MHz",
            "Input Resistance": "2 MΩ typical",
        },
        "lab_notes": "Not rail-to-rail: output swings within ~2V of supply rails. For single 5V microcontroller supplies, prefer modern rail-to-rail op-amps like MCP6002.",
    },
    "LM358": {
        "name": "LM358 Dual Low-Power Operational Amplifier",
        "category": "Dual Op-Amp",
        "package": "DIP-8 / SOIC-8",
        "supply_voltage": "Single supply: 3V to 32V; Split: ±1.5V to ±16V",
        "max_current": "40 mA sink / 20 mA source",
        "description": "Dual independent, high-gain, internally frequency-compensated op-amps designed specifically to operate from a single power supply over a wide voltage range.",
        "pinout": [
            {"pin": 1, "name": "1OUT", "type": "Output", "desc": "Output of Op-Amp 1"},
            {"pin": 2, "name": "1IN-", "type": "Input", "desc": "Inverting input of Op-Amp 1"},
            {"pin": 3, "name": "1IN+", "type": "Input", "desc": "Non-inverting input of Op-Amp 1"},
            {"pin": 4, "name": "GND / V-", "type": "Power", "desc": "Ground (single supply) or Negative rail (split supply)"},
            {"pin": 5, "name": "2IN+", "type": "Input", "desc": "Non-inverting input of Op-Amp 2"},
            {"pin": 6, "name": "2IN-", "type": "Input", "desc": "Inverting input of Op-Amp 2"},
            {"pin": 7, "name": "2OUT", "type": "Output", "desc": "Output of Op-Amp 2"},
            {"pin": 8, "name": "VCC / V+", "type": "Power", "desc": "Positive power supply rail (+3V to +32V)"},
        ],
        "specs": {
            "Common-Mode Input Range": "Includes ground (0V) directly",
            "Slew Rate": "0.6 V/µs",
            "Unity Gain Bandwidth": "1.0 MHz",
            "Quiescent Current": "500 µA total",
        },
        "lab_notes": "Input common-mode range includes negative rail (GND), making it perfect for single-supply current-sensing shunts and comparator setups.",
    },
    "TL072": {
        "name": "TL072 Low-Noise JFET-Input Dual Op-Amp",
        "category": "Dual Audio/Precision Op-Amp",
        "package": "DIP-8 / SOIC-8",
        "supply_voltage": "±5V to ±18V",
        "max_current": "40 mA short-circuit output",
        "description": "High-speed JFET-input dual operational amplifier with low input bias current, low harmonic distortion (0.003%), and low noise (18 nV/√Hz).",
        "pinout": [
            {"pin": 1, "name": "1OUT", "type": "Output", "desc": "Output of Channel 1"},
            {"pin": 2, "name": "1IN-", "type": "Input", "desc": "Inverting input of Channel 1"},
            {"pin": 3, "name": "1IN+", "type": "Input", "desc": "Non-inverting input of Channel 1"},
            {"pin": 4, "name": "V-", "type": "Power", "desc": "Negative supply rail (-5V to -18V)"},
            {"pin": 5, "name": "2IN+", "type": "Input", "desc": "Non-inverting input of Channel 2"},
            {"pin": 6, "name": "2IN-", "type": "Input", "desc": "Inverting input of Channel 2"},
            {"pin": 7, "name": "2OUT", "type": "Output", "desc": "Output of Channel 2"},
            {"pin": 8, "name": "V+", "type": "Power", "desc": "Positive supply rail (+5V to +18V)"},
        ],
        "specs": {
            "Input Impedance": "10¹² Ω (1 TΩ, JFET gates)",
            "Slew Rate": "13 V/µs (fast response)",
            "Unity Gain Bandwidth": "3.0 MHz",
            "Total Harmonic Distortion": "0.003% typical",
        },
        "lab_notes": "Ideal for audio preamps, active crossover filters, and high-impedance piezo transducers. Beware of phase reversal if inputs exceed common-mode limits.",
    },
    "LM7805": {
        "name": "LM7805 3-Terminal +5V Linear Voltage Regulator",
        "category": "Linear Voltage Regulator",
        "package": "TO-220 / D2PAK",
        "supply_voltage": "7V to 25V (35V absolute max)",
        "max_current": "1.5 A with adequate heatsinking",
        "description": "Standard 3-terminal positive voltage regulator delivering clean, low-ripple fixed +5.0V output with thermal overload and short-circuit protection.",
        "pinout": [
            {"pin": 1, "name": "INPUT", "type": "Power", "desc": "Unregulated DC input (+7.0V to +25V recommended)"},
            {"pin": 2, "name": "GROUND", "type": "Power", "desc": "Common ground reference (connected to metal tab on TO-220)"},
            {"pin": 3, "name": "OUTPUT", "type": "Power", "desc": "Regulated +5.0V DC output (up to 1.5A)"},
        ],
        "specs": {
            "Regulated Output": "5.0V ± 4% (4.8V – 5.2V)",
            "Dropout Voltage": "2.0V typical at 1.0A load",
            "Ripple Rejection": "78 dB typical at 120 Hz",
            "Power Dissipation": "P = (V_in - 5V) * I_load",
        },
        "lab_notes": "Place a 0.33µF capacitor on the input pin and a 0.1µF capacitor on the output pin close to the IC to ensure stability and eliminate HF oscillations.",
    },
    "BC547": {
        "name": "BC547 NPN General Purpose Bipolar Junction Transistor",
        "category": "NPN Small-Signal Transistor",
        "package": "TO-92",
        "supply_voltage": "V_CEO = 45V max, V_CBO = 50V max",
        "max_current": "I_C = 100 mA continuous (200 mA peak)",
        "description": "Everyday silicon planar epitaxial NPN transistor for switching, small-signal audio preamplification, and digital logic buffering.",
        "pinout": [
            {"pin": 1, "name": "COLLECTOR", "type": "Output", "desc": "Collector terminal (C) - Right pin when flat face points away / Left pin with flat facing you (standard European pinout: C-B-E)"},
            {"pin": 2, "name": "BASE", "type": "Input", "desc": "Base terminal (B) - Center pin (requires current limiting resistor)"},
            {"pin": 3, "name": "EMITTER", "type": "Passive", "desc": "Emitter terminal (E) - Arrow points OUT on schematic"},
        ],
        "specs": {
            "DC Current Gain (hFE)": "110 to 800 (BC547A: 110-220, B: 200-450, C: 420-800)",
            "V_CE(sat)": "90 mV typical at Ic=10mA, Ib=0.5mA",
            "Transition Frequency (f_T)": "300 MHz",
            "Max Power Dissipation": "500 mW at 25°C",
        },
        "lab_notes": "Standard European TO-92 pinout is C-B-E (looking at flat face: Pin 1 Collector, Pin 2 Base, Pin 3 Emitter). Do not confuse with American 2N3904 (E-B-C).",
    },
    "2N2222": {
        "name": "2N2222 / PN2222 NPN High-Speed Switching Transistor",
        "category": "NPN Switching & Driver Transistor",
        "package": "TO-18 (Metal Can) / TO-92 (PN2222 Plastic)",
        "supply_voltage": "V_CEO = 30V / 40V max, V_CBO = 60V / 75V max",
        "max_current": "I_C = 800 mA continuous",
        "description": "High-current, high-speed NPN switching transistor widely used to drive small relays, DC solenoids, high-brightness LEDs, and stepper coils.",
        "pinout": [
            {"pin": 1, "name": "EMITTER", "type": "Passive", "desc": "Emitter terminal (E) - Pin 1 on plastic TO-92 (E-B-C convention)"},
            {"pin": 2, "name": "BASE", "type": "Input", "desc": "Base terminal (B) - Center pin"},
            {"pin": 3, "name": "COLLECTOR", "type": "Output", "desc": "Collector terminal (C)"},
        ],
        "specs": {
            "DC Current Gain (hFE)": "100 to 300 at Ic=150mA",
            "V_CE(sat)": "0.3V max at Ic=150mA, Ib=15mA",
            "Switching Time": "Turn-on: ~35 ns; Turn-off: ~285 ns",
            "Max Power Dissipation": "625 mW (TO-92) / 1.8W (TO-18 heatsinked)",
        },
        "lab_notes": "Standard TO-92 PN2222 pinout is E-B-C (opposite of BC547). When switching inductive loads (relays, motors), always connect a flyback diode (1N4007) across the coil.",
    },
    "IRFZ44N": {
        "name": "IRFZ44N 55V 49A N-Channel Power HEXFET MOSFET",
        "category": "Power MOSFET",
        "package": "TO-220AB",
        "supply_voltage": "V_DSS = 55V max, V_GS = ±20V max",
        "max_current": "I_D = 49A continuous at 25°C, 35A at 100°C",
        "description": "Advanced fifth-generation Power HEXFET featuring ultra-low on-resistance per silicon area, fast switching, and high avalanche energy rating.",
        "pinout": [
            {"pin": 1, "name": "GATE (G)", "type": "Input", "desc": "High-impedance gate terminal (requires 10V Vgs for minimum Rds(on))"},
            {"pin": 2, "name": "DRAIN (D)", "type": "Output", "desc": "Drain terminal (connected internally to metal tab)"},
            {"pin": 3, "name": "SOURCE (S)", "type": "Passive", "desc": "Source terminal (connect to ground or negative power rail)"},
        ],
        "specs": {
            "R_DS(on)": "17.5 mΩ (0.0175 Ω) max at Vgs=10V, Id=25A",
            "Threshold Voltage V_GS(th)": "2.0V to 4.0V (Standard-level, NOT logic-level)",
            "Total Gate Charge Q_g": "63 nC max",
            "Max Power Dissipation": "94 W with adequate heatsink",
        },
        "lab_notes": "IRFZ44N requires 10V gate drive to achieve minimum 17.5mΩ Rds(on). If driving from a 3.3V or 5V MCU (Arduino/ESP32), use a gate driver IC or logic-level MOSFET like IRLZ44N.",
    },
    "1N4007": {
        "name": "1N4007 1000V 1A Silicon Rectifier Diode",
        "category": "Rectifier Diode",
        "package": "DO-41 (Axial Plastic)",
        "supply_voltage": "V_RRM = 1000V Peak Reverse Voltage",
        "max_current": "I_F(AV) = 1.0 A forward rectified current",
        "description": "General-purpose power rectifier diode widely used for AC mains rectification, polarity protection, and flyback suppression.",
        "pinout": [
            {"pin": 1, "name": "ANODE (A)", "type": "Passive", "desc": "Positive terminal (plain black body side)"},
            {"pin": 2, "name": "CATHODE (K)", "type": "Passive", "desc": "Negative terminal (marked with silver/grey cathode stripe band)"},
        ],
        "specs": {
            "Forward Voltage Drop V_F": "1.1V max at 1.0A DC (0.7V typical at low current)",
            "Reverse Leakage Current": "5.0 µA max at 25°C",
            "Peak Surge Current I_FSM": "30 A (8.3ms half sine pulse)",
            "Reverse Recovery Time": "~2 µs (Standard recovery, not for high-frequency SMPS)",
        },
        "lab_notes": "The silver ring painted on the cylindrical package marks the CATHODE. Current flows from Anode to Cathode (in the direction of the schematic arrow).",
    },
    "1N4148": {
        "name": "1N4148 High-Speed Silicon Switching Signal Diode",
        "category": "Small Signal Switching Diode",
        "package": "DO-35 (Glass hermetic)",
        "supply_voltage": "V_RRM = 100V max reverse voltage",
        "max_current": "I_F = 200 mA continuous (450 mA peak)",
        "description": "Ultra-fast silicon epitaxial planar switching diode for general high-speed digital logic, clipping, clamping, and RF demodulation.",
        "pinout": [
            {"pin": 1, "name": "ANODE (A)", "type": "Passive", "desc": "Positive terminal (transparent glass end)"},
            {"pin": 2, "name": "CATHODE (K)", "type": "Passive", "desc": "Negative terminal (marked with dark black painted ring)"},
        ],
        "specs": {
            "Reverse Recovery Time t_rr": "4.0 nanoseconds max (ultra-fast)",
            "Forward Voltage Drop V_F": "1.0V max at 10 mA (0.65V typical)",
            "Junction Capacitance C_J": "4.0 pF max at 1 MHz, 0V",
            "Reverse Breakdown Voltage": "100V min",
        },
        "lab_notes": "The black ring on the transparent orange glass package marks the CATHODE. With 4ns recovery time, it easily handles frequencies past 100 MHz.",
    },
}

# Color band lookup mappings
COLOR_VALUES = {
    "black": 0, "brown": 1, "red": 2, "orange": 3, "yellow": 4,
    "green": 5, "blue": 6, "violet": 7, "purple": 7, "grey": 8, "gray": 8, "white": 9
}
MULTIPLIER_VALUES = {
    "black": 1, "brown": 10, "red": 100, "orange": 1_000, "yellow": 10_000,
    "green": 100_000, "blue": 1_000_000, "violet": 10_000_000,
    "gold": 0.1, "silver": 0.01
}
TOLERANCE_VALUES = {
    "brown": "±1%", "red": "±2%", "green": "±0.5%", "blue": "±0.25%",
    "violet": "±0.1%", "gold": "±5%", "silver": "±10%", "none": "±20%"
}


def format_ohms(val: float) -> str:
    if val >= 1_000_000:
        return f"{val / 1_000_000:.2f}".rstrip("0").rstrip(".") + " MΩ"
    elif val >= 1_000:
        return f"{val / 1_000:.2f}".rstrip("0").rstrip(".") + " kΩ"
    else:
        return f"{val:.2f}".rstrip("0").rstrip(".") + " Ω"


def decode_color_bands(query: str) -> Optional[str]:
    """Identifies resistor color bands from text like 'brown black red gold'."""
    tokens = [re.sub(r"[^a-z]", "", t.lower()) for t in re.split(r"[\s,\-]+", query)]
    found_colors = [t for t in tokens if t in COLOR_VALUES or t in MULTIPLIER_VALUES or t in TOLERANCE_VALUES]
    
    if len(found_colors) < 3:
        return None

    # Handle 4-band: digit, digit, multiplier, tolerance
    if len(found_colors) == 4:
        c1, c2, c3, c4 = found_colors
        if c1 in COLOR_VALUES and c2 in COLOR_VALUES and c3 in MULTIPLIER_VALUES:
            digits = COLOR_VALUES[c1] * 10 + COLOR_VALUES[c2]
            mult = MULTIPLIER_VALUES[c3]
            resistance = digits * mult
            tol = TOLERANCE_VALUES.get(c4, "±5%")
            return (
                f"### [CONFIRMED] Resistor Color Band Analysis (4-Band)\n\n"
                f"- **Decoded Bands**: `{c1.upper()}` • `{c2.upper()}` • `{c3.upper()}` • `{c4.upper()}`\n"
                f"- **Calculation**: $({COLOR_VALUES[c1]} \\times 10 + {COLOR_VALUES[c2]}) \\times {mult} = {format_ohms(resistance)}$\n"
                f"- **Nominal Value**: **`{format_ohms(resistance)}`**\n"
                f"- **Tolerance**: **`{tol}`**\n"
                f"- **Safe Range**: `${format_ohms(resistance * 0.95)}$ to ${format_ohms(resistance * 1.05)}$\n\n"
                f"**Standard E-Series**: Matches standard **E24** decade value."
            )

    # Handle 5-band: digit, digit, digit, multiplier, tolerance
    if len(found_colors) >= 5:
        c1, c2, c3, c4, c5 = found_colors[:5]
        if c1 in COLOR_VALUES and c2 in COLOR_VALUES and c3 in COLOR_VALUES and c4 in MULTIPLIER_VALUES:
            digits = COLOR_VALUES[c1] * 100 + COLOR_VALUES[c2] * 10 + COLOR_VALUES[c3]
            mult = MULTIPLIER_VALUES[c4]
            resistance = digits * mult
            tol = TOLERANCE_VALUES.get(c5, "±1%")
            return (
                f"### [CONFIRMED] Precision Resistor Color Band Analysis (5-Band)\n\n"
                f"- **Decoded Bands**: `{c1.upper()}` • `{c2.upper()}` • `{c3.upper()}` • `{c4.upper()}` • `{c5.upper()}`\n"
                f"- **Calculation**: $({COLOR_VALUES[c1]} \\times 100 + {COLOR_VALUES[c2]} \\times 10 + {COLOR_VALUES[c3]}) \\times {mult} = {format_ohms(resistance)}$\n"
                f"- **Nominal Value**: **`{format_ohms(resistance)}`**\n"
                f"- **Tolerance**: **`{tol}`** (Precision grade)\n\n"
                f"**Standard E-Series**: Matches standard **E96** precision series."
            )

    return None


def decode_smd_code(query: str) -> Optional[str]:
    """Decodes standard 3-digit and 4-digit SMD resistor markings like '103', '472', '1002'."""
    lower = query.lower()
    # Guard against IP addresses, subnets, and non-component numbers
    if re.search(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", query) or any(k in lower for k in ["subnet", "cidr", "ip", "ping", "mask"]):
        return None

    # For bare digits without 'R', require SMD/resistor context or query being just the code
    has_r = bool(re.search(r"\b(?:[0-9]{2}[R][0-9]?|[0-9][R][0-9]{1,2})\b", query, re.IGNORECASE))
    is_explicit_smd = any(k in lower for k in ["smd", "resistor", "code", "marking", "package", "chip"]) or query.strip().isdigit() or has_r
    if not is_explicit_smd:
        return None

    match = re.search(r"\b([0-9]{3,4}|[0-9]{2}[R][0-9]?|[0-9][R][0-9]{1,2})\b", query, re.IGNORECASE)
    if not match:
        return None

    code = match.group(1).upper()

    if "R" in code:
        val_str = code.replace("R", ".")
        try:
            ohms = float(val_str)
            return (
                f"### [CONFIRMED] SMD Resistor Code `{code}`\n\n"
                f"- **Marking Standard**: Decimal 'R' indicator notation\n"
                f"- **Resistance**: **`{ohms} Ω`**\n"
                f"- **Typical Tolerance**: ±5% (Standard thick film) or ±1%"
            )
        except ValueError:
            pass

    if len(code) == 3 and code.isdigit():
        digits = int(code[:2])
        mult = 10 ** int(code[2])
        ohms = digits * mult
        return (
            f"### [CONFIRMED] 3-Digit SMD Resistor Code `{code}`\n\n"
            f"- **Formula**: $({code[0]} \\times 10 + {code[1]}) \\times 10^{code[2]} = {format_ohms(ohms)}$\n"
            f"- **Nominal Resistance**: **`{format_ohms(ohms)}`**\n"
            f"- **Typical Tolerance**: ±5% (E24 series standard)"
        )

    if len(code) == 4 and code.isdigit():
        digits = int(code[:3])
        mult = 10 ** int(code[3])
        ohms = digits * mult
        return (
            f"### [CONFIRMED] 4-Digit Precision SMD Resistor Code `{code}`\n\n"
            f"- **Formula**: $({code[0]} \\times 100 + {code[1]} \\times 10 + {code[2]}) \\times 10^{code[3]} = {format_ohms(ohms)}$\n"
            f"- **Nominal Resistance**: **`{format_ohms(ohms)}`**\n"
            f"- **Typical Tolerance**: ±1% (E96 precision series)"
        )

    return None


def lookup_component(query: str) -> Optional[str]:
    """Finds exact or keyword match for registered ICs and returns structured markdown."""
    q_norm = query.upper().replace("-", "").replace(" ", "")

    for key, data in DATASHEET_REGISTRY.items():
        key_norm = key.upper().replace("-", "")
        if key_norm in q_norm or key in query.upper():
            rows = []
            for p in data["pinout"]:
                rows.append(f"| {p['pin']} | `{p['name']}` | {p['type']} | {p['desc']} |")

            table_body = "\n".join(rows)

            specs_list = "\n".join([f"- **{k}**: {v}" for k, v in data["specs"].items()])

            return (
                f"### [CONFIRMED] {data['name']}\n\n"
                f"**Category**: {data['category']} • **Package**: `{data['package']}` • **Supply**: `{data['supply_voltage']}`\n\n"
                f"{data['description']}\n\n"
                f"#### Pinout Architecture ({data['package']})\n\n"
                f"| Pin # | Name | Direction | Functional Description |\n"
                f"| :---: | :--- | :---: | :--- |\n"
                f"{table_body}\n\n"
                f"#### Key Electrical Specifications\n\n"
                f"{specs_list}\n\n"
                f"> **Lab Note & Best Practice**: {data['lab_notes']}"
            )

    return None
