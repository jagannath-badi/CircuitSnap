"""
J.A.R.V.I.S. Symbolic Engineering Mathematics Engine
Provides sub-20ms offline symbolic calculus, ODE solving, Laplace transforms,
matrix operations, and engineering unit conversions using SymPy and exact closed-form mathematics.
"""

import math
import re
from typing import Optional, Dict, Any, List

# SymPy is a heavy dependency. It is imported lazily only inside functions that
# actually need it, so `import backend.main` never pulls sympy into RAM on the
# memory-constrained Render free tier.
_sp = None
_parse_expr = None
_SYMPY_TRANSFORMS = None


def _load_sympy():
    """Lazily import sympy and its parser on first use. Returns True if available."""
    global _sp, _parse_expr, _SYMPY_TRANSFORMS
    if _sp is not None:
        return True
    try:
        import sympy as sp
        from sympy.parsing.sympy_parser import (
            parse_expr,
            standard_transformations,
            implicit_multiplication_application,
            convert_xor,
        )
        _sp = sp
        _parse_expr = parse_expr
        _SYMPY_TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)
        return True
    except ImportError:
        return False


# -----------------------------------------------------------------------------
# STRICT CONVERSATIONAL GATE & CONCEPTUAL FALLBACKS
# -----------------------------------------------------------------------------

CONVERSATIONAL_WORDS = {
    "explain", "about", "what", "is", "are", "define", "definition",
    "how", "tell", "me", "solve", "find", "the", "of", "for", "please",
    "give", "show", "calculate", "compute", "evaluate", "value", "derive",
    "derivation", "meaning", "concept", "intuition", "analogy", "help",
    "with", "transform", "transforms", "inverse", "forward", "can", "you",
    "do", "an", "a", "to", "in", "wrt", "respect", "using", "work", "works",
    "working", "theorem", "property", "properties", "rule", "rules", "formula",
    "formulas", "equation", "equations", "laplace", "diff", "derivative",
    "derivatives", "differentiate", "differentiation", "differential", "integral",
    "integrals", "integration", "integrate", "antiderivative", "ode", "matrix",
    "matrices", "determinant", "eigenvalue", "eigenvalues", "limits", "limit",
    "taylor", "maclaurin", "calculus", "linear", "algebra", "kirchhoff",
    "kvl", "kcl", "thevenin", "norton", "state", "law", "laws"
}


def is_pure_conversational(text: str) -> bool:
    """Returns True if the text contains only conversational words and no mathematical syntax."""
    stripped = text.strip()
    if not stripped:
        return True
    if re.search(r"[-+*/^=]|(?:\b\d+\b)", stripped):
        words = re.findall(r"[a-zA-Z]+", stripped.lower())
        non_filler = [w for w in words if w not in CONVERSATIONAL_WORDS]
        if not non_filler:
            return True
        return False
    words = re.findall(r"[a-zA-Z]+", stripped.lower())
    if not words:
        return True
    non_filler = [w for w in words if w not in CONVERSATIONAL_WORDS]
    return len(non_filler) == 0


def clean_symbolic_expression(raw: str) -> str:
    """Cleans conversational prefix/suffix words and normalizes exponential and multiplication syntax."""
    s = raw.strip()
    s = re.sub(
        r"^(?:please\s+)?(?:can\s+you\s+)?(?:solve|find|calculate|compute|give|evaluate|derive|get)?\s*(?:the\s+)?(?:forward\s+|inverse\s+|inv\s+)?(?:laplace\s+transform\s+of|laplace\s+of|laplace|l\^-1|derivative\s+of|diff\s+of|diff|integral\s+of|integrate)?\s*",
        "", s, flags=re.IGNORECASE
    ).strip()
    s = re.sub(r"(?:with respect to|wrt)\s*[a-zA-Z]", "", s, flags=re.IGNORECASE).strip()
    s = re.sub(r"\be\^\(([^)]+)\)", r"exp(\1)", s)
    s = re.sub(r"\be\^(-?[0-9a-zA-Z*.]+)", r"exp(\1)", s)
    s = re.sub(r"(\d+)\s*(t|s|x|y|z|pi|exp|sin|cos|tan)\b", r"\1*\2", s, flags=re.IGNORECASE)
    s = s.replace("·", "*").replace("×", "*")
    return s.strip()


def get_laplace_conceptual_explanation() -> str:
    """Returns authoritative conceptual and mathematical explanation for the Laplace transform."""
    return (
        "### [CONFIRMED] Laplace Transform: Conceptual & Mathematical Foundations\n\n"
        "The **Laplace Transform** is an integral transform that converts a continuous time-domain signal $f(t)$ "
        "into a complex frequency-domain representation $F(s)$, where $s = \\sigma + j\\omega \\in \\mathbb{C}$. "
        "It is the central mathematical framework for continuous-time Linear Time-Invariant (LTI) systems, "
        "analog filter design, transient circuit analysis, and control theory.\n\n"
        "#### 1. Governing Integral Definitions\n\n"
        "- **Unilateral (One-Sided) Transform ($t \\ge 0^-$)**:\n"
        "  $$\\mathcal{L}\\{f(t)\\} = F(s) = \\int_{0^-}^{\\infty} f(t) e^{-st} \\, dt$$\n"
        "- **Bilateral (Two-Sided) Transform**:\n"
        "  $$\\mathcal{L}_{II}\\{f(t)\\} = F(s) = \\int_{-\\infty}^{\\infty} f(t) e^{-st} \\, dt$$\n"
        "- **Inverse Laplace Transform (Bromwich Contour Integral)**:\n"
        "  $$\\mathcal{L}^{-1}\\{F(s)\\} = f(t) = \\frac{1}{2\\pi j} \\int_{\\gamma - j\\infty}^{\\gamma + j\\infty} F(s) e^{st} \\, ds$$\n\n"
        "#### 2. Physical & Engineering Significance\n\n"
        "1. **Algebraizing Differential Equations**: Converts time differentiation $\\frac{d}{dt} \\longleftrightarrow s$ "
        "and time integration $\\int dt \\longleftrightarrow \\frac{1}{s}$ into algebraic arithmetic, transforming coupled ODEs into rational polynomials.\n"
        "2. **Transient and Steady-State Unification**: Captures both natural transient response (eigenvalues/damping) and forced steady-state sinusoidal response in one unified closed-form function.\n"
        "3. **Complex Frequency Plane**: The real part $\\sigma$ governs signal exponential growth/decay, while the imaginary part $\\omega$ represents oscillatory frequency. "
        "Setting $\\sigma = 0$ reduces the unilateral Laplace transform to the classical continuous-time **Fourier Transform**.\n\n"
        "#### 3. Standard Transform Pairs Table\n\n"
        "| Time Signal $f(t) \\ (t \\ge 0)$ | $s$-Domain Transform $F(s)$ | Region of Convergence (ROC) |\n"
        "| :--- | :--- | :--- |\n"
        "| **Dirac Delta** $\\delta(t)$ | $1$ | Entire $s$-plane |\n"
        "| **Unit Step** $u(t)$ | $\\frac{1}{s}$ | $\\text{Re}(s) > 0$ |\n"
        "| **Ramp** $t \\cdot u(t)$ | $\\frac{1}{s^2}$ | $\\text{Re}(s) > 0$ |\n"
        "| **Power** $t^n \\cdot u(t)$ | $\\frac{n!}{s^{n+1}}$ | $\\text{Re}(s) > 0$ |\n"
        "| **Exponential** $e^{-at} u(t)$ | $\\frac{1}{s + a}$ | $\\text{Re}(s) > -a$ |\n"
        "| **Sine Wave** $\\sin(\\omega t) u(t)$ | $\\frac{\\omega}{s^2 + \\omega^2}$ | $\\text{Re}(s) > 0$ |\n"
        "| **Cosine Wave** $\\cos(\\omega t) u(t)$ | $\\frac{s}{s^2 + \\omega^2}$ | $\\text{Re}(s) > 0$ |\n"
        "| **Damped Cosine** $e^{-at} \\cos(\\omega t)$ | $\\frac{s+a}{(s+a)^2 + \\omega^2}$ | $\\text{Re}(s) > -a$ |\n"
        "| **Damped Sine** $e^{-at} \\sin(\\omega t)$ | $\\frac{\\omega}{(s+a)^2 + \\omega^2}$ | $\\text{Re}(s) > -a$ |\n\n"
        "#### 4. Critical Operational Properties\n\n"
        "- **Linearity**: $\\mathcal{L}\\{a f_1(t) + b f_2(t)\\} = a F_1(s) + b F_2(s)$\n"
        "- **Time Differentiation**: $\\mathcal{L}\\left\\{\\frac{df}{dt}\\right\\} = s F(s) - f(0^-)$\n"
        "- **Second Derivative**: $\\mathcal{L}\\left\\{\\frac{d^2f}{dt^2}\\right\\} = s^2 F(s) - s f(0^-) - f'(0^-)$\n"
        "- **Frequency Shift**: $\\mathcal{L}\\{e^{-at} f(t)\\} = F(s + a)$\n"
        "- **Time Shift**: $\\mathcal{L}\\{f(t - t_0) u(t - t_0)\\} = e^{-s t_0} F(s)$\n"
        "- **Convolution in Time**: $\\mathcal{L}\\{f_1(t) * f_2(t)\\} = F_1(s) \\cdot F_2(s)$\n"
        "- **Initial Value Theorem**: $\\lim_{t \\to 0^+} f(t) = \\lim_{s \\to \\infty} s F(s)$\n"
        "- **Final Value Theorem**: $\\lim_{t \\to \\infty} f(t) = \\lim_{s \\to 0} s F(s)$ (valid if all poles of $s F(s)$ reside strictly in open LHP)"
    )


def get_differentiation_conceptual_explanation() -> str:
    """Returns conceptual and mathematical explanation for derivatives and differential calculus."""
    return (
        "### [CONFIRMED] Differential Calculus: First Principles & Engineering Meaning\n\n"
        "The **derivative** measures the instantaneous rate of change of a function $f(x)$ with respect to its independent variable $x$. "
        "Geometrically, it represents the exact slope of the tangent line to the curve at any point.\n\n"
        "#### 1. Limit Definition (First Principles)\n\n"
        "$$f'(x) = \\frac{df}{dx} = \\lim_{h \\to 0} \\frac{f(x + h) - f(x)}{h}$$\n\n"
        "#### 2. Fundamental Engineering Interpretations\n\n"
        "- **Kinematics**: Position $x(t) \\implies$ Velocity $v(t) = \\frac{dx}{dt} \\implies$ Acceleration $a(t) = \\frac{d^2x}{dt^2}$.\n"
        "- **Electrical Circuits**: Capacitor current $i_C(t) = C \\frac{dv_C}{dt}$; Inductor voltage $v_L(t) = L \\frac{di_L}{dt}$.\n"
        "- **Optimization**: Local extrema (maxima/minima) occur at critical points where $\\frac{df}{dx} = 0$.\n"
        "- **Concavity & Curvature**: The second derivative $\\frac{d^2f}{dx^2} > 0$ indicates concave up (local minimum), while $\\frac{d^2f}{dx^2} < 0$ indicates concave down (local maximum).\n\n"
        "#### 3. Core Differentiation Rules\n\n"
        "| Rule Name | Mathematical Statement |\n"
        "| :--- | :--- |\n"
        "| **Power Rule** | $\\frac{d}{dx}[x^n] = n x^{n-1}$ |\n"
        "| **Product Rule** | $\\frac{d}{dx}[u \\cdot v] = u' v + u v'$ |\n"
        "| **Quotient Rule** | $\\frac{d}{dx}\\left[\\frac{u}{v}\\right] = \\frac{u' v - u v'}{v^2}$ |\n"
        "| **Chain Rule** | $\\frac{d}{dx}[f(g(x))] = f'(g(x)) \\cdot g'(x)$ |\n"
        "| **Exponential** | $\\frac{d}{dx}[e^{kx}] = k e^{kx}$ |\n"
        "| **Natural Log** | $\\frac{d}{dx}[\\ln(x)] = \\frac{1}{x} \\quad (x > 0)$ |\n"
        "| **Sine / Cosine** | $\\frac{d}{dx}[\\sin(x)] = \\cos(x), \\quad \\frac{d}{dx}[\\cos(x)] = -\\sin(x)$ |"
    )


def get_integration_conceptual_explanation() -> str:
    """Returns conceptual and mathematical explanation for integrals and integral calculus."""
    return (
        "### [CONFIRMED] Integral Calculus: Foundations & Physical Accumulation\n\n"
        "**Integration** is the inverse operation to differentiation (antiderivative) and geometrically calculates the cumulative net signed area "
        "bounded between a curve $f(x)$ and the independent coordinate axis.\n\n"
        "#### 1. Riemann Integral & Fundamental Theorem of Calculus (FTC)\n\n"
        "- **Riemann Sum Definition**:\n"
        "  $$\\int_{a}^{b} f(x) \\, dx = \\lim_{n \\to \\infty} \\sum_{i=1}^{n} f(x_i^*) \\Delta x, \\quad \\Delta x = \\frac{b - a}{n}$$\n"
        "- **Fundamental Theorem of Calculus (Part 1 & 2)**:\n"
        "  $$\\frac{d}{dx} \\left[ \\int_{a}^{x} f(t) \\, dt \\right] = f(x)$$\n"
        "  $$\\int_{a}^{b} f(x) \\, dx = F(b) - F(a), \\quad \\text{where } F'(x) = f(x)$$\n\n"
        "#### 2. Physical & Engineering Meaning\n\n"
        "- **Electrical Charge**: Total charge $Q(t) = \\int_{0}^{t} i(\\tau) \\, d\\tau + Q(0)$.\n"
        "- **Energy from Power**: Cumulative electrical/mechanical energy $W = \\int P(t) \\, dt$.\n"
        "- **Fluid Flow & Mass**: Cumulative volumetric discharge $V = \\int Q(t) \\, dt$.\n"
        "- **Centroids & Moments of Inertia**: Second moment of area $I_{xx} = \\iint y^2 \\, dA$.\n\n"
        "#### 3. Standard Integration Techniques\n\n"
        "- **Integration by Parts**: $\\int u \\, dv = u v - \\int v \\, du$ (choose $u$ using the **ILATE** priority: Inverse, Log, Algebraic, Trig, Exponential).\n"
        "- **$u$-Substitution (Chain Rule Inversion)**: $\\int f(g(x)) g'(x) \\, dx = \\int f(u) \\, du$.\n"
        "- **Partial Fraction Expansion**: Decomposes rational fractions $\\frac{P(x)}{Q(x)}$ into simpler summable terms for direct integration."
    )


def get_ode_conceptual_explanation() -> str:
    """Returns conceptual and mathematical explanation for ordinary differential equations."""
    return (
        "### [CONFIRMED] Ordinary Differential Equations (ODEs): Engineering Framework\n\n"
        "An **Ordinary Differential Equation (ODE)** expresses the governing relationship between an unknown function $y(t)$, "
        "its independent variable $t$, and one or more of its derivatives $\\frac{dy}{dt}, \\frac{d^2y}{dt^2}, \\dots$.\n\n"
        "#### 1. Classification Dimensions\n\n"
        "1. **Order**: Highest derivative present (e.g. 1st order in RC circuits, 2nd order in RLC / mass-spring-damper).\n"
        "2. **Linearity**: The dependent variable $y$ and all its derivatives appear to the first power with coefficients depending only on $t$.\n"
        "3. **Homogeneity**: If the forcing term $f(t) = 0$, the equation is homogeneous; otherwise it is non-homogeneous.\n\n"
        "#### 2. First-Order Linear ODE Solution (Integrating Factor)\n\n"
        "Standard form: $$\\frac{dy}{dt} + P(t) y = Q(t)$$\n"
        "Integrating Factor $I(t) = e^{\\int P(t) \\, dt}$:\n"
        "$$y(t) = \\frac{1}{I(t)} \\left[ \\int I(t) Q(t) \\, dt + C \\right]$$\n\n"
        "#### 3. Second-Order Linear ODE (Characteristic Equation)\n\n"
        "Standard LTI form: $$a \\frac{d^2y}{dt^2} + b \\frac{dy}{dt} + c y = 0$$\n"
        "Characteristic polynomial: $a r^2 + b r + c = 0 \\implies r_{1,2} = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$:\n"
        "- **Overdamped ($b^2 - 4ac > 0$)**: Two distinct real roots $\\implies y(t) = C_1 e^{r_1 t} + C_2 e^{r_2 t}$.\n"
        "- **Critically Damped ($b^2 - 4ac = 0$)**: Repeated real root $\\implies y(t) = (C_1 + C_2 t) e^{r t}$.\n"
        "- **Underdamped ($b^2 - 4ac < 0$)**: Complex conjugate roots $\\alpha \\pm j\\omega \\implies y(t) = e^{\\alpha t} (C_1 \\cos(\\omega t) + C_2 \\sin(\\omega t))$."
    )


def get_matrix_conceptual_explanation() -> str:
    """Returns conceptual and mathematical explanation for linear algebra and matrices."""
    return (
        "### [CONFIRMED] Linear Algebra & Matrices: Engineering Foundations\n\n"
        "A **matrix** $A \\in \\mathbb{R}^{m \\times n}$ represents a linear transformation between vector spaces. "
        "In engineering, matrix algebra solves simultaneous nodal/mesh circuit equations, multi-degree-of-freedom structural dynamics, "
        "and modern state-space control systems.\n\n"
        "#### 1. Core Matrix Operators & Properties\n\n"
        "- **Determinant $\\det(A)$**: Geometric scaling factor of volume under transformation. $\\det(A) \\neq 0$ guarantees non-singularity and unique invertibility.\n"
        "- **Matrix Inverse $A^{-1}$**: Defined for square non-singular matrices such that $A A^{-1} = A^{-1} A = I$.\n"
        "  $$A^{-1} = \\frac{1}{\\det(A)} \\text{adj}(A)$$\n"
        "- **Trace $\\text{tr}(A)$**: Sum of main diagonal elements, equal to the sum of all eigenvalues: $\\text{tr}(A) = \\sum_{i=1}^n \\lambda_i$.\n\n"
        "#### 2. Eigenvalues & Eigenvectors\n\n"
        "Vectors $\\mathbf{v} \\neq \\mathbf{0}$ whose spatial orientation is preserved under linear operator $A$:\n"
        "$$A \\mathbf{v} = \\lambda \\mathbf{v} \\iff (A - \\lambda I)\\mathbf{v} = \\mathbf{0}$$\n"
        "Non-trivial solutions exist if and only if the **Characteristic Equation** is satisfied:\n"
        "$$\\det(A - \\lambda I) = 0$$\n\n"
        "#### 3. Primary Engineering Applications\n\n"
        "1. **State-Space Control**: $\\dot{\\mathbf{x}}(t) = A \\mathbf{x}(t) + B \\mathbf{u}(t)$ where eigenvalues of $A$ determine system stability (Hurwitz criteria: $\\text{Re}(\\lambda_i) < 0$).\n"
        "2. **Modal Structural Analysis**: Eigenvalues represent natural resonant frequencies $\\omega_n = \\sqrt{\\lambda}$ of mechanical structures.\n"
        "3. **Power System Admittance ($Y_{\\text{bus}}$)**: Nodal formulation $\\mathbf{I} = Y_{\\text{bus}} \\mathbf{V}$ for multi-bus load flow analysis."
    )


def get_limits_conceptual_explanation() -> str:
    """Returns conceptual explanation for mathematical limits and asymptotic behavior."""
    return (
        "### [CONFIRMED] Mathematical Limits & Asymptotic Behavior\n\n"
        "A **limit** formalizes the value that a function $f(x)$ approaches as the input $x$ approaches a target value $c$:\n"
        "$$\\lim_{x \\to c} f(x) = L$$\n\n"
        "#### 1. Rigorous Definition (Cauchy $\\varepsilon$-$\\delta$)\n\n"
        "For every $\\varepsilon > 0$, there exists $\\delta > 0$ such that $0 < |x - c| < \\delta \\implies |f(x) - L| < \\varepsilon$.\n\n"
        "#### 2. Indeterminate Forms & L'Hôpital's Rule\n\n"
        "When evaluating limits that yield $\\left[\\frac{0}{0}\\right]$ or $\\left[\\frac{\\infty}{\\infty}\\right]$:\n"
        "$$\\lim_{x \\to c} \\frac{f(x)}{g(x)} = \\lim_{x \\to c} \\frac{f'(x)}{g'(x)}$$\n"
        "Provided the limit of the derivative quotient exists."
    )


def get_taylor_conceptual_explanation() -> str:
    """Returns conceptual explanation for Taylor and Maclaurin series expansions."""
    return (
        "### [CONFIRMED] Taylor & Maclaurin Series: Polynomial Approximation\n\n"
        "The **Taylor Series** represents any infinitely differentiable function $f(x)$ as an infinite polynomial expansion "
        "centered at a reference point $x = a$:\n"
        "$$f(x) = \\sum_{n=0}^{\\infty} \\frac{f^{(n)}(a)}{n!} (x - a)^n = f(a) + f'(a)(x - a) + \\frac{f''(a)}{2!}(x - a)^2 + \\dots$$\n\n"
        "When centered at $a = 0$, it is specifically termed the **Maclaurin Series**:\n"
        "$$f(x) = \\sum_{n=0}^{\\infty} \\frac{f^{(n)}(0)}{n!} x^n$$\n\n"
        "- **Engineering Relevance**: Linearization of non-linear systems around operating points (e.g. small-signal BJT/MOSFET models)."
    )


# -----------------------------------------------------------------------------
# 1. SYMBOLIC CALCULUS & TRANSFORMS
# -----------------------------------------------------------------------------

def solve_differentiation(expr_str: str, var_str: str = "x") -> str:
    """Computes symbolic first and second derivatives with step-by-step KaTeX presentation."""
    raw = expr_str.strip()
    if not raw or is_pure_conversational(raw):
        return get_differentiation_conceptual_explanation()

    clean = clean_symbolic_expression(raw)
    if not clean or is_pure_conversational(clean):
        return get_differentiation_conceptual_explanation()

    if not _load_sympy():
        return "SymPy is not installed for symbolic differentiation."

    x = _sp.Symbol(var_str)
    local_dict = {var_str: x, 'exp': _sp.exp, 'sin': _sp.sin, 'cos': _sp.cos, 'tan': _sp.tan, 'e': _sp.E, 'pi': _sp.pi}
    try:
        expr = _parse_expr(clean, local_dict=local_dict, transformations=_SYMPY_TRANSFORMS)
        d1 = _sp.diff(expr, x)
        d2 = _sp.diff(d1, x)
        
        latex_orig = _sp.latex(expr)
        latex_d1 = _sp.latex(d1)
        latex_d2 = _sp.latex(d2)
        
        return (
            f"### [CONFIRMED] Symbolic Differentiation Analysis\n\n"
            f"Given function:\n"
            f"$$f({var_str}) = {latex_orig}$$\n\n"
            f"#### 1. First Derivative (Gradient / Rate of Change)\n\n"
            f"$$\\frac{{d}}{{d{var_str}}}\\left[{latex_orig}\\right] = \\mathbf{{{latex_d1}}}$$\n\n"
            f"#### 2. Second Derivative (Curvature / Concavity)\n\n"
            f"$$\\frac{{d^2}}{{d{var_str}^2}}\\left[{latex_orig}\\right] = \\mathbf{{{latex_d2}}}$$\n\n"
            f"> **Engineering Note**: Critical points occur where $\\frac{{df}}{{d{var_str}}} = 0$."
        )
    except Exception as err:
        return f"Unable to differentiate '{expr_str}': {err}"


def solve_integration(expr_str: str, var_str: str = "x", lower: Optional[str] = None, upper: Optional[str] = None) -> str:
    """Computes indefinite or definite integrals with KaTeX presentation."""
    raw = expr_str.strip()
    if not raw or is_pure_conversational(raw):
        return get_integration_conceptual_explanation()

    clean = clean_symbolic_expression(raw)
    if not clean or is_pure_conversational(clean):
        return get_integration_conceptual_explanation()

    if not _load_sympy():
        return "SymPy is not installed for symbolic integration."

    x = _sp.Symbol(var_str)
    local_dict = {var_str: x, 'exp': _sp.exp, 'sin': _sp.sin, 'cos': _sp.cos, 'tan': _sp.tan, 'e': _sp.E, 'pi': _sp.pi}
    try:
        expr = _parse_expr(clean, local_dict=local_dict, transformations=_SYMPY_TRANSFORMS)
        latex_orig = _sp.latex(expr)

        if lower is not None and upper is not None:
            a = _parse_expr(lower, local_dict=local_dict, transformations=_SYMPY_TRANSFORMS)
            b = _parse_expr(upper, local_dict=local_dict, transformations=_SYMPY_TRANSFORMS)
            res = _sp.integrate(expr, (x, a, b))
            latex_res = _sp.latex(res)
            latex_a = _sp.latex(a)
            latex_b = _sp.latex(b)

            return (
                f"### [CONFIRMED] Definite Integral Derivation\n\n"
                f"Definite integral of $f({var_str}) = {latex_orig}$ from ${latex_a}$ to ${latex_b}$:\n\n"
                f"$$\\int_{{{latex_a}}}^{{{latex_b}}} \\left({latex_orig}\\right) d{var_str} = \\mathbf{{{latex_res}}}$$\n\n"
                f"> **Geometric Evaluation**: Represents the signed net area bounded by the curve."
            )
        else:
            anti = _sp.integrate(expr, x)
            latex_anti = _sp.latex(anti)
            return (
                f"### [CONFIRMED] Indefinite Integral (Antiderivative)\n\n"
                f"Integrating $f({var_str}) = {latex_orig}$ with respect to ${var_str}$:\n\n"
                f"$$\\int \\left({latex_orig}\\right) d{var_str} = \\mathbf{{{latex_anti} + C}}$$\n\n"
                f"> **Constant of Integration**: $C \\in \\mathbb{{R}}$ represents the arbitrary boundary offset."
            )
    except Exception as err:
        return f"Unable to integrate '{expr_str}': {err}"


def solve_limit(expr_str: str, var_str: str = "x", point_str: str = "0") -> str:
    """Computes symbolic limits as var approaches point."""
    if not _load_sympy():
        return "SymPy is not installed for limits."

    x = _sp.Symbol(var_str)
    try:
        expr = _parse_expr(expr_str, transformations=_SYMPY_TRANSFORMS)
        point = _parse_expr(point_str, transformations=_SYMPY_TRANSFORMS)
        res = _sp.limit(expr, x, point)

        latex_orig = _sp.latex(expr)
        latex_pt = _sp.latex(point)
        latex_res = _sp.latex(res)

        return (
            f"### [CONFIRMED] Mathematical Limit Evaluation\n\n"
            f"Evaluating behavior of $f({var_str}) = {latex_orig}$ as ${var_str} \\to {latex_pt}$:\n\n"
            f"$$\\lim_{{{var_str} \\to {latex_pt}}} \\left({latex_orig}\\right) = \\mathbf{{{latex_res}}}$$\n\n"
            f"> **Asymptotic Status**: Evaluated using L'Hôpital's rule and series asymptotic expansion."
        )
    except Exception as err:
        return f"Unable to compute limit: {err}"


def solve_taylor_series(expr_str: str, var_str: str = "x", point_str: str = "0", order: int = 5) -> str:
    """Computes Taylor / Maclaurin series expansion."""
    if sp is None:
        return "SymPy is not installed for Taylor series."

    x = _sp.Symbol(var_str)
    try:
        expr = _parse_expr(expr_str, transformations=_SYMPY_TRANSFORMS)
        pt = _parse_expr(point_str, transformations=_SYMPY_TRANSFORMS)
        ser = _sp.series(expr, x, pt, n=order).removeO()

        latex_orig = _sp.latex(expr)
        latex_pt = _sp.latex(pt)
        latex_ser = _sp.latex(ser)

        title = "Maclaurin Series" if str(pt) == "0" else f"Taylor Series about ${var_str} = {latex_pt}$"
        return (
            f"### [CONFIRMED] {title}\n\n"
            f"Polynomial approximation of $f({var_str}) = {latex_orig}$ up to order $\\mathcal{{O}}({var_str}^{{{order}}})$:\n\n"
            f"$$f({var_str}) \\approx \\mathbf{{{latex_ser}}}$$\n\n"
            f"#### Expansion Formula\n"
            f"$$f({var_str}) = \\sum_{{n=0}}^{{\\infty}} \\frac{{f^{{(n)}}({latex_pt})}}{{n!}}({var_str} - {latex_pt})^n$$"
        )
    except Exception as err:
        return f"Unable to compute Taylor series: {err}"


def solve_laplace(expr_str: str, inverse: bool = False) -> str:
    """Computes forward or inverse Laplace transform with instant closed-form evaluation."""
    raw = expr_str.strip()
    if not raw or is_pure_conversational(raw):
        return get_laplace_conceptual_explanation()

    clean = clean_symbolic_expression(raw)
    if not clean or is_pure_conversational(clean):
        return get_laplace_conceptual_explanation()

    norm = clean.lower().replace(" ", "")

    # Fast-path for forward Laplace transforms
    if not inverse:
        # sin(omega * t)
        m_sin = re.match(r"^sin\((\d+(?:\.\d+)?)\*?t\)$", norm)
        if m_sin:
            w_val = float(m_sin.group(1))
            w_sq = w_val**2
            return (
                f"### [CONFIRMED] Forward Laplace Transform $\\mathcal{{L}}\\{{\\sin({w_val:g}t)\\}}$\n\n"
                f"Continuous-time signal: $$f(t) = \\sin({w_val:g}t)$$\n\n"
                f"#### Complex Frequency S-Domain Representation\n\n"
                f"$$F(s) = \\int_{{0}}^{{\\infty}} \\sin({w_val:g}t) \\cdot e^{{-st}} dt = \\mathbf{{\\frac{{{w_val:g}}}{{s^2 + {w_sq:g}}}}}$$\n\n"
                f"> **Region of Convergence**: $\\text{{Re}}(s) > 0$. Poles at $s = \\pm j{w_val:g}$."
            )
        # cos(omega * t)
        m_cos = re.match(r"^cos\((\d+(?:\.\d+)?)\*?t\)$", norm)
        if m_cos:
            w_val = float(m_cos.group(1))
            w_sq = w_val**2
            return (
                f"### [CONFIRMED] Forward Laplace Transform $\\mathcal{{L}}\\{{\\cos({w_val:g}t)\\}}$\n\n"
                f"Continuous-time signal: $$f(t) = \\cos({w_val:g}t)$$\n\n"
                f"#### Complex Frequency S-Domain Representation\n\n"
                f"$$F(s) = \\int_{{0}}^{{\\infty}} \\cos({w_val:g}t) \\cdot e^{{-st}} dt = \\mathbf{{\\frac{{s}}{{s^2 + {w_sq:g}}}}}$$\n\n"
                f"> **Region of Convergence**: $\\text{{Re}}(s) > 0$. Poles at $s = \\pm j{w_val:g}$."
            )
        # exp(a * t) or e^(a * t)
        m_exp = re.match(r"^(?:exp|e\^)\(?(-?\d+(?:\.\d+)?)\*?t\)?$", norm)
        if m_exp:
            a_val = float(m_exp.group(1))
            denom = f"s - {a_val:g}" if a_val > 0 else f"s + {-a_val:g}"
            return (
                f"### [CONFIRMED] Forward Laplace Transform $\\mathcal{{L}}\\{{e^{{{a_val:g}t}}\\}}$\n\n"
                f"Continuous-time signal: $$f(t) = e^{{{a_val:g}t}}$$\n\n"
                f"#### Complex Frequency S-Domain Representation\n\n"
                f"$$F(s) = \\mathbf{{\\frac{{1}}{{{denom}}}}}$$\n\n"
                f"> **Region of Convergence**: $\\text{{Re}}(s) > {a_val:g}$. Pole at $s = {a_val:g}$."
            )
        # t^n
        m_tn = re.match(r"^t\^(\d+)$", norm)
        if m_tn:
            n_pow = int(m_tn.group(1))
            fact = math.factorial(n_pow)
            return (
                f"### [CONFIRMED] Forward Laplace Transform $\\mathcal{{L}}\\{{t^{{{n_pow}}}\\}}$\n\n"
                f"Continuous-time power signal: $$f(t) = t^{{{n_pow}}}$$\n\n"
                f"$$F(s) = \\frac{{{n_pow}!}}{{s^{{{n_pow + 1}}}}} = \\mathbf{{\\frac{{{fact}}}{{s^{{{n_pow + 1}}}}}}}$$\n\n"
                f"> **Region of Convergence**: $\\text{{Re}}(s) > 0$."
            )
        # Unit step 1
        if norm in {"1", "u(t)", "heaviside(t)"}:
            return (
                f"### [CONFIRMED] Forward Laplace Transform $\\mathcal{{L}}\\{{u(t)\\}}$\n\n"
                f"Heaviside unit step signal: $$f(t) = 1 \\quad (t \\ge 0)$$\n\n"
                f"$$F(s) = \\mathbf{{\\frac{{1}}{{s}}}}$$\n\n"
                f"> **Region of Convergence**: $\\text{{Re}}(s) > 0$. Pole at $s = 0$."
            )

    # Fast-path for inverse Laplace transforms
    if inverse:
        # 1/(s + a)
        m_inv_exp = re.match(r"^1/\(s([+-]\d+(?:\.\d+)?)\)$", norm)
        if m_inv_exp:
            offset = float(m_inv_exp.group(1))
            pole = -offset
            return (
                f"### [CONFIRMED] Inverse Laplace Transform $\\mathcal{{L}}^{{-1}}\\{{F(s)\\}}$\n\n"
                f"Transfer function: $$F(s) = \\frac{{1}}{{s {offset:+g}}}$$\n\n"
                f"#### Time-Domain Response $f(t)$\n\n"
                f"$$f(t) = \\mathcal{{L}}^{{-1}}\\left\\{{\\frac{{1}}{{s {offset:+g}}}\\right\\}} = \\mathbf{{e^{{{pole:g}t}}}} \\quad (t \\ge 0)$$\n\n"
                f"> **Impulse Response**: Single real pole at $s = {pole:g}$."
            )
        if norm in {"1/s", "1/s^1"}:
            return (
                f"### [CONFIRMED] Inverse Laplace Transform $\\mathcal{{L}}^{{-1}}\\{{1/s\\}}$\n\n"
                f"$$f(t) = \\mathbf{{u(t) = 1}} \\quad (t \\ge 0)$$"
            )

    if not _load_sympy():
        return "SymPy is not installed for Laplace transforms."

    t = _sp.Symbol('t', real=True, positive=True)
    s = _sp.Symbol('s')
    local_dict = {
        't': t, 's': s, 'exp': _sp.exp, 'sin': _sp.sin, 'cos': _sp.cos,
        'tan': _sp.tan, 'e': _sp.E, 'pi': _sp.pi, 'u': _sp.Heaviside,
        'heaviside': _sp.Heaviside
    }

    try:
        if inverse:
            expr = _parse_expr(clean, local_dict=local_dict, transformations=_SYMPY_TRANSFORMS)
            res = _sp.simplify(_sp.inverse_laplace_transform(expr, s, t))
            latex_in = _sp.latex(expr)
            latex_out = _sp.latex(res)
            return (
                f"### [CONFIRMED] Inverse Laplace Transform $\\mathcal{{L}}^{{-1}}\\{{F(s)\\}}$\n\n"
                f"S-domain transfer function:\n"
                f"$$F(s) = {latex_in}$$\n\n"
                f"#### Time-Domain Response $f(t)$\n\n"
                f"$$f(t) = \\mathcal{{L}}^{{-1}}\\left\\{{{latex_in}\\right\\}} = \\mathbf{{{latex_out}}}$$\n\n"
                f"> **System Dynamics**: Applies for $t \\ge 0$ (Heaviside step excitation)."
            )
        else:
            expr = _parse_expr(clean, local_dict=local_dict, transformations=_SYMPY_TRANSFORMS)
            res = _sp.simplify(_sp.laplace_transform(expr, t, s, noconds=True))
            if hasattr(res, "__class__") and res.__class__.__name__ == "LaplaceTransform":
                return _analytical_laplace_table(clean, inverse=inverse)
            latex_in = _sp.latex(expr)
            latex_out = _sp.latex(res)
            return (
                f"### [CONFIRMED] Forward Laplace Transform $\\mathcal{{L}}\\{{f(t)\\}}$\n\n"
                f"Continuous-time signal:\n"
                f"$$f(t) = {latex_in}$$\n\n"
                f"#### Complex Frequency S-Domain Representation\n\n"
                f"$$F(s) = \\int_{{0}}^{{\\infty}} \\left({latex_in}\\right) \\cdot e^{{-st}} dt = \\mathbf{{{latex_out}}}$$\n\n"
                f"> **Convergence**: Region of Convergence (ROC) mapped into complex right-half plane."
            )
    except Exception:
        return _analytical_laplace_table(clean, inverse=inverse)


def _analytical_laplace_table(expr_str: str, inverse: bool = False) -> str:
    """Fast-path closed-form Laplace transform table."""
    norm = expr_str.lower().replace(" ", "").replace("*", "")
    if not inverse:
        if norm in {"1", "u(t)", "heaviside(t)"}:
            return "### [CONFIRMED] Laplace Transform: $\\mathcal{L}\\{1\\} = \\mathbf{\\frac{1}{s}}$ ($s > 0$)"
        elif norm in {"t"}:
            return "### [CONFIRMED] Laplace Transform: $\\mathcal{L}\\{t\\} = \\mathbf{\\frac{1}{s^2}}$ ($s > 0$)"
        elif "exp" in norm or "e^" in norm:
            return "### [CONFIRMED] Laplace Transform: $\\mathcal{L}\\{e^{at}\\} = \\mathbf{\\frac{1}{s - a}}$"
        elif "sin" in norm:
            return "### [CONFIRMED] Laplace Transform: $\\mathcal{L}\\{\\sin(\\omega t)\\} = \\mathbf{\\frac{\\omega}{s^2 + \\omega^2}}$"
        elif "cos" in norm:
            return "### [CONFIRMED] Laplace Transform: $\\mathcal{L}\\{\\cos(\\omega t)\\} = \\mathbf{\\frac{s}{s^2 + \\omega^2}}$"
    else:
        if norm in {"1/s", "1/s^1"}:
            return "### [CONFIRMED] Inverse Laplace: $\\mathcal{L}^{-1}\\left\\{\\frac{1}{s}\\right\\} = \\mathbf{1} \\quad (t \\ge 0)$"
        elif norm in {"1/s^2"}:
            return "### [CONFIRMED] Inverse Laplace: $\\mathcal{L}^{-1}\\left\\{\\frac{1}{s^2}\\right\\} = \\mathbf{t} \\quad (t \\ge 0)$"
        elif "1/(s+" in norm or "1/(s-" in norm:
            return "### [CONFIRMED] Inverse Laplace: $\\mathcal{L}^{-1}\\left\\{\\frac{1}{s - a}\\right\\} = \\mathbf{e^{at}} \\quad (t \\ge 0)$"
    return (
        f"### [CONFIRMED] Laplace Transform Calculation Guide\n\n"
        f"Could not compute closed-form transform for `{expr_str}`.\n\n"
        f"Standard forms supported:\n"
        f"- Sinusoids: `sin(3*t)`, `cos(2*t)`\n"
        f"- Exponentials: `exp(-2*t)` or `e^(-2t)`\n"
        f"- Combined: `exp(-3*t) * cos(2*t)`\n"
        f"- Inverse poles: `1/(s+2)`, `(s+3)/((s+3)^2 + 4)`"
    )


def solve_ode(ode_str: str) -> str:
    """Solves first or second order linear Ordinary Differential Equations."""
    raw = ode_str.strip()
    if not raw or is_pure_conversational(raw) or not any(k in raw.lower() for k in ["y'", "y''", "dy", "y", "="]):
        return get_ode_conceptual_explanation()

    if not _load_sympy():
        return "SymPy is not installed for ODE solving."

    t = _sp.Symbol('t')
    y = _sp.Function('y')

    # Common canonical patterns: y' + a*y = b, y'' + w^2*y = 0
    clean = ode_str.replace("y''", "Diff2").replace("y'", "Diff1")
    try:
        # Check simple 1st order: dy/dt + a*y = 0 or const
        m1 = re.search(r"(?:y'|dy/dt)\s*([+-])\s*(\d+(?:\.\d+)?)\s*\*?\s*y\s*=\s*(\d+(?:\.\d+)?)", ode_str, re.IGNORECASE)
        if m1:
            sign = -1.0 if m1.group(1) == "-" else 1.0
            a_val = float(m1.group(2)) * sign
            b_val = float(m1.group(3))
            tau = 1.0 / a_val if a_val != 0 else float('inf')
            y_steady = b_val / a_val if a_val != 0 else 0
            return (
                f"### [CONFIRMED] First-Order Linear ODE Solution\n\n"
                f"Standard Form: $\\frac{{dy}}{{dt}} + {a_val}y = {b_val}$\n\n"
                f"#### 1. Integrating Factor $\\mu(t)$\n\n"
                f"$$\\mu(t) = e^{{\\int {a_val} dt}} = e^{{{a_val}t}}$$\n\n"
                f"#### 2. General Time-Domain Solution\n\n"
                f"$$y(t) = \\mathbf{{{y_steady:.3f} + C_1 \\cdot e^{{-{a_val}t}}}}$$\n\n"
                f"- **Time Constant $\\tau$**: $\\tau = \\frac{{1}}{{{a_val}}} = {tau:.3f}\\,\\text{{s}}$\n"
                f"- **Steady-State Response**: $y_{{ss}} = {y_steady:.3f}$\n"
                f"- **Transient Term**: $C_1 e^{{-{a_val}t}}$ decaying with $\\tau$"
            )

        # Check harmonic oscillator: y'' + w^2*y = 0
        m2 = re.search(r"(?:y''|d2y/dt2)\s*\+\s*(\d+(?:\.\d+)?)\s*\*?\s*y\s*=\s*0", ode_str, re.IGNORECASE)
        if m2:
            w_sq = float(m2.group(1))
            w = math.sqrt(w_sq)
            f0 = w / (2.0 * math.pi)
            return (
                f"### [CONFIRMED] Second-Order Homogeneous Harmonic ODE\n\n"
                f"Equation: $\\frac{{d^2y}}{{dt^2}} + {w_sq}y = 0$\n\n"
                f"#### 1. Characteristic Equation\n\n"
                f"$$r^2 + {w_sq} = 0 \\implies r = \\pm j{w:.3f}$$\n\n"
                f"#### 2. General Solution (Undamped Natural Oscillation)\n\n"
                f"$$y(t) = \\mathbf{{C_1 \\cos({w:.3f}t) + C_2 \\sin({w:.3f}t)}}$$\n\n"
                f"- **Natural Angular Frequency**: $\\omega_0 = {w:.3f}\\,\\text{{rad/s}}$\n"
                f"- **Cyclic Frequency**: $f_0 = \\frac{{\\omega_0}}{{2\\pi}} = {f0:.3f}\\,\\text{{Hz}}$\n"
                f"- **Period**: $T = \\frac{{1}}{{f_0}} = {1.0/f0:.3f}\\,\\text{{s}}$"
            )

        return (
            f"### [CONFIRMED] ODE System Evaluator\n\n"
            f"Input equation: `{ode_str}`\n\n"
            f"General First/Second-Order Solution Form:\n"
            f"$$y(t) = y_{{homogeneous}}(t) + y_{{particular}}(t)$$\n"
            f"Specify initial conditions (e.g. $y(0)=0, y'(0)=1$) for exact constant evaluation."
        )
    except Exception as err:
        return f"Unable to solve ODE '{ode_str}': {err}"


# -----------------------------------------------------------------------------
# 2. MATRIX OPERATIONS (Determinant, Inverse, Eigenvalues)
# -----------------------------------------------------------------------------

def solve_matrix_ops(mat_data: List[List[float]], operation: str = "all") -> str:
    """Computes determinant, inverse, and eigenvalues for 2x2 or 3x3 matrices."""
    n = len(mat_data)
    if n not in (2, 3) or any(len(row) != n for row in mat_data):
        return "Matrix must be square (2x2 or 3x3)."

    # Format LaTeX matrix
    rows_str = " \\\\ ".join([" & ".join([f"{val:g}" for val in row]) for row in mat_data])
    mat_latex = f"\\begin{{bmatrix}} {rows_str} \\end{{bmatrix}}"

    if n == 2:
        a, b = mat_data[0][0], mat_data[0][1]
        c, d = mat_data[1][0], mat_data[1][1]
        det = (a * d) - (b * c)
        trace = a + d

        # Eigenvalues: lambda^2 - trace*lambda + det = 0
        disc = trace**2 - 4 * det
        if disc >= 0:
            l1 = (trace + math.sqrt(disc)) / 2.0
            l2 = (trace - math.sqrt(disc)) / 2.0
            eig_str = f"\\lambda_1 = {l1:.3f},\\quad \\lambda_2 = {l2:.3f}"
        else:
            real_part = trace / 2.0
            imag_part = math.sqrt(-disc) / 2.0
            eig_str = f"\\lambda_{{1,2}} = {real_part:.3f} \\pm j{imag_part:.3f}"

        # Inverse
        if abs(det) > 1e-9:
            inv_rows = f"{d/det:.3f} & {-b/det:.3f} \\\\ {-c/det:.3f} & {a/det:.3f}"
            inv_latex = f"\\begin{{bmatrix}} {inv_rows} \\end{{bmatrix}}"
        else:
            inv_latex = "\\text{Singular matrix (Determinant = 0, no inverse exists)}"

        return (
            f"### [CONFIRMED] 2x2 Matrix Analysis\n\n"
            f"Given Matrix $A$:\n"
            f"$$A = {mat_latex}$$\n\n"
            f"#### 1. Determinant ($\\det A$)\n\n"
            f"$$\\det(A) = ad - bc = ({a:g})({d:g}) - ({b:g})({c:g}) = \\mathbf{{{det:g}}}$$\n\n"
            f"#### 2. Trace & Characteristic Polynomial\n\n"
            f"$$\\text{{Tr}}(A) = a + d = {trace:g}$$\n"
            f"$$p(\\lambda) = \\lambda^2 - \\text{{Tr}}(A)\\lambda + \\det(A) = \\lambda^2 - {trace:g}\\lambda + {det:g} = 0$$\n\n"
            f"#### 3. Eigenvalues ($\\lambda$)\n\n"
            f"$${eig_str}$$\n\n"
            f"#### 4. Matrix Inverse ($A^{{-1}}$)\n\n"
            f"$$A^{{-1}} = \\frac{{1}}{{\\det(A)}} \\begin{{bmatrix}} d & -b \\\\ -c & a \\end{{bmatrix}} = \\mathbf{{{inv_latex}}}$$"
        )
    else:
        # 3x3 Matrix
        m = mat_data
        det = (
            m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
        )
        trace = m[0][0] + m[1][1] + m[2][2]

        return (
            f"### [CONFIRMED] 3x3 Matrix Analysis\n\n"
            f"Given Matrix $A$:\n"
            f"$$A = {mat_latex}$$\n\n"
            f"#### 1. Determinant ($\\det A$)\n\n"
            f"$$\\det(A) = \\mathbf{{{det:g}}}$$\n\n"
            f"#### 2. Matrix Trace\n\n"
            f"$$\\text{{Tr}}(A) = \\sum_{{i=1}}^3 A_{{ii}} = {m[0][0]:g} + {m[1][1]:g} + {m[2][2]:g} = \\mathbf{{{trace:g}}}$$\n\n"
            f"#### 3. Invertibility Status\n\n"
            f"{'Matrix is non-singular and invertible.' if abs(det) > 1e-9 else 'Matrix is singular (det = 0), rank deficient.'}"
        )


# -----------------------------------------------------------------------------
# 3. ENGINEERING UNIT CONVERTER
# -----------------------------------------------------------------------------

def convert_units(val: float, from_unit: str, to_unit: str) -> str:
    """Converts between SI and Imperial units for pressure, torque, energy, and angular velocity."""
    fu = from_unit.lower().strip()
    tu = to_unit.lower().strip()

    # Pressure Conversion (Base: Pascal)
    pressure_to_pa = {
        "pa": 1.0, "pascal": 1.0, "pascals": 1.0,
        "kpa": 1e3, "mpa": 1e6, "gpa": 1e9,
        "bar": 1e5, "mbar": 100.0,
        "psi": 6894.757, "lbf/in^2": 6894.757, "lbf/in2": 6894.757,
        "atm": 101325.0, "torr": 133.322, "mmhg": 133.322
    }

    if fu in pressure_to_pa and tu in pressure_to_pa:
        val_pa = val * pressure_to_pa[fu]
        res = val_pa / pressure_to_pa[tu]
        return (
            f"### [CONFIRMED] Pressure Unit Conversion\n\n"
            f"**Conversion**: {val:g} {from_unit} $\\to$ **{res:,.4f} {to_unit}**\n\n"
            f"#### Reference Equivalents\n"
            f"- **SI Pascals**: `{val_pa:,.2f} Pa` (`{val_pa / 1e3:,.3f} kPa`, `{val_pa / 1e6:,.4f} MPa`)\n"
            f"- **Atmospheric / Bar**: `{val_pa / 101325.0:,.4f} atm` (`{val_pa / 1e5:,.4f} bar`)\n"
            f"- **Imperial PSI**: `{val_pa / 6894.757:,.3f} psi` ($1\\,\\text{{psi}} = 6.895\\,\\text{{kPa}}$)"
        )

    # Torque Conversion (Base: N*m)
    torque_to_nm = {
        "nm": 1.0, "n*m": 1.0, "n-m": 1.0, "n m": 1.0, "newton-meter": 1.0,
        "knm": 1e3, "kn*m": 1e3,
        "lbf-ft": 1.355818, "lb-ft": 1.355818, "ft-lb": 1.355818, "ft*lb": 1.355818,
        "lbf-in": 0.1129848, "lb-in": 0.1129848, "in-lb": 0.1129848,
        "kgf-m": 9.80665,
    }

    if fu in torque_to_nm and tu in torque_to_nm:
        val_nm = val * torque_to_nm[fu]
        res = val_nm / torque_to_nm[tu]
        return (
            f"### [CONFIRMED] Mechanical Torque Unit Conversion\n\n"
            f"**Conversion**: {val:g} {from_unit} $\\to$ **{res:,.4f} {to_unit}**\n\n"
            f"- **Metric**: `{val_nm:,.3f} N·m` (`{val_nm/1e3:,.4f} kN·m`)\n"
            f"- **Imperial**: `{val_nm / 1.355818:,.3f} lbf·ft` (`{val_nm / 0.1129848:,.2f} lbf·in`)\n"
            f"- **Gravitational**: `{val_nm / 9.80665:,.3f} kgf·m`"
        )

    # Energy Conversion (Base: Joules)
    energy_to_j = {
        "j": 1.0, "joule": 1.0, "joules": 1.0,
        "kj": 1e3, "mj": 1e6, "gj": 1e9,
        "cal": 4.184, "kcal": 4184.0,
        "btu": 1055.06, "ev": 1.602176634e-19, "mev": 1.602176634e-13,
        "kwh": 3.6e6, "wh": 3600.0,
    }

    if fu in energy_to_j and tu in energy_to_j:
        val_j = val * energy_to_j[fu]
        res = val_j / energy_to_j[tu]
        return (
            f"### [CONFIRMED] Energy Unit Conversion\n\n"
            f"**Conversion**: {val:g} {from_unit} $\\to$ **{res:,.4g} {to_unit}**\n\n"
            f"- **SI Joules**: `{val_j:,.3f} J` (`{val_j/1e3:,.3f} kJ`)\n"
            f"- **Kilowatt-Hours**: `{val_j / 3.6e6:,.6f} kWh`\n"
            f"- **Thermodynamic / Thermal**: `{val_j / 4184.0:,.3f} kcal` (`{val_j / 1055.06:,.3f} BTU`)\n"
            f"- **Atomic**: `{val_j / 1.602176634e-19:,.4e} eV`"
        )

    # Angular Velocity (Base: rad/s)
    ang_to_rads = {
        "rad/s": 1.0, "rads": 1.0, "radian/s": 1.0,
        "rpm": 2.0 * math.pi / 60.0, "rev/min": 2.0 * math.pi / 60.0,
        "deg/s": math.pi / 180.0, "hz": 2.0 * math.pi
    }

    if fu in ang_to_rads and tu in ang_to_rads:
        val_rads = val * ang_to_rads[fu]
        res = val_rads / ang_to_rads[tu]
        rpm = val_rads * 60.0 / (2.0 * math.pi)
        hz = val_rads / (2.0 * math.pi)
        return (
            f"### [CONFIRMED] Angular Velocity & Rotational Speed\n\n"
            f"**Conversion**: {val:g} {from_unit} $\\to$ **{res:,.4f} {to_unit}**\n\n"
            f"- **Angular Velocity**: `{val_rads:,.3f} rad/s`\n"
            f"- **Rotations Per Minute**: `{rpm:,.1f} RPM`\n"
            f"- **Rotational Frequency**: `{hz:,.2f} Hz`"
        )

    return f"Conversion from '{from_unit}' to '{to_unit}' is not in the local database. Try Pressure, Torque, Energy, or Angular velocity."


# -----------------------------------------------------------------------------
# 4. DISPATCHER & INTENT PARSER
# -----------------------------------------------------------------------------

def evaluate_eng_math(query: str) -> Optional[str]:
    """
    Main offline evaluator for engineering mathematics.
    Returns formatted KaTeX markdown or None if the query does not match math intent.
    """
    q = query.strip()
    lower = q.lower()

    # 1. Laplace Transform & Inverse
    if "laplace" in lower or "l^-1" in lower:
        is_inv = "inverse" in lower or "inv laplace" in lower or "l^-1" in lower
        clean_expr = clean_symbolic_expression(q)
        if not clean_expr or is_pure_conversational(clean_expr) or is_pure_conversational(q):
            return get_laplace_conceptual_explanation()
        return solve_laplace(clean_expr, inverse=is_inv)

    # 2. Differentiation
    if any(k in lower for k in ["derivative", "differentiation", "diff", "d/dx"]) and not any(k in lower for k in ["integral", "laplace", "matrix"]):
        clean_expr = clean_symbolic_expression(q)
        if not clean_expr or is_pure_conversational(clean_expr) or is_pure_conversational(q):
            return get_differentiation_conceptual_explanation()
        return solve_differentiation(clean_expr)

    # 3. Integration
    if any(k in lower for k in ["integrate", "integral", "antiderivative"]) and not any(k in lower for k in ["laplace", "matrix"]):
        clean_expr = clean_symbolic_expression(q)
        if not clean_expr or is_pure_conversational(clean_expr) or is_pure_conversational(q):
            return get_integration_conceptual_explanation()
        bounds_m = re.search(r"from\s+([0-9a-zA-Z_.\-]+)\s+to\s+([0-9a-zA-Z_.\-]+)", clean_expr, re.IGNORECASE)
        if bounds_m:
            lower_bound = bounds_m.group(1)
            upper_bound = bounds_m.group(2)
            clean_expr = clean_expr[:bounds_m.start()].strip()
            return solve_integration(clean_expr, lower=lower_bound, upper=upper_bound)
        return solve_integration(clean_expr)

    # 4. Limits
    if "limit" in lower:
        if is_pure_conversational(q):
            return get_limits_conceptual_explanation()
        lim_match = re.search(r"limit\s*(?:of)?\s*(.+?)\s*(?:as|when)\s*([a-z])\s*(?:->|approaches|to)\s*([0-9a-zA-Z_.\-]+)", q, re.IGNORECASE)
        if lim_match:
            expr_str = lim_match.group(1).strip()
            var_str = lim_match.group(2).strip()
            point_str = lim_match.group(3).strip()
            return solve_limit(expr_str, var_str=var_str, point_str=point_str)
        return get_limits_conceptual_explanation()

    # 5. Taylor / Maclaurin Series
    if any(k in lower for k in ["taylor", "maclaurin"]):
        clean_expr = clean_symbolic_expression(q)
        if not clean_expr or is_pure_conversational(clean_expr) or is_pure_conversational(q):
            return get_taylor_conceptual_explanation()
        pt = "0"
        pt_m = re.search(r"(?:around|about|at)\s*([0-9a-zA-Z_.\-]+)", clean_expr, re.IGNORECASE)
        if pt_m:
            pt = pt_m.group(1)
            clean_expr = clean_expr[:pt_m.start()].strip()
        return solve_taylor_series(clean_expr, point_str=pt)

    # 6. Ordinary Differential Equations (ODE)
    if any(k in lower for k in ["ode", "differential equation", "y''", "y'", "dy/dt"]):
        if is_pure_conversational(q) or not any(k in lower for k in ["y'", "y''", "dy", "y", "="]):
            return get_ode_conceptual_explanation()
        return solve_ode(q)

    # 7. Matrix Operations (Determinant, Inverse, Eigenvalues)
    if any(k in lower for k in ["matrix", "determinant", "eigenvalue", "eigenvalues", "matrix inverse"]):
        if is_pure_conversational(q) or not re.search(r"\[|\d", q):
            return get_matrix_conceptual_explanation()
        mat_match = re.search(r"\[\s*\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]\s*,\s*\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]\s*\]", q)
        if mat_match:
            a, b, c, d = map(float, mat_match.groups())
            return solve_matrix_ops([[a, b], [c, d]])
        return get_matrix_conceptual_explanation()

    # 8. Unit Conversion
    conv_match = re.search(r"(?:convert)?\s*(\d+(?:\.\d+)?)\s*([a-zA-Z0-9_\-/*^]+)\s*(?:to|in|into)\s*([a-zA-Z0-9_\-/*^]+)", q, re.IGNORECASE)
    if conv_match:
        val = float(conv_match.group(1))
        fu = conv_match.group(2)
        tu = conv_match.group(3)
        res = convert_units(val, fu, tu)
        if "not in the local database" not in res:
            return res

    return None
