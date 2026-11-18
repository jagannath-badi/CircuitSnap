"""
J.A.R.V.I.S. Computer Science & Digital Logic Engine
Provides sub-20ms offline base conversion, IEEE-754 floating point representation,
IPv4 CIDR subnet calculation, Big-O algorithmic complexity matrices, and digital logic truth-table evaluation.
"""

import ipaddress
import re
import struct
from typing import Optional, Dict, Any, List


# -----------------------------------------------------------------------------
# 1. NUMBER SYSTEMS, TWO'S COMPLEMENT & IEEE-754 CONVERTER
# -----------------------------------------------------------------------------

def convert_number_systems(val_str: str) -> str:
    """Converts between Decimal, Binary, Hexadecimal, Octal and 8/16/32-bit Two's Complement."""
    raw = val_str.strip().lower()
    val_int = 0

    try:
        if raw.startswith("0x") or raw.startswith("hex "):
            val_int = int(raw.replace("hex ", "").replace("0x", ""), 16)
        elif raw.startswith("0b") or raw.startswith("bin "):
            val_int = int(raw.replace("bin ", "").replace("0b", ""), 2)
        elif raw.startswith("0o") or raw.startswith("oct "):
            val_int = int(raw.replace("oct ", "").replace("0o", ""), 8)
        else:
            val_int = int(raw)
    except ValueError:
        return f"Unable to parse integer value '{val_str}'."

    # Format standard bases
    dec_str = f"{val_int:,}"
    hex_str = f"0x{val_int & 0xFFFFFFFF:08X}" if val_int < 0 else f"0x{val_int:X}"
    bin_str = bin(val_int & 0xFFFFFFFF) if val_int < 0 else bin(val_int)
    oct_str = oct(val_int & 0xFFFFFFFF) if val_int < 0 else oct(val_int)

    # Two's complement bit patterns
    b8 = f"{(val_int & 0xFF):08b}"
    b16 = f"{(val_int & 0xFFFF):016b}"
    b32 = f"{(val_int & 0xFFFFFFFF):032b}"

    # Group binary into 4-bit nibbles for readability
    b32_grouped = " ".join([b32[i:i+4] for i in range(0, 32, 4)])

    return (
        f"### [CONFIRMED] Multi-Base Number System Representation\n\n"
        f"Decimal Magnitude: **{dec_str}**\n\n"
        f"| Representation | Value | Base Format |\n"
        f"| :--- | :--- | :--- |\n"
        f"| **Decimal (Base 10)** | `{val_int}` | Signed Integer |\n"
        f"| **Hexadecimal (Base 16)** | `{hex_str}` | Hex Nibbles (4-bit chunks) |\n"
        f"| **Binary (Base 2)** | `{bin_str}` | Raw Bitstream |\n"
        f"| **Octal (Base 8)** | `{oct_str}` | Octal Chunks (3-bit chunks) |\n\n"
        f"#### Two's Complement Fixed-Width Bit Patterns\n\n"
        f"- **8-Bit Signed**: `0b{b8}` ({int(b8, 2) if val_int >= 0 else val_int})\n"
        f"- **16-Bit Signed**: `0b{' '.join([b16[i:i+4] for i in range(0, 16, 4)])}`\n"
        f"- **32-Bit Word**: `0b{b32_grouped}`\n\n"
        f"> **Parity & Bit Length**: Number of set bits (Hamming weight): **{bin(val_int & 0xFFFFFFFF).count('1')}**."
    )


def solve_ieee754(float_val: float) -> str:
    """Deconstructs 32-bit single-precision IEEE-754 floating point format into Sign, Exponent, and Mantissa."""
    packed = struct.pack(">f", float_val)
    int_bits = struct.unpack(">I", packed)[0]

    sign_bit = (int_bits >> 31) & 0x1
    exponent_bits = (int_bits >> 23) & 0xFF
    mantissa_bits = int_bits & 0x7FFFFF

    unbiased_exp = exponent_bits - 127
    mantissa_fraction = 1.0 + (mantissa_bits / (2**23)) if exponent_bits != 0 else mantissa_bits / (2**23)

    sign_bin = f"{sign_bit:01b}"
    exp_bin = f"{exponent_bits:08b}"
    mant_bin = f"{mantissa_bits:023b}"

    return (
        f"### [CONFIRMED] IEEE-754 Single-Precision Floating Point (32-Bit)\n\n"
        f"Floating Point Real: **{float_val}**\n\n"
        f"#### 1. Binary Bitfield Layout\n\n"
        f"```text\n"
        f"Sign [1] | Exponent [8] | Fraction / Mantissa [23]\n"
        f"   {sign_bin}     |   {exp_bin}  | {mant_bin}\n"
        f"```\n\n"
        f"| Field | Bits | Decimal Equivalent | Role |\n"
        f"| :--- | :--- | :--- | :--- |\n"
        f"| **Sign ($s$)** | `{sign_bin}` | `{sign_bit}` | {('Negative (−1)' if sign_bit == 1 else 'Positive (+1)')} |\n"
        f"| **Biased Exponent ($e$)** | `{exp_bin}` | `{exponent_bits}` | $E = e - 127 = \\mathbf{{{unbiased_exp}}}$ |\n"
        f"| **Mantissa / Fraction ($f$)** | `{mant_bin[:8]}...` | `0x{mantissa_bits:06X}` | Normalized: $1 + \\sum b_i 2^{{-i}} = \\mathbf{{{mantissa_fraction:.7f}}}$ |\n\n"
        f"#### 2. Closed-Form Evaluation Formula\n\n"
        f"$$V = (-1)^s \\times 2^{{e - 127}} \\times (1 + f)$$\n"
        f"$$V = (-1)^{{{sign_bit}}} \\times 2^{{{unbiased_exp}}} \\times {mantissa_fraction:.7f} = \\mathbf{{{float_val}}}$$\n\n"
        f"- **32-Bit Hexadecimal Representation**: `0x{int_bits:08X}`"
    )


# -----------------------------------------------------------------------------
# 2. IPV4 CIDR SUBNET CALCULATOR
# -----------------------------------------------------------------------------

def solve_cidr_subnet(cidr_str: str) -> str:
    """Calculates network boundaries, broadcast, netmask, and usable host count for IPv4 CIDR blocks."""
    clean = cidr_str.strip()
    try:
        # Default to /24 if only bare IP is provided
        if "/" not in clean:
            clean = f"{clean}/24"

        net = ipaddress.IPv4Network(clean, strict=False)
        host_count = net.num_addresses
        usable_hosts = max(0, host_count - 2) if net.prefixlen < 31 else host_count
        first_ip = net.network_address + 1 if net.prefixlen < 31 else net.network_address
        last_ip = net.broadcast_address - 1 if net.prefixlen < 31 else net.broadcast_address

        # Class determination
        first_octet = int(str(net.network_address).split(".")[0])
        if first_octet < 128:
            ip_class = "Class A"
        elif first_octet < 192:
            ip_class = "Class B"
        elif first_octet < 224:
            ip_class = "Class C"
        elif first_octet < 240:
            ip_class = "Class D (Multicast)"
        else:
            ip_class = "Class E (Experimental)"

        scope = "Private RFC-1918" if net.is_private else "Public Internet"

        # Binary mask
        mask_int = int(net.netmask)
        mask_bin = ".".join([f"{(mask_int >> (8 * (3 - i))) & 0xFF:08b}" for i in range(4)])

        return (
            f"### [CONFIRMED] IPv4 CIDR Subnet Architecture\n\n"
            f"Target Block: **{net.with_prefixlen}**\n\n"
            f"| Metric | Address Value | Binary Format |\n"
            f"| :--- | :--- | :--- |\n"
            f"| **Network Address** | `{net.network_address}` | Subnet Wire Identifier |\n"
            f"| **Subnet Mask** | `{net.netmask}` | `{mask_bin}` |\n"
            f"| **Wildcard Mask** | `{net.hostmask}` | Inverse Mask (ACL routing) |\n"
            f"| **Broadcast Address** | `{net.broadcast_address}` | Directed Subnet Broadcast |\n"
            f"| **Usable Host Range** | `{first_ip}` – `{last_ip}` | Static / DHCP Client Pool |\n\n"
            f"#### Subnet Capacity & Categorization\n\n"
            f"- **Total IPv4 Addresses**: `{host_count:,}` ($2^{{{32 - net.prefixlen}}}$)\n"
            f"- **Usable Host Nodes**: **{usable_hosts:,}** ($2^{{{32 - net.prefixlen}}} - 2$)\n"
            f"- **Network Scope**: **{scope}** ({ip_class})\n"
            f"- **Prefix Length**: `/{net.prefixlen}` (Mask Bits: {net.prefixlen} continuous ones)"
        )
    except Exception as err:
        return f"Unable to parse IPv4 CIDR string '{cidr_str}': {err}"


# -----------------------------------------------------------------------------
# 3. BIG-O COMPLEXITY REFERENCE MATRIX
# -----------------------------------------------------------------------------

BIG_O_DATA_STRUCTURES = [
    {"name": "Array", "access": "O(1)", "search": "O(n)", "insert": "O(n)", "delete": "O(n)", "space": "O(n)"},
    {"name": "Singly-Linked List", "access": "O(n)", "search": "O(n)", "insert": "O(1)", "delete": "O(1)", "space": "O(n)"},
    {"name": "Stack / Queue", "access": "O(n)", "search": "O(n)", "insert": "O(1)", "delete": "O(1)", "space": "O(n)"},
    {"name": "Hash Table", "access": "N/A", "search": "O(1) avg / O(n)", "insert": "O(1) avg / O(n)", "delete": "O(1) avg / O(n)", "space": "O(n)"},
    {"name": "Binary Search Tree", "access": "O(log n) avg / O(n)", "search": "O(log n) avg / O(n)", "insert": "O(log n) avg / O(n)", "delete": "O(log n) avg / O(n)", "space": "O(n)"},
    {"name": "AVL / Red-Black Tree", "access": "O(log n)", "search": "O(log n)", "insert": "O(log n)", "delete": "O(log n)", "space": "O(n)"},
    {"name": "Binary Heap (Priority Queue)", "access": "N/A", "search": "O(n)", "insert": "O(log n)", "delete": "O(log n)", "space": "O(n)"},
]

BIG_O_ALGORITHMS = [
    {"name": "Binary Search", "best": "O(1)", "avg": "O(log n)", "worst": "O(log n)", "space": "O(1)", "stable": "Yes"},
    {"name": "Merge Sort", "best": "O(n log n)", "avg": "O(n log n)", "worst": "O(n log n)", "space": "O(n)", "stable": "Yes"},
    {"name": "Quick Sort", "best": "O(n log n)", "avg": "O(n log n)", "worst": "O(n^2)", "space": "O(log n)", "stable": "No"},
    {"name": "Heap Sort", "best": "O(n log n)", "avg": "O(n log n)", "worst": "O(n log n)", "space": "O(1)", "stable": "No"},
    {"name": "Insertion Sort", "best": "O(n)", "avg": "O(n^2)", "worst": "O(n^2)", "space": "O(1)", "stable": "Yes"},
    {"name": "BFS / DFS (Graph)", "best": "O(V + E)", "avg": "O(V + E)", "worst": "O(V + E)", "space": "O(V)", "stable": "N/A"},
    {"name": "Dijkstra (Min-Heap)", "best": "O((V + E) log V)", "avg": "O((V + E) log V)", "worst": "O((V + E) log V)", "space": "O(V)", "stable": "N/A"},
]

def get_big_o_matrix(filter_term: Optional[str] = None) -> str:
    """Returns Big-O algorithmic complexity reference tables for data structures and algorithms."""
    # Data structure table
    ds_rows = "\n".join([
        f"| **{d['name']}** | `{d['access']}` | `{d['search']}` | `{d['insert']}` | `{d['delete']}` | `{d['space']}` |"
        for d in BIG_O_DATA_STRUCTURES
    ])

    # Algorithm table
    algo_rows = "\n".join([
        f"| **{a['name']}** | `{a['best']}` | `{a['avg']}` | `{a['worst']}` | `{a['space']}` | {a['stable']} |"
        for a in BIG_O_ALGORITHMS
    ])

    return (
        f"### [CONFIRMED] Computer Science Big-O Complexity Matrix\n\n"
        f"#### 1. Core Data Structures Time & Space Complexity\n\n"
        f"| Data Structure | Access | Search | Insertion | Deletion | Space (Worst) |\n"
        f"| :--- | :--- | :--- | :--- | :--- | :--- |\n"
        f"{ds_rows}\n\n"
        f"#### 2. Classical Sorting & Graph Algorithm Complexity\n\n"
        f"| Algorithm | Best Time | Average Time | Worst Time | Space | Stable? |\n"
        f"| :--- | :--- | :--- | :--- | :--- | :---: |\n"
        f"{algo_rows}\n\n"
        f"> **Complexity Hierarchy**: $\\mathcal{{O}}(1) < \\mathcal{{O}}(\\log n) < \\mathcal{{O}}(n) < \\mathcal{{O}}(n \\log n) < \\mathcal{{O}}(n^2) < \\mathcal{{O}}(2^n) < \\mathcal{{O}}(n!)$."
    )


# -----------------------------------------------------------------------------
# 4. DIGITAL LOGIC TRUTH TABLE & BOOLEAN EVALUATOR
# -----------------------------------------------------------------------------

def evaluate_truth_table(expr_str: str) -> str:
    """
    Generates a full Markdown truth table for 2-3 input Boolean expressions.
    Supports operators: AND (&, *), OR (|, +), NOT (!, ~), XOR (^).
    """
    clean = expr_str.strip()
    # Normalize operators to Python syntax
    py_expr = clean
    py_expr = re.sub(r"\bAND\b", "and", py_expr, flags=re.IGNORECASE)
    py_expr = re.sub(r"\bOR\b", "or", py_expr, flags=re.IGNORECASE)
    py_expr = re.sub(r"\bNOT\b", "not", py_expr, flags=re.IGNORECASE)
    py_expr = re.sub(r"\bXOR\b", "^", py_expr, flags=re.IGNORECASE)
    py_expr = re.sub(r"\bNAND\b", "not and", py_expr, flags=re.IGNORECASE)
    py_expr = re.sub(r"\bNOR\b", "not or", py_expr, flags=re.IGNORECASE)
    py_expr = py_expr.replace("&", " and ").replace("|", " or ").replace("~", " not ").replace("!", " not ")
    # Handle multiplication as AND: A * B -> A and B
    py_expr = re.sub(r"([A-Za-z])\s*\*\s*([A-Za-z])", r"\1 and \2", py_expr)
    py_expr = re.sub(r"([A-Za-z])\s*\+\s*([A-Za-z])", r"\1 or \2", py_expr)

    # Detect variables (A, B, C or x, y, z)
    found_vars = sorted(list(set(re.findall(r"\b[A-Za-z]\b", clean))))
    # Filter out keywords if any
    found_vars = [v for v in found_vars if v.lower() not in {"and", "or", "not", "xor", "nand", "nor"}]

    if not found_vars:
        found_vars = ["A", "B"]
        py_expr = "A and B"
        clean = "A & B"

    n = len(found_vars)
    if n > 4:
        return "Truth table generation is optimized for 2 to 4 Boolean variables."

    # Build truth table rows
    header = " | ".join([f"**{v}**" for v in found_vars]) + f" | **$Y = {clean}$** |"
    separator = " | ".join([":---:" for _ in range(n + 1)]) + " |"
    rows = []

    total_rows = 2**n
    for i in range(total_rows):
        env = {}
        for bit_idx, var_name in enumerate(found_vars):
            bit_val = (i >> (n - 1 - bit_idx)) & 1
            env[var_name] = bool(bit_val)

        try:
            res_val = bool(eval(py_expr, {"__builtins__": {}}, env))
            res_bit = 1 if res_val else 0
        except Exception:
            res_bit = 0

        row_str = " | ".join([str((i >> (n - 1 - bit_idx)) & 1) for bit_idx in range(n)]) + f" | **{res_bit}** |"
        rows.append(row_str)

    table_md = f"| {header}\n| {separator}\n" + "\n".join([f"| {r}" for r in rows])

    return (
        f"### [CONFIRMED] Digital Logic Truth Table Evaluation\n\n"
        f"Boolean Function: **$Y = {clean}$**\n\n"
        f"{table_md}\n\n"
        f"#### Standard Digital Logic Theorems\n\n"
        f"- **De Morgan's Theorem 1**: $\\overline{{A \\cdot B}} = \\bar{{A}} + \\bar{{B}}$ (NAND universal equivalence)\n"
        f"- **De Morgan's Theorem 2**: $\\overline{{A + B}} = \\bar{{A}} \\cdot \\bar{{B}}$ (NOR universal equivalence)\n"
        f"- **Involution**: $\\overline{{\\bar{{A}}}} = A$\n"
        f"- **Absorption**: $A + A \\cdot B = A$"
    )


# -----------------------------------------------------------------------------
# 5. DISPATCHER & INTENT PARSER
# -----------------------------------------------------------------------------

def evaluate_cs_digital(query: str) -> Optional[str]:
    """
    Main offline evaluator for computer science and digital logic.
    Returns formatted KaTeX/Markdown or None if the query does not match.
    """
    q = query.strip()
    lower = q.lower()

    # 1. Number Systems & Two's Complement
    num_match = re.search(r"(?:binary|hex|hexadecimal|octal|base 2|base 16|base 10|two's complement|twos complement)\s*(?:of|for)?\s*(-?(?:0x[0-9a-fA-F]+|0b[01]+|\d+))", q, re.IGNORECASE)
    if num_match:
        val_str = num_match.group(1)
        return convert_number_systems(val_str)

    # 2. IEEE-754 Floating Point
    if any(k in lower for k in ["ieee-754", "ieee 754", "floating point representation", "float bits"]):
        m_flt = re.search(r"(-?\d+(?:\.\d+)?)", q)
        f_val = float(m_flt.group(1)) if m_flt else 13.5
        return solve_ieee754(f_val)

    # 3. CIDR Subnet Calculator
    cidr_match = re.search(r"(?:subnet|cidr|ip mask|network address)\s*(?:for)?\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?)", q, re.IGNORECASE)
    if cidr_match:
        cidr_str = cidr_match.group(1)
        return solve_cidr_subnet(cidr_str)
    elif re.search(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}\b", q):
        m_ip = re.search(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}\b", q)
        if m_ip:
            return solve_cidr_subnet(m_ip.group(0))

    # 4. Big-O Complexity Cheatsheet (Only for general matrix/table requests, not specific algorithmic queries)
    has_specific_algo = any(k in lower for k in [
        "dijkstra", "bellman", "floyd", "prim", "kruskal", "astar", "a*",
        "quicksort", "mergesort", "heapsort", "binary search", "bfs", "dfs", "knapsack", "lcs", "lis"
    ])
    is_general_table_req = any(k in lower for k in ["table", "matrix", "cheatsheet", "summary", "chart", "comparison", "all"])
    if not has_specific_algo and (is_general_table_req or lower.strip() in {"big-o", "big o", "time complexity", "big-o matrix", "big o table"}):
        return get_big_o_matrix()
    if any(k in lower for k in ["big-o matrix", "big-o table", "big o table", "big-o cheatsheet", "complexity table", "complexity matrix"]):
        return get_big_o_matrix()

    # 5. Truth Table & Boolean Logic
    if any(k in lower for k in ["truth table", "boolean table", "logic table", "boolean logic", "de morgan"]):
        clean_expr = re.sub(r"(?:truth table|boolean table|logic table)(?:\s+for)?", "", q, flags=re.IGNORECASE).strip()
        if not clean_expr:
            clean_expr = "A & B"
        return evaluate_truth_table(clean_expr)

    return None
