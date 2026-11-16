"""
J.A.R.V.I.S. Mechanical & Thermodynamics Engineering Engine
Provides sub-20ms offline calculations for stress/strain, beam deflection,
torque & rotational power, fluid dynamics (Reynolds, Bernoulli), and thermodynamics (Carnot, Ideal Gas).
"""

import math
import re
from typing import Optional, Dict, Any


# -----------------------------------------------------------------------------
# 1. MECHANICS OF MATERIALS: STRESS, STRAIN & YOUNG'S MODULUS
# -----------------------------------------------------------------------------

def solve_stress_strain(force: float = 50_000, area: float = 0.001, delta_l: float = 0.0005, original_l: float = 1.0) -> str:
    """Calculates normal stress (sigma), strain (epsilon), and Young's modulus (E)."""
    stress_pa = force / area if area > 0 else 0
    stress_mpa = stress_pa / 1e6
    strain = delta_l / original_l if original_l > 0 else 0
    youngs_e_pa = stress_pa / strain if strain > 0 else 0
    youngs_e_gpa = youngs_e_pa / 1e9

    return (
        f"### [CONFIRMED] Mechanics of Materials: Stress & Strain Derivation\n\n"
        f"Given Parameters:\n"
        f"- Applied Axial Force $F = {force:,.1f}\\,\\text{{N}}$ ({force/1e3:,.2f} kN)\n"
        f"- Cross-Sectional Area $A = {area:,.6f}\\,\\text{{m}}^2$ ({area * 1e6:,.1f} mm²)\n"
        f"- Gauge Length $L_0 = {original_l:.3f}\\,\\text{{m}}$\n"
        f"- Elongation $\\Delta L = {delta_l * 1e3:.3f}\\,\\text{{mm}}$ ({delta_l:,.6f} m)\n\n"
        f"#### 1. Engineering Normal Stress ($\\sigma$)\n\n"
        f"$$\\sigma = \\frac{{F}}{{A}} = \\frac{{{force:,.1f}}}{{{area:,.6f}}} = {stress_pa:,.0f}\\,\\text{{Pa}} = \\mathbf{{{stress_mpa:.2f}\\,\\text{{MPa}}}}$$\n\n"
        f"#### 2. Engineering Normal Strain ($\\varepsilon$)\n\n"
        f"$$\\varepsilon = \\frac{{\\Delta L}}{{L_0}} = \\frac{{{delta_l:,.6f}}}{{{original_l:.3f}}} = \\mathbf{{{strain:.6f}}} = \\mathbf{{{strain * 100:.4f}\\%}}$$\n\n"
        f"#### 3. Modulus of Elasticity (Young's Modulus $E$)\n\n"
        f"$$E = \\frac{{\\sigma}}{{\\varepsilon}} = \\frac{{{stress_pa:,.0f}}}{{{strain:.6f}}} = {youngs_e_pa:,.0f}\\,\\text{{Pa}} = \\mathbf{{{youngs_e_gpa:.2f}\\,\\text{{GPa}}}}$$\n\n"
        f"- **Structural Reference**: Structural Steel $\\approx 200\\,\\text{{GPa}}$, Aluminum 6061-T6 $\\approx 69\\,\\text{{GPa}}$, Titanium $\\approx 114\\,\\text{{GPa}}$."
    )


# -----------------------------------------------------------------------------
# 2. BEAM BENDING & DEFLECTION
# -----------------------------------------------------------------------------

def solve_beam_deflection(
    beam_type: str = "cantilever",
    load_n: float = 5_000,
    length_m: float = 2.0,
    e_gpa: float = 200.0,
    i_m4: float = 8.33e-6,
) -> str:
    """Calculates max deflection and maximum bending moment for cantilever and simply supported beams."""
    e_pa = e_gpa * 1e9

    if "cantilever" in beam_type.lower():
        # Cantilever with end load P: delta_max = P*L^3 / (3*E*I), M_max = P*L
        delta_max = (load_n * (length_m**3)) / (3.0 * e_pa * i_m4)
        m_max = load_n * length_m
        b_name = "Cantilever Beam (Point Load at Free End)"
        def_formula = (
            f"$$\\delta_{{max}} = \\frac{{P L^3}}{{3 E I}} = "
            f"\\frac{{{load_n:,.0f} \\cdot ({length_m})^3}}{{3 \\cdot ({e_pa:,.0e}) \\cdot ({i_m4:,.2e})}} = "
            f"\\mathbf{{{delta_max * 1e3:.3f}\\,\\text{{mm}}}}$$"
        )
        m_formula = f"$$M_{{max}} = P \\cdot L = {load_n:,.0f} \\times {length_m} = \\mathbf{{{m_max:,.1f}\\,\\text{{N}}\\cdot\\text{{m}}}}$$"
    else:
        # Simply supported with center load P: delta_max = P*L^3 / (48*E*I), M_max = P*L / 4
        delta_max = (load_n * (length_m**3)) / (48.0 * e_pa * i_m4)
        m_max = (load_n * length_m) / 4.0
        b_name = "Simply Supported Beam (Point Load at Midspan)"
        def_formula = (
            f"$$\\delta_{{max}} = \\frac{{P L^3}}{{48 E I}} = "
            f"\\frac{{{load_n:,.0f} \\cdot ({length_m})^3}}{{48 \\cdot ({e_pa:,.0e}) \\cdot ({i_m4:,.2e})}} = "
            f"\\mathbf{{{delta_max * 1e3:.3f}\\,\\text{{mm}}}}$$"
        )
        m_formula = f"$$M_{{max}} = \\frac{{P L}}{{4}} = \\frac{{{load_n:,.0f} \\times {length_m}}}{{4}} = \\mathbf{{{m_max:,.1f}\\,\\text{{N}}\\cdot\\text{{m}}}}$$"

    return (
        f"### [CONFIRMED] Beam Deflection & Stress Analysis\n\n"
        f"Beam Architecture: **{b_name}**\n\n"
        f"Parameters:\n"
        f"- Applied Load $P = {load_n:,.1f}\\,\\text{{N}}$ ({load_n/1e3:.2f} kN)\n"
        f"- Span Length $L = {length_m:.2f}\\,\\text{{m}}$\n"
        f"- Modulus of Elasticity $E = {e_gpa:.1f}\\,\\text{{GPa}}$\n"
        f"- Area Moment of Inertia $I = {i_m4:,.2e}\\,\\text{{m}}^4$ ({i_m4 * 1e8:,.1f} cm⁴)\n\n"
        f"#### 1. Maximum Deflection ($\\delta_{{max}}$)\n\n"
        f"{def_formula}\n\n"
        f"#### 2. Maximum Bending Moment ($M_{{max}}$)\n\n"
        f"{m_formula}\n\n"
        f"- **Deflection-to-Span Ratio**: $L / \\delta_{{max}} \\approx {length_m / delta_max:,.0f}$ (Industry structural limit typically $L/360$ to $L/240$)."
    )


# -----------------------------------------------------------------------------
# 3. TORQUE, SPEED & ROTATIONAL POWER
# -----------------------------------------------------------------------------

def solve_torque_power(torque_nm: Optional[float] = None, rpm: Optional[float] = None, power_kw: Optional[float] = None) -> str:
    """Calculates mechanical shaft power, torque, or RPM from P = tau * omega."""
    if torque_nm is not None and rpm is not None:
        omega = (2.0 * math.pi * rpm) / 60.0
        p_watts = torque_nm * omega
        p_kw = p_watts / 1e3
        hp = p_watts / 745.7

        return (
            f"### [CONFIRMED] Rotational Shaft Power Derivation\n\n"
            f"Given Operating Point:\n"
            f"- Torque $\\tau = {torque_nm:,.2f}\\,\\text{{N}}\\cdot\\text{{m}}$\n"
            f"- Rotational Speed $N = {rpm:,.0f}\\,\\text{{RPM}}$\n\n"
            f"#### 1. Angular Velocity ($\\omega$)\n\n"
            f"$$\\omega = \\frac{{2\\pi N}}{{60}} = \\frac{{2\\pi \\times {rpm:,.0f}}}{{60}} = \\mathbf{{{omega:.2f}\\,\\text{{rad/s}}}}$$\n\n"
            f"#### 2. Shaft Mechanical Power ($P$)\n\n"
            f"$$P = \\tau \\cdot \\omega = {torque_nm:,.2f} \\times {omega:.2f} = {p_watts:,.1f}\\,\\text{{W}} = \\mathbf{{{p_kw:.3f}\\,\\text{{kW}}}}$$\n\n"
            f"- **Imperial Horsepower**: $\\mathbf{{{hp:.2f}\\,\\text{{HP}}}}$ ($1\\,\\text{{HP}} \\approx 745.7\\,\\text{{W}}$)\n"
            f"- **Standard Metric Rule**: $P_{{\\text{{kW}}}} \\approx \\frac{{\\tau \\cdot N}}{{9549}}$"
        )
    elif power_kw is not None and rpm is not None:
        p_watts = power_kw * 1e3
        omega = (2.0 * math.pi * rpm) / 60.0
        torque_nm = p_watts / omega if omega > 0 else 0
        hp = p_watts / 745.7

        return (
            f"### [CONFIRMED] Motor Shaft Torque Derivation\n\n"
            f"Given:\n"
            f"- Power $P = {power_kw:,.2f}\\,\\text{{kW}}$ ({hp:.2f} HP)\n"
            f"- Speed $N = {rpm:,.0f}\\,\\text{{RPM}}$\n\n"
            f"$$\\tau = \\frac{{P}}{{\\omega}} = \\frac{{60 \\cdot P}}{{2\\pi N}} = \\frac{{60 \\times {p_watts:,.0f}}}{{2\\pi \\times {rpm:,.0f}}} = \\mathbf{{{torque_nm:,.2f}\\,\\text{{N}}\\cdot\\text{{m}}}}$$\n\n"
            f"- **Imperial Torque**: `{torque_nm / 1.355818:.2f} lbf·ft`"
        )
    return "Please specify Torque and RPM, or Power (kW) and RPM."


# -----------------------------------------------------------------------------
# 4. FLUID MECHANICS: REYNOLDS NUMBER & BERNOULLI
# -----------------------------------------------------------------------------

def solve_reynolds_number(velocity: float = 2.0, diameter: float = 0.05, density: float = 1000.0, viscosity: float = 0.001) -> str:
    """Calculates Reynolds Number and classifies flow regime (Laminar, Transitional, Turbulent)."""
    re = (density * velocity * diameter) / viscosity if viscosity > 0 else 0

    if re < 2300:
        regime = "Laminar Flow"
        regime_desc = "Viscous forces dominate; smooth parallel fluid streamlines with negligible mixing."
        badge = "LAMINAR (Re < 2,300)"
    elif 2300 <= re <= 4000:
        regime = "Transitional Flow"
        regime_desc = "Intermittent turbulence bursts; sensitive to pipe wall roughness and vibrations."
        badge = "TRANSITIONAL (2,300 ≤ Re ≤ 4,000)"
    else:
        regime = "Turbulent Flow"
        regime_desc = "Inertial forces dominate; chaotic eddy currents, intense radial mixing, high friction factor."
        badge = "TURBULENT (Re > 4,000)"

    kinematic_nu = viscosity / density if density > 0 else 0

    return (
        f"### [CONFIRMED] Fluid Dynamics: Reynolds Number Analysis\n\n"
        f"Flow Conditions:\n"
        f"- Fluid Velocity $v = {velocity:.3f}\\,\\text{{m/s}}$\n"
        f"- Internal Pipe Diameter $D = {diameter * 1e3:.1f}\\,\\text{{mm}}$ ({diameter:.4f} m)\n"
        f"- Fluid Density $\\rho = {density:,.1f}\\,\\text{{kg/m}}^3$\n"
        f"- Dynamic Viscosity $\\mu = {viscosity:,.6f}\\,\\text{{Pa}}\\cdot\\text{{s}}$ ({viscosity * 1e3:.2f} cP)\n"
        f"- Kinematic Viscosity $\\nu = \\mu / \\rho = {kinematic_nu:,.3e}\\,\\text{{m}}^2/\\text{{s}}$\n\n"
        f"#### 1. Governing Dimensionless Equation\n\n"
        f"$$Re = \\frac{{\\rho v D}}{{\\mu}} = \\frac{{{density:,.1f} \\cdot {velocity:.3f} \\cdot {diameter:.4f}}}{{{viscosity:,.6f}}} = \\mathbf{{{re:,.1f}}}$$\n\n"
        f"#### 2. Flow Regime Classification: **{badge}**\n\n"
        f"**{regime}**: {regime_desc}\n\n"
        f"- **Moody Friction Factor Reference**: For smooth pipes in turbulent regime, $f \\approx 0.316 \\cdot Re^{{-0.25}}$ (Blasius correlation)."
    )


def solve_bernoulli_pressure_drop(v1: float = 1.0, v2: float = 3.0, rho: float = 1000.0, delta_z: float = 0.0) -> str:
    """Calculates pressure difference delta P across two cross-sections via Bernoulli's equation."""
    g = 9.81
    dyn1 = 0.5 * rho * (v1**2)
    dyn2 = 0.5 * rho * (v2**2)
    grav_term = rho * g * delta_z
    delta_p_pa = (dyn1 - dyn2) - grav_term
    delta_p_kpa = delta_p_pa / 1e3

    return (
        f"### [CONFIRMED] Bernoulli Incompressible Fluid Flow Analysis\n\n"
        f"Flow State:\n"
        f"- Fluid Density $\\rho = {rho:,.1f}\\,\\text{{kg/m}}^3$\n"
        f"- Upstream Velocity $v_1 = {v1:.2f}\\,\\text{{m/s}}$ (Dynamic pressure: ${dyn1:.1f}\\,\\text{{Pa}}$)\n"
        f"- Downstream Velocity $v_2 = {v2:.2f}\\,\\text{{m/s}}$ (Dynamic pressure: ${dyn2:.1f}\\,\\text{{Pa}}$)\n"
        f"- Elevation Difference $\\Delta z = {delta_z:.2f}\\,\\text{{m}}$\n\n"
        f"#### 1. Incompressible Energy Conservation\n\n"
        f"$$P_1 + \\frac{{1}}{{2}}\\rho v_1^2 + \\rho g z_1 = P_2 + \\frac{{1}}{{2}}\\rho v_2^2 + \\rho g z_2$$\n\n"
        f"#### 2. Differential Pressure ($\\Delta P = P_1 - P_2$)\n\n"
        f"$$\\Delta P = \\frac{{1}}{{2}}\\rho (v_2^2 - v_1^2) + \\rho g \\Delta z$$\n"
        f"$$\\Delta P = \\frac{{1}}{{2}}({rho:,.1f})({v2:.2f}^2 - {v1:.2f}^2) + ({rho:,.1f})(9.81)({delta_z:.2f}) = {delta_p_pa:,.0f}\\,\\text{{Pa}} = \\mathbf{{{delta_p_kpa:.3f}\\,\\text{{kPa}}}}$$\n\n"
        f"> **Venturi Effect**: As fluid accelerates from $v_1$ to $v_2$, static pressure decreases correspondingly."
    )


# -----------------------------------------------------------------------------
# 5. THERMODYNAMICS: CARNOT CYCLE & IDEAL GAS
# -----------------------------------------------------------------------------

def solve_carnot_efficiency(th_val: float = 500.0, tc_val: float = 30.0, is_celsius: bool = True) -> str:
    """Calculates maximum theoretical thermal efficiency of a Carnot heat engine."""
    if is_celsius:
        th_k = th_val + 273.15
        tc_k = tc_val + 273.15
    else:
        th_k = th_val
        tc_k = tc_val

    if th_k <= tc_k or th_k <= 0:
        return "Hot reservoir temperature $T_H$ must be strictly greater than cold reservoir $T_C$ and above absolute zero."

    eta_carnot = 1.0 - (tc_k / th_k)
    cop_refrig = tc_k / (th_k - tc_k)
    cop_heatpump = th_k / (th_k - tc_k)

    return (
        f"### [CONFIRMED] Carnot Cycle Thermodynamic Efficiency\n\n"
        f"Reservoir Temperatures:\n"
        f"- Hot Source $T_H = {th_val:,.1f}\\,{('^\\circ\\text{C}' if is_celsius else '\\text{K}')}$ $\\implies \\mathbf{{{th_k:,.2f}\\,\\text{{K}}}}$\n"
        f"- Cold Sink $T_C = {tc_val:,.1f}\\,{('^\\circ\\text{C}' if is_celsius else '\\text{K}')}$ $\\implies \\mathbf{{{tc_k:,.2f}\\,\\text{{K}}}}$\n\n"
        f"#### 1. Second Law Maximum Thermal Efficiency ($\\eta_{{\\text{{Carnot}}}}$)\n\n"
        f"$$\\eta_{{\\text{{Carnot}}}} = 1 - \\frac{{T_C}}{{T_H}} = 1 - \\frac{{{tc_k:,.2f}}}{{{th_k:,.2f}}} = \\mathbf{{{eta_carnot * 100:.2f}\\%}}$$\n\n"
        f"#### 2. Reverse Cycle Coefficients of Performance (COP)\n\n"
        f"- **Refrigeration COP**: $\\text{{COP}}_{{R}} = \\frac{{T_C}}{{T_H - T_C}} = \\frac{{{tc_k:,.2f}}}{{{th_k - tc_k:,.2f}}} = \\mathbf{{{cop_refrig:.2f}}}$\n"
        f"- **Heat Pump COP**: $\\text{{COP}}_{{HP}} = \\frac{{T_H}}{{T_H - T_C}} = \\mathbf{{{cop_heatpump:.2f}}}$ ($1 + \\text{{COP}}_R$)\n\n"
        f"> **Carnot Principle**: No actual heat engine operating between these two thermal reservoirs can exceed {eta_carnot * 100:.2f}% efficiency."
    )


def solve_ideal_gas(p_kpa: Optional[float] = 101.325, v_m3: Optional[float] = 0.024, t_c: Optional[float] = 20.0, n_moles: Optional[float] = None) -> str:
    """Calculates state variables using Ideal Gas Law P*V = n*R*T."""
    r_const = 8.314462  # J / (mol * K)
    t_k = (t_c + 273.15) if t_c is not None else 293.15

    if n_moles is None and p_kpa is not None and v_m3 is not None:
        p_pa = p_kpa * 1e3
        n_calc = (p_pa * v_m3) / (r_const * t_k)
        return (
            f"### [CONFIRMED] Ideal Gas Equation of State ($PV = nRT$)\n\n"
            f"Parameters:\n"
            f"- Pressure $P = {p_kpa:,.2f}\\,\\text{{kPa}}$ ({p_pa:,.0f} Pa)\n"
            f"- Volume $V = {v_m3:,.4f}\\,\\text{{m}}^3$ ({v_m3 * 1e3:.1f} Liters)\n"
            f"- Temperature $T = {t_c:.1f}^\\circ\\text{{C}} = {t_k:.2f}\\,\\text{{K}}$\n"
            f"- Universal Gas Constant $R = 8.3145\\,\\text{{J/(mol}}\\cdot\\text{{K)}}$\n\n"
            f"#### Calculated Substance Quantity ($n$)\n\n"
            f"$$n = \\frac{{P V}}{{R T}} = \\frac{{{p_pa:,.0f} \\times {v_m3:,.4f}}}{{8.3145 \\times {t_k:.2f}}} = \\mathbf{{{n_calc:.4f}\\,\\text{{moles}}}}$$\n\n"
            f"- For Dry Air (Molar mass $M \\approx 28.97\\,\\text{{g/mol}}$): Mass $m \\approx {n_calc * 28.97:.2f}\\,\\text{{g}}$."
        )
    return "Please provide Pressure, Volume, and Temperature to solve for molar quantity."


# -----------------------------------------------------------------------------
# 6. DISPATCHER & INTENT PARSER
# -----------------------------------------------------------------------------

def evaluate_mech_thermo(query: str) -> Optional[str]:
    """
    Main offline evaluator for mechanical, civil, and thermodynamic engineering.
    Returns formatted KaTeX markdown or None if the query does not match.
    """
    q = query.strip()
    lower = q.lower()

    # 1. Stress & Strain
    if any(k in lower for k in ["stress", "strain", "young's modulus", "youngs modulus", "elastic modulus"]):
        f_val = 50_000.0
        a_val = 0.001
        dl_val = 0.0005
        l0_val = 1.0

        mf = re.search(r"f(?:orce)?\s*=\s*(\d+(?:\.\d+)?)\s*(kn|n)?", q, re.IGNORECASE)
        if mf:
            f_val = float(mf.group(1)) * (1e3 if (mf.group(2) or "").lower() == "kn" else 1.0)
        ma = re.search(r"a(?:rea)?\s*=\s*(\d+(?:\.\d+)?)\s*(m2|mm2|m\^2|mm\^2)?", q, re.IGNORECASE)
        if ma:
            unit = (ma.group(2) or "").lower()
            a_val = float(ma.group(1)) * (1e-6 if "mm" in unit else 1.0)
        return solve_stress_strain(force=f_val, area=a_val, delta_l=dl_val, original_l=l0_val)

    # 2. Beam Deflection
    if any(k in lower for k in ["beam deflection", "beam bending", "cantilever", "simply supported beam"]):
        b_type = "cantilever" if "cantilever" in lower else "simply supported"
        p_load = 5_000.0
        l_span = 2.0
        e_mod = 200.0
        i_inertia = 8.33e-6

        mp = re.search(r"p\s*=\s*(\d+(?:\.\d+)?)\s*(kn|n)?", q, re.IGNORECASE)
        if mp:
            p_load = float(mp.group(1)) * (1e3 if (mp.group(2) or "").lower() == "kn" else 1.0)
        ml = re.search(r"l(?:ength)?\s*=\s*(\d+(?:\.\d+)?)\s*m?", q, re.IGNORECASE)
        if ml:
            l_span = float(ml.group(1))
        return solve_beam_deflection(beam_type=b_type, load_n=p_load, length_m=l_span, e_gpa=e_mod, i_m4=i_inertia)

    # 3. Torque & Power
    if any(k in lower for k in ["torque", "shaft power", "rotational power", "rpm"]) and not any(k in lower for k in ["convert"]):
        m_rpm = re.search(r"(\d+(?:\.\d+)?)\s*rpm", q, re.IGNORECASE)
        m_tau = re.search(r"(\d+(?:\.\d+)?)\s*(?:nm|n\*m|n-m)", q, re.IGNORECASE)
        m_kw = re.search(r"(\d+(?:\.\d+)?)\s*kw", q, re.IGNORECASE)

        rpm_val = float(m_rpm.group(1)) if m_rpm else 1500.0
        if m_tau:
            tau_val = float(m_tau.group(1))
            return solve_torque_power(torque_nm=tau_val, rpm=rpm_val)
        elif m_kw:
            kw_val = float(m_kw.group(1))
            return solve_torque_power(rpm=rpm_val, power_kw=kw_val)
        elif "torque" in lower or "power" in lower:
            return solve_torque_power(torque_nm=50.0, rpm=rpm_val)

    # 4. Reynolds Number
    if any(k in lower for k in ["reynolds", "reynold", "laminar flow", "turbulent flow", "pipe flow"]):
        v_flow = 2.0
        d_pipe = 0.05
        rho_fluid = 1000.0
        mu_visc = 0.001

        mv = re.search(r"v\s*=\s*(\d+(?:\.\d+)?)", q, re.IGNORECASE)
        if mv:
            v_flow = float(mv.group(1))
        md = re.search(r"d\s*=\s*(\d+(?:\.\d+)?)", q, re.IGNORECASE)
        if md:
            d_pipe = float(md.group(1))
        return solve_reynolds_number(velocity=v_flow, diameter=d_pipe, density=rho_fluid, viscosity=mu_visc)

    # 5. Bernoulli Pressure Drop
    if any(k in lower for k in ["bernoulli", "venturi", "pressure drop", "dynamic pressure"]):
        v1_val = 1.0
        v2_val = 3.0
        mv1 = re.search(r"v1\s*=\s*(\d+(?:\.\d+)?)", q, re.IGNORECASE)
        if mv1:
            v1_val = float(mv1.group(1))
        mv2 = re.search(r"v2\s*=\s*(\d+(?:\.\d+)?)", q, re.IGNORECASE)
        if mv2:
            v2_val = float(mv2.group(1))
        return solve_bernoulli_pressure_drop(v1=v1_val, v2=v2_val)

    # 6. Carnot Efficiency
    if any(k in lower for k in ["carnot", "heat engine", "thermal efficiency"]):
        th = 500.0
        tc = 50.0
        is_c = True
        mth = re.search(r"t[h|1]\s*=\s*(\d+(?:\.\d+)?)\s*([ck])?", q, re.IGNORECASE)
        if mth:
            th = float(mth.group(1))
            if (mth.group(2) or "").lower() == "k":
                is_c = False
        mtc = re.search(r"t[c|2]\s*=\s*(\d+(?:\.\d+)?)\s*([ck])?", q, re.IGNORECASE)
        if mtc:
            tc = float(mtc.group(1))
        return solve_carnot_efficiency(th_val=th, tc_val=tc, is_celsius=is_c)

    # 7. Ideal Gas Law
    if any(k in lower for k in ["ideal gas", "pv=nrt", "gas law"]):
        p = 101.325
        v = 0.024
        t = 20.0
        mp = re.search(r"p\s*=\s*(\d+(?:\.\d+)?)", q, re.IGNORECASE)
        if mp:
            p = float(mp.group(1))
        mv = re.search(r"v\s*=\s*(\d+(?:\.\d+)?)", q, re.IGNORECASE)
        if mv:
            v = float(mv.group(1))
        return solve_ideal_gas(p_kpa=p, v_m3=v, t_c=t)

    return None
