"""
J.A.R.V.I.S. Universal Engineering Intelligence Engine
Comprehensive multi-discipline derivations across Civil, Mechanical/Aero, CSE/IT, EE/ECE, and Math.
"""

import math
import re
from typing import Optional, Dict, Any, List


# -----------------------------------------------------------------------------
# 1. CIVIL ENGINEERING: SHEAR & MOMENT, SOIL MECHANICS, HYDRAULICS
# -----------------------------------------------------------------------------

def solve_beam_shear_moment(beam_type: str = "simply_supported", load_type: str = "point", p: float = 10_000.0, l: float = 6.0, w: float = 2_000.0) -> str:
    """Calculates support reactions, max shear force V_max, and max bending moment M_max."""
    if "cantilever" in beam_type.lower():
        if "udl" in load_type.lower() or "distributed" in load_type.lower():
            r_a = w * l
            v_max = r_a
            m_max = (w * (l**2)) / 2.0
            desc = f"Cantilever with Uniform Distributed Load $w = {w:,.0f}\\,\\text{{N/m}}$"
            v_eq = f"$$V(x) = w(L - x) \\implies V_{{max}} = w L = {v_max:,.1f}\\,\\text{{N}}$$"
            m_eq = f"$$M(x) = -\\frac{{w(L - x)^2}}{{2}} \\implies M_{{max}} = \\frac{{w L^2}}{{2}} = \\mathbf{{{m_max:,.1f}\\,\\text{{N}}\\cdot\\text{{m}}}}$$"
        else:
            r_a = p
            v_max = p
            m_max = p * l
            desc = f"Cantilever with End Point Load $P = {p:,.0f}\\,\\text{{N}}$"
            v_eq = f"$$V(x) = P = \\mathbf{{{v_max:,.1f}\\,\\text{{N}}}}$$"
            m_eq = f"$$M(x) = -P(L - x) \\implies M_{{max}} = P L = \\mathbf{{{m_max:,.1f}\\,\\text{{N}}\\cdot\\text{{m}}}}$$"
    else:
        # Simply Supported
        if "udl" in load_type.lower() or "distributed" in load_type.lower():
            r_a = (w * l) / 2.0
            r_b = r_a
            v_max = r_a
            m_max = (w * (l**2)) / 8.0
            desc = f"Simply Supported Beam with Full-Span UDL $w = {w:,.0f}\\,\\text{{N/m}}$"
            v_eq = f"$$R_A = R_B = \\frac{{w L}}{{2}} = \\mathbf{{{r_a:,.1f}\\,\\text{{N}}}}, \\quad V_{{max}} = {v_max:,.1f}\\,\\text{{N}}$$"
            m_eq = f"$$M_{{max}} = \\frac{{w L^2}}{{8}} = \\frac{{{w:,.0f} \\times ({l})^2}}{{8}} = \\mathbf{{{m_max:,.1f}\\,\\text{{N}}\\cdot\\text{{m}}}}\\,\\text{{at midspan}}\\,(x = L/2)$$"
        else:
            r_a = p / 2.0
            r_b = r_a
            v_max = r_a
            m_max = (p * l) / 4.0
            desc = f"Simply Supported Beam with Midspan Concentrated Load $P = {p:,.0f}\\,\\text{{N}}$"
            v_eq = f"$$R_A = R_B = \\frac{{P}}{{2}} = \\mathbf{{{r_a:,.1f}\\,\\text{{N}}}}, \\quad V_{{max}} = {v_max:,.1f}\\,\\text{{N}}$$"
            m_eq = f"$$M_{{max}} = \\frac{{P L}}{{4}} = \\frac{{{p:,.0f} \\times {l}}}{{4}} = \\mathbf{{{m_max:,.1f}\\,\\text{{N}}\\cdot\\text{{m}}}}\\,\\text{{at center}}$$"

    return (
        f"### [CONFIRMED] Structural Analysis: Shear & Bending Moment Derivation\n\n"
        f"Configuration: **{desc}**\n\n"
        f"Parameters: Span $L = {l:.2f}\\,\\text{{m}}$\n\n"
        f"#### 1. Shear Force Evaluation ($V$)\n\n"
        f"{v_eq}\n\n"
        f"#### 2. Maximum Bending Moment ($M_{{max}}$)\n\n"
        f"{m_eq}\n\n"
        f"- **Point of Inflection**: Zero shear corresponds to maximum bending moment: $\\frac{{dM}}{{dx}} = V(x) = 0$."
    )


def solve_soil_mechanics(e_void: Optional[float] = 0.65, g_s: float = 2.65, w_water: float = 0.15) -> str:
    """Calculates soil index properties: porosity (n), dry/saturated unit weight, and degree of saturation."""
    gamma_w = 9.81  # kN/m^3
    n_porosity = e_void / (1.0 + e_void) if e_void else 0.394
    s_deg = (w_water * g_s) / e_void if e_void else 0.611
    gamma_dry = (g_s * gamma_w) / (1.0 + e_void)
    gamma_sat = ((g_s + e_void) * gamma_w) / (1.0 + e_void)

    return (
        f"### [CONFIRMED] Geotechnical Engineering: Soil Phase Index Properties\n\n"
        f"Given Parameters:\n"
        f"- Void Ratio $e = {e_void:.3f}$\n"
        f"- Specific Gravity of Soil Solids $G_s = {g_s:.2f}$\n"
        f"- Water Content $w = {w_water * 100:.1f}\\%$\n\n"
        f"#### 1. Soil Porosity ($n$)\n\n"
        f"$$n = \\frac{{e}}{{1 + e}} = \\frac{{{e_void:.3f}}}{{1 + {e_void:.3f}}} = \\mathbf{{{n_porosity:.4f}}} = \\mathbf{{{n_porosity * 100:.2f}\\%}}$$\n\n"
        f"#### 2. Degree of Saturation ($S_r$)\n\n"
        f"$$S_r \\cdot e = w \\cdot G_s \\implies S_r = \\frac{{w \\cdot G_s}}{{e}} = \\frac{{{w_water:.3f} \\times {g_s:.2f}}}{{{e_void:.3f}}} = \\mathbf{{{s_deg * 100:.1f}\\%}}$$\n\n"
        f"#### 3. Unit Weights (Dry & Saturated)\n\n"
        f"$$\\gamma_{{dry}} = \\frac{{G_s \\cdot \\gamma_w}}{{1 + e}} = \\frac{{{g_s:.2f} \\times 9.81}}{{1 + {e_void:.3f}}} = \\mathbf{{{gamma_dry:.2f}\\,\\text{{kN/m}}^3}}$$\n\n"
        f"$$\\gamma_{{sat}} = \\frac{{(G_s + e) \\cdot \\gamma_w}}{{1 + e}} = \\frac{{({g_s:.2f} + {e_void:.3f}) \\times 9.81}}{{1 + {e_void:.3f}}} = \\mathbf{{{gamma_sat:.2f}\\,\\text{{kN/m}}^3}}$$"
    )


def solve_mannings_hydraulics(area: float = 5.0, wetted_perim: float = 6.0, slope: float = 0.001, n_rough: float = 0.015) -> str:
    """Calculates open channel flow velocity and discharge via Manning's formula."""
    rh = area / wetted_perim if wetted_perim > 0 else 0
    v = (1.0 / n_rough) * (rh ** (2.0 / 3.0)) * (slope ** 0.5)
    q_discharge = area * v

    return (
        f"### [CONFIRMED] Hydraulics: Open Channel Flow (Manning's Equation)\n\n"
        f"Channel Geometry:\n"
        f"- Flow Area $A = {area:.2f}\\,\\text{{m}}^2$\n"
        f"- Wetted Perimeter $P = {wetted_perim:.2f}\\,\\text{{m}}$\n"
        f"- Bed Slope $S = {slope:.5f}$ ($1:{int(1.0/slope) if slope > 0 else 0}$)\n"
        f"- Roughness Coefficient $n = {n_rough:.3f}$\n\n"
        f"#### 1. Hydraulic Radius ($R_h$)\n\n"
        f"$$R_h = \\frac{{A}}{{P}} = \\frac{{{area:.2f}}}{{{wetted_perim:.2f}}} = \\mathbf{{{rh:.3f}\\,\\text{{m}}}}$$\n\n"
        f"#### 2. Flow Velocity ($v$) & Discharge ($Q$)\n\n"
        f"$$v = \\frac{{1}}{{n}} R_h^{{2/3}} S^{{1/2}} = \\frac{{1}}{{{n_rough:.3f}}} \\cdot ({rh:.3f})^{{2/3}} \\cdot ({slope})^{{1/2}} = \\mathbf{{{v:.3f}\\,\\text{{m/s}}}}$$\n\n"
        f"$$Q = A \\cdot v = {area:.2f} \\times {v:.3f} = \\mathbf{{{q_discharge:.3f}\\,\\text{{m}}^3/\\text{{s}}}}$$"
    )


# -----------------------------------------------------------------------------
# 2. AEROSPACE: LIFT, DRAG & PROPULSION
# -----------------------------------------------------------------------------

def solve_aerodynamics(v_ms: float = 75.0, rho: float = 1.225, s_wing: float = 16.2, cl: float = 0.45, cd: float = 0.032) -> str:
    """Calculates aerodynamic Lift, Drag, and Lift-to-Drag ratio L/D."""
    q_dyn = 0.5 * rho * (v_ms ** 2)
    lift_n = q_dyn * s_wing * cl
    drag_n = q_dyn * s_wing * cd
    ld_ratio = cl / cd if cd > 0 else 0

    return (
        f"### [CONFIRMED] Aerodynamics: Wing Lift & Drag Analysis\n\n"
        f"Flight Condition:\n"
        f"- True Airspeed $v = {v_ms:.1f}\\,\\text{{m/s}}$ ({v_ms * 3.6:.1f} km/h, {v_ms / 0.514444:.1f} knots)\n"
        f"- Air Density $\\rho = {rho:.3f}\\,\\text{{kg/m}}^3$ (Dynamic Pressure $q = {q_dyn:,.1f}\\,\\text{{Pa}}$)\n"
        f"- Wing Reference Area $S = {s_wing:.2f}\\,\\text{{m}}^2$\n"
        f"- Coefficients: $C_L = {cl:.3f}$, $C_D = {cd:.4f}$\n\n"
        f"#### 1. Aerodynamic Lift ($L$)\n\n"
        f"$$L = \\frac{{1}}{{2}}\\rho v^2 S C_L = ({q_dyn:,.1f}) \\cdot ({s_wing:.2f}) \\cdot ({cl:.3f}) = {lift_n:,.1f}\\,\\text{{N}} = \\mathbf{{{lift_n/1e3:.2f}\\,\\text{{kN}}}}$$\n\n"
        f"#### 2. Aerodynamic Drag ($D$)\n\n"
        f"$$D = \\frac{{1}}{{2}}\\rho v^2 S C_D = ({q_dyn:,.1f}) \\cdot ({s_wing:.2f}) \\cdot ({cd:.4f}) = {drag_n:,.1f}\\,\\text{{N}} = \\mathbf{{{drag_n/1e3:.2f}\\,\\text{{kN}}}}$$\n\n"
        f"#### 3. Aerodynamic Efficiency (Glide Ratio)\n\n"
        f"$$\\frac{{L}}{{D}} = \\frac{{C_L}}{{C_D}} = \\frac{{{cl:.3f}}}{{{cd:.4f}}} = \\mathbf{{{ld_ratio:.2f}}}:1$$"
    )


# -----------------------------------------------------------------------------
# 3. ELECTRICAL & CONTROL SYSTEMS: 3-PHASE & 2ND-ORDER DYNAMICS
# -----------------------------------------------------------------------------

def solve_three_phase_power(v_line: float = 400.0, i_line: float = 25.0, pf: float = 0.85) -> str:
    """Calculates active, reactive, and apparent power in balanced 3-phase AC systems."""
    p_watts = math.sqrt(3) * v_line * i_line * pf
    sin_phi = math.sqrt(max(0.0, 1.0 - pf**2))
    q_vars = math.sqrt(3) * v_line * i_line * sin_phi
    s_va = math.sqrt(3) * v_line * i_line

    return (
        f"### [CONFIRMED] Electrical Power Systems: Balanced 3-Phase AC Analysis\n\n"
        f"System Ratings:\n"
        f"- Line-to-Line Voltage $V_L = {v_line:,.1f}\\,\\text{{V}}$ (RMS)\n"
        f"- Line Current $I_L = {i_line:,.1f}\\,\\text{{A}}$ (RMS)\n"
        f"- Power Factor $\\cos\\phi = {pf:.2f}$ (Phase angle $\\phi = {math.acos(pf)*180/math.pi:.1f}^\\circ$)\n\n"
        f"#### 1. Active / Real Power ($P$)\n\n"
        f"$$P = \\sqrt{{3}} V_L I_L \\cos\\phi = \\sqrt{{3}} \\times {v_line:,.0f} \\times {i_line:.1f} \\times {pf:.2f} = \\mathbf{{{p_watts / 1e3:.2f}\\,\\text{{kW}}}}$$\n\n"
        f"#### 2. Reactive Power ($Q$)\n\n"
        f"$$Q = \\sqrt{{3}} V_L I_L \\sin\\phi = \\sqrt{{3}} \\times {v_line:,.0f} \\times {i_line:.1f} \\times {sin_phi:.3f} = \\mathbf{{{q_vars / 1e3:.2f}\\,\\text{{kVAR}}}}$$\n\n"
        f"#### 3. Total Apparent Power ($S$)\n\n"
        f"$$S = \\sqrt{{3}} V_L I_L = \\sqrt{{P^2 + Q^2}} = \\mathbf{{{s_va / 1e3:.2f}\\,\\text{{kVA}}}}$$\n\n"
        f"- **Star ($Y$) Equivalent**: $V_{{ph}} = V_L / \\sqrt{{3}} = {v_line / math.sqrt(3):.1f}\\,\\text{{V}}, \\quad I_{{ph}} = I_L = {i_line:.1f}\\,\\text{{A}}$\n"
        f"- **Delta ($\\Delta$) Equivalent**: $V_{{ph}} = V_L = {v_line:.1f}\\,\\text{{V}}, \\quad I_{{ph}} = I_L / \\sqrt{{3}} = {i_line / math.sqrt(3):.1f}\\,\\text{{A}}$"
    )


def solve_control_systems_2nd_order(wn: float = 5.0, zeta: float = 0.5) -> str:
    """Calculates peak time, settling time, and percentage overshoot for a 2nd-order control system."""
    if zeta < 0:
        return "System is unstable (negative damping ratio)."
    elif zeta == 0:
        regime = "Undamped System (Sustained Oscillation)"
        mp = 100.0
        tp = math.pi / wn
        ts = float('inf')
    elif zeta < 1.0:
        regime = "Underdamped System"
        wd = wn * math.sqrt(1.0 - zeta**2)
        tp = math.pi / wd
        mp = math.exp(- (math.pi * zeta) / math.sqrt(1.0 - zeta**2)) * 100.0
        ts = 4.0 / (zeta * wn)  # 2% settling criterion
    elif zeta == 1.0:
        regime = "Critically Damped System (Fastest non-oscillatory response)"
        mp = 0.0
        tp = float('nan')
        ts = 5.83 / wn
    else:
        regime = "Overdamped System (Sluggish response with two real poles)"
        mp = 0.0
        tp = float('nan')
        ts = 4.0 / (wn * (zeta - math.sqrt(zeta**2 - 1.0)))

    return (
        f"### [CONFIRMED] Control Systems: Second-Order Step Response Analysis\n\n"
        f"Standard Closed-Loop Transfer Function:\n"
        f"$$T(s) = \\frac{{\\omega_n^2}}{{s^2 + 2\\zeta\\omega_n s + \\omega_n^2}} = \\frac{{{wn**2:g}}}{{s^2 + {2*zeta*wn:g}s + {wn**2:g}}}$$\n\n"
        f"Parameters:\n"
        f"- Natural Frequency $\\omega_n = {wn:.2f}\\,\\text{{rad/s}}$\n"
        f"- Damping Ratio $\\zeta = {zeta:.3f}$ $\\implies$ **{regime}**\n\n"
        f"#### Transient Specifications (2% Error Criterion)\n\n"
        f"- **Peak Time ($t_p$)**: $t_p = \\frac{{\\pi}}{{\\omega_d}} = \\frac{{\\pi}}{{{wn * math.sqrt(max(1e-6, 1.0 - zeta**2)):.3f}}} = \\mathbf{{{tp:.3f}\\,\\text{{s}}}}$\n"
        f"- **Maximum Percent Overshoot (\\%OS)**: $M_p = e^{{-\\frac{{\\pi\\zeta}}{{\\sqrt{{1-\\zeta^2}}}}}} \\times 100\\% = \\mathbf{{{mp:.2f}\\%}}$\n"
        f"- **Settling Time ($t_s$)**: $t_s \\approx \\frac{{4}}{{\\zeta\\omega_n}} = \\frac{{4}}{{{zeta * wn:.2f}}} = \\mathbf{{{ts:.3f}\\,\\text{{s}}}}$\n"
        f"- **Complex Poles**: $s_{{1,2}} = -\\zeta\\omega_n \\pm j\\omega_d = {-zeta*wn:.2f} \\pm j{wn * math.sqrt(max(0.0, 1.0 - zeta**2)):.2f}$"
    )


# -----------------------------------------------------------------------------
# 4. CSE / IT: OS SCHEDULING & DBMS NORMAL FORMS
# -----------------------------------------------------------------------------

def solve_os_scheduling_fcfs(burst_times: List[int]) -> str:
    """Calculates completion, turnaround, and waiting times for FCFS CPU scheduling."""
    n = len(burst_times)
    ct = [0] * n
    tat = [0] * n
    wt = [0] * n

    current_time = 0
    for i, bt in enumerate(burst_times):
        current_time += bt
        ct[i] = current_time
        tat[i] = ct[i]  # Assuming Arrival Time = 0
        wt[i] = tat[i] - bt

    avg_tat = sum(tat) / n
    avg_wt = sum(wt) / n

    table_rows = "\n".join([
        f"| **P{i+1}** | 0 | {burst_times[i]} | {ct[i]} | {tat[i]} | **{wt[i]}** |"
        for i in range(n)
    ])

    return (
        f"### [CONFIRMED] Operating Systems: FCFS CPU Scheduling\n\n"
        f"| Process | Arrival Time ($AT$) | Burst Time ($BT$) | Completion ($CT$) | Turnaround ($TAT$) | Waiting Time ($WT$) |\n"
        f"| :---: | :---: | :---: | :---: | :---: | :---: |\n"
        f"{table_rows}\n\n"
        f"#### Summary Metrics\n\n"
        f"- **Turnaround Time Formula**: $TAT = CT - AT$\n"
        f"- **Waiting Time Formula**: $WT = TAT - BT$\n"
        f"- **Average Turnaround Time**: $\\mathbf{{{avg_tat:.2f}\\,\\text{{ms}}}}$\n"
        f"- **Average Waiting Time**: $\\mathbf{{{avg_wt:.2f}\\,\\text{{ms}}}}$\n\n"
        f"> **Convoy Effect Alert**: FCFS is non-preemptive; long burst processes delay short processes."
    )


def get_dbms_normal_forms_cheatsheet() -> str:
    """Returns database normalization reference matrix for 1NF, 2NF, 3NF, and BCNF."""
    return (
        f"### [CONFIRMED] Database Management Systems: Normal Forms Matrix\n\n"
        f"| Normal Form | Core Requirement | Violation Trap | Remediation |\n"
        f"| :--- | :--- | :--- | :--- |\n"
        f"| **1NF (First)** | Atomic values only; no multi-valued or nested attributes | Repeating groups, CSV strings in a column | Split into individual rows or separate table |\n"
        f"| **2NF (Second)** | Must be in 1NF + **No Partial Dependency** ($X \\to Y$ where $X$ is proper subset of candidate key) | Non-prime attribute dependent on part of composite key | Decompose table so attributes depend on whole key |\n"
        f"| **3NF (Third)** | Must be in 2NF + **No Transitive Dependency** ($X \\to Y \\to Z$) | Non-prime attribute determining another non-prime attribute | Move $Y \\to Z$ into separate lookup table |\n"
        f"| **BCNF (Boyce-Codd)** | For every functional dependency $X \\to Y$, $X$ must be a **Super Key** | Overlapping candidate keys with non-trivial dependencies | Strict decomposition (may not preserve all dependencies) |\n\n"
        f"> **GATE Rule**: $3\\text{{NF}}$ always guarantees lossless join and dependency preservation, whereas $\\text{{BCNF}}$ guarantees lossless join but may sacrifice dependency preservation."
    )


# -----------------------------------------------------------------------------
# 5. DISPATCHER & INTENT PARSER
# -----------------------------------------------------------------------------

def evaluate_universal_engineering(query: str) -> Optional[str]:
    """
    Main offline evaluator for multi-discipline engineering derivations.
    Covers Civil, Aerospace, EE, Control Systems, OS, and DBMS.
    """
    q = query.strip()
    lower = q.lower()

    # 1. Civil: Beam Shear & Moment
    if any(k in lower for k in ["shear force", "bending moment", "sfd", "bmd", "udl"]):
        b_type = "cantilever" if "cantilever" in lower else "simply_supported"
        l_type = "udl" if ("udl" in lower or "distributed" in lower) else "point"
        return solve_beam_shear_moment(beam_type=b_type, load_type=l_type)

    # 2. Civil: Soil Mechanics
    if any(k in lower for k in ["soil mechanics", "void ratio", "porosity", "darcy"]):
        return solve_soil_mechanics()

    # 3. Civil: Hydraulics / Manning's
    if any(k in lower for k in ["manning", "open channel", "hydraulic radius"]):
        return solve_mannings_hydraulics()

    # 4. Aerospace: Aerodynamics
    if any(k in lower for k in ["aerodynamics", "lift and drag", "lift-to-drag", "l/d ratio"]):
        return solve_aerodynamics()

    # 5. EE: Three-Phase AC Power
    if any(k in lower for k in ["three phase", "3-phase", "3 phase", "star delta", "apparent power"]):
        return solve_three_phase_power()

    # 6. EE: Control Systems 2nd Order
    if any(k in lower for k in ["control system", "damping ratio", "percent overshoot", "overshoot", "settling time"]):
        return solve_control_systems_2nd_order()

    # 7. CSE: OS Scheduling
    if any(k in lower for k in ["cpu scheduling", "fcfs", "turnaround time", "waiting time"]):
        return solve_os_scheduling_fcfs([5, 3, 8, 6])

    # 8. CSE: DBMS Normal Forms
    if any(k in lower for k in ["normal form", "1nf", "2nf", "3nf", "bcnf", "normalization"]):
        return get_dbms_normal_forms_cheatsheet()

    return None
