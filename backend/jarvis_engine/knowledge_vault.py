"""
J.A.R.V.I.S. Self-Evolving Knowledge Vault
Persistent SQLite + BM25/TF-IDF semantic document indexing and retrieval engine.
Supports PDF ingestion via pypdf, lecture note ingestion, and user-taught concept learning.
"""

import io
import math
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import pypdf
except ImportError:
    pypdf = None


DB_PATH = Path(__file__).resolve().parent.parent / "knowledge_vault.db"


def get_db_connection() -> sqlite3.Connection:
    """Returns a thread-safe SQLite connection configured for WAL mode, busy timeout, and fast queries."""
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.row_factory = sqlite3.Row
    return conn


def init_vault_db() -> None:
    """Initializes tables for documents and indexed knowledge chunks."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vault_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                branch TEXT NOT NULL DEFAULT 'ALL',
                source_type TEXT NOT NULL DEFAULT 'file',
                char_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vault_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER,
                branch TEXT NOT NULL DEFAULT 'ALL',
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doc_id) REFERENCES vault_documents (id) ON DELETE CASCADE
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vault_branch ON vault_chunks(branch);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vault_doc ON vault_chunks(doc_id);")

        # Seed foundational GATE & Engineering concepts if fresh database
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM vault_chunks;")
        if cursor.fetchone()["cnt"] == 0:
            _seed_foundational_concepts(conn)


def _seed_foundational_concepts(conn: sqlite3.Connection) -> None:
    """Seeds foundational multi-branch engineering and GATE exam shortcuts."""
    seeds = [
        # GATE & Math
        ("Laplace Transform of Standard Signals", "MATH",
         "L{1} = 1/s (s>0). L{t^n} = n!/s^(n+1). L{e^(at)} = 1/(s-a). L{sin(wt)} = w/(s^2+w^2). L{cos(wt)} = s/(s^2+w^2). Frequency shift: L{e^(at)*f(t)} = F(s-a). Initial Value Theorem: f(0+) = lim(s->inf) s*F(s). Final Value Theorem: f(inf) = lim(s->0) s*F(s) if poles of s*F(s) in LHP.",
         "laplace, transforms, initial value, final value, gate"),
        ("Eigenvalues and Cayley-Hamilton Theorem", "MATH",
         "Cayley-Hamilton Theorem: Every square matrix A satisfies its own characteristic equation p(A) = 0. Trace(A) = sum of eigenvalues. Det(A) = product of eigenvalues. Eigenvalues of triangular matrix are diagonal elements. If lambda is eigenvalue of A, lambda^k is eigenvalue of A^k.",
         "eigenvalues, matrix, cayley-hamilton, linear algebra"),
        # ECE & EE
        ("NE555 Timer Pinout and Astable Multivibrator", "ECE",
         "Pin 1: GND. Pin 2: Trigger (Active Low < Vcc/3). Pin 3: Output. Pin 4: Reset (Active Low). Pin 5: Control Voltage (0.01uF capacitor to ground). Pin 6: Threshold (> 2Vcc/3). Pin 7: Discharge. Pin 8: Vcc (+4.5V to +16V). Frequency: f = 1.44/((R1 + 2*R2)*C). Duty Cycle = (R1 + R2)/(R1 + 2*R2) * 100%.",
         "ne555, 555 timer, pinout, astable, frequency, duty cycle"),
        ("Three-Phase Power and Star-Delta Relations", "EE",
         "Star (Y) Connection: V_L = sqrt(3) * V_ph (leads by 30 deg), I_L = I_ph. Delta (D) Connection: V_L = V_ph, I_L = sqrt(3) * I_ph (lags by 30 deg). Total Active Power: P = sqrt(3) * V_L * I_L * cos(phi) = 3 * V_ph * I_ph * cos(phi). Reactive Power: Q = sqrt(3) * V_L * I_L * sin(phi). Apparent Power: S = sqrt(3) * V_L * I_L.",
         "three phase, star delta, power, power factor, ee, electrical"),
        # MECH & AERO
        ("Beam Deflection and Bending Stress Formulas", "MECH",
         "Bending formula: sigma / y = M / I = E / R. Maximum bending stress: sigma_max = M_max / Z where Z = I / y_max is Section Modulus. Cantilever with end load P: delta_max = P*L^3 / (3*E*I), M_max = P*L. Simply supported beam with center load P: delta_max = P*L^3 / (48*E*I), M_max = P*L / 4.",
         "beam deflection, bending stress, cantilever, simply supported, mechanical"),
        ("Carnot and Rankine Cycle Thermal Efficiencies", "MECH",
         "Carnot efficiency: eta_carnot = 1 - T_C / T_H (temperatures in Kelvin). Rankine Cycle: eta_rankine = (W_turbine - W_pump) / Q_in = (h1 - h2 - (h4 - h3)) / (h1 - h4). Specific heat ratio gamma for air is 1.4.",
         "carnot, rankine, thermodynamics, efficiency, heat engine"),
        # CIVIL
        ("Darcy's Law and Soil Mechanics Index Properties", "CIVIL",
         "Darcy's Law: Q = k * i * A where k is hydraulic conductivity, i = delta_h / L is hydraulic gradient. Void Ratio: e = V_v / V_s. Porosity: n = V_v / V = e / (1 + e). Degree of Saturation: S = V_w / V_v. Water content w = M_w / M_s. Relation: S * e = w * G.",
         "darcy, soil mechanics, porosity, void ratio, hydraulics, civil"),
        ("Manning's Formula for Open Channel Flow", "CIVIL",
         "Manning's equation for uniform open channel flow: v = (1 / n) * R_h^(2/3) * S^(1/2) in SI units, where v is mean velocity (m/s), n is Manning's roughness coefficient, R_h = A / P is Hydraulic Radius, P is wetted perimeter, S is energy slope.",
         "manning, open channel, hydraulic radius, flow velocity, civil"),
        # CSE
        ("Big-O Algorithmic Complexity Cheatsheet", "CSE",
         "Array: Access O(1), Search O(n), Insert O(n), Delete O(n). Hash Table: Search/Insert/Delete average O(1), worst O(n). BST: O(log n) avg, O(n) worst. AVL / Red-Black Tree: O(log n) guaranteed. Sorting: Quicksort O(n log n) avg, O(n^2) worst, space O(log n). Mergesort O(n log n) best/avg/worst, space O(n), stable. Heapsort O(n log n), space O(1), unstable.",
         "big-o, complexity, sorting, data structures, cse, gate"),
        ("IPv4 Subnetting and CIDR Reference", "CSE",
         "Subnet Mask /24: 255.255.255.0 (256 addresses, 254 usable hosts). /28: 255.255.255.240 (16 addresses, 14 usable hosts). Number of hosts = 2^(32 - prefix) - 2. Network address has all host bits 0, Broadcast has all host bits 1. Private ranges: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16.",
         "cidr, subnet, ipv4, network address, broadcast, cse, gate"),
    ]

    for title, branch, content, tags in seeds:
        conn.execute("""
            INSERT INTO vault_chunks (doc_id, branch, title, content, tags)
            VALUES (NULL, ?, ?, ?, ?);
        """, (branch, title, content, tags))


# -----------------------------------------------------------------------------
# 1. DOCUMENT PARSING & CHUNKING
# -----------------------------------------------------------------------------

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extracts text content from PDF bytes using pypdf."""
    if pypdf is None:
        raise RuntimeError("pypdf is not installed. Please install pypdf to ingest PDFs.")

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    pages_text = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages_text.append(f"--- Page {idx + 1} ---\n{text.strip()}")
    return "\n\n".join(pages_text)


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[Tuple[str, str]]:
    """
    Splits text into coherent chunks, detecting headings where available.
    Returns list of (title, chunk_content).
    """
    chunks: List[Tuple[str, str]] = []
    # If text has markdown headings, split by headings
    sections = re.split(r"(?:^|\n)(#{1,4}\s+[^\n]+)", text)
    if len(sections) > 2:
        current_title = "General Concept"
        for i in range(1, len(sections), 2):
            heading = sections[i].strip("# ").strip()
            body = sections[i + 1].strip() if i + 1 < len(sections) else ""
            if len(body) > chunk_size:
                # Sub-chunk large body
                sub_chunks = [body[j:j+chunk_size] for j in range(0, len(body), chunk_size - overlap)]
                for sub_idx, sc in enumerate(sub_chunks):
                    chunks.append((f"{heading} (Part {sub_idx + 1})", sc.strip()))
            elif body:
                chunks.append((heading, body))
        if chunks:
            return chunks

    # Fallback sliding window
    words = text.split()
    if not words:
        return []

    words_per_chunk = max(40, chunk_size // 6)
    overlap_words = max(10, overlap // 6)

    for i in range(0, len(words), words_per_chunk - overlap_words):
        chunk_words = words[i:i + words_per_chunk]
        chunk_str = " ".join(chunk_words)
        # Infer title from first 6 words
        title = " ".join(chunk_words[:6]) + ("..." if len(chunk_words) > 6 else "")
        chunks.append((title, chunk_str))
        if i + words_per_chunk >= len(words):
            break

    return chunks


# -----------------------------------------------------------------------------
# 2. INGESTION FUNCTIONS
# -----------------------------------------------------------------------------

def ingest_document(filename: str, file_bytes: bytes, branch: str = "ALL") -> Dict[str, Any]:
    """Ingests a file (PDF, Markdown, or plain text) into the Knowledge Vault."""
    init_vault_db()
    lower_name = filename.lower()
    branch = branch.upper().strip()

    if lower_name.endswith(".pdf"):
        full_text = extract_text_from_pdf(file_bytes)
        source_type = "pdf"
    else:
        full_text = file_bytes.decode("utf-8", errors="replace")
        source_type = "text"

    if not full_text.strip():
        return {"status": "error", "message": f"No text could be extracted from {filename}."}

    chunks = chunk_text(full_text)
    if not chunks:
        chunks = [(Path(filename).stem, full_text)]

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO vault_documents (filename, branch, source_type, char_count)
            VALUES (?, ?, ?, ?);
        """, (filename, branch, source_type, len(full_text)))
        doc_id = cursor.lastrowid

        for title, content in chunks:
            # Extract tags from content
            words = set(re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", content.lower()))
            tags = ", ".join(list(words)[:15])
            conn.execute("""
                INSERT INTO vault_chunks (doc_id, branch, title, content, tags)
                VALUES (?, ?, ?, ?, ?);
            """, (doc_id, branch, title, content, tags))

    return {
        "status": "success",
        "doc_id": doc_id,
        "filename": filename,
        "branch": branch,
        "chunks_indexed": len(chunks),
        "char_count": len(full_text),
    }


def ingest_user_taught_concept(text: str, branch: str = "ALL", title: Optional[str] = None) -> Dict[str, Any]:
    """Ingests a user-taught formula or correction (e.g. 'Learn: ...' or message feedback)."""
    init_vault_db()
    clean = text.strip()
    clean = re.sub(r"^(?:learn|remember|teach|note|vault):\s*", "", clean, flags=re.IGNORECASE).strip()

    if not clean:
        return {"status": "error", "message": "Concept text is empty."}

    inferred_title = title or ("User Formula: " + " ".join(clean.split()[:5]) + "...")
    words = set(re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", clean.lower()))
    tags = ", ".join(list(words)[:15])

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO vault_chunks (doc_id, branch, title, content, tags)
            VALUES (NULL, ?, ?, ?, ?);
        """, (branch.upper().strip(), inferred_title, clean, tags))
        chunk_id = cursor.lastrowid

    return {
        "status": "success",
        "chunk_id": chunk_id,
        "title": inferred_title,
        "branch": branch,
        "message": "Concept successfully preserved in J.A.R.V.I.S. Knowledge Vault.",
    }


# -----------------------------------------------------------------------------
# 3. BM25 / TF-IDF RETRIEVAL ENGINE
# -----------------------------------------------------------------------------

def tokenize(text: str) -> List[str]:
    """Splits text into normalized alphanumeric query tokens."""
    return [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text)]


def search_vault(query: str, branch: Optional[str] = None, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    BM25 rank-ordered semantic retrieval over knowledge vault chunks.
    Filters by engineering branch if specified.
    """
    init_vault_db()
    tokens = tokenize(query)
    if not tokens:
        return []

    with get_db_connection() as conn:
        cursor = conn.cursor()
        if branch and branch.upper() != "ALL":
            cursor.execute("""
                SELECT id, doc_id, branch, title, content, tags
                FROM vault_chunks
                WHERE branch = ? OR branch = 'ALL';
            """, (branch.upper(),))
        else:
            cursor.execute("SELECT id, doc_id, branch, title, content, tags FROM vault_chunks;")

        all_rows = cursor.fetchall()
        if not all_rows:
            return []

        # Total documents in corpus
        N = len(all_rows)
        doc_tokens_list: List[List[str]] = []
        doc_lengths: List[int] = []

        # Inverted index: term -> list of doc indices containing term
        term_df: Dict[str, int] = {}

        for row in all_rows:
            combined = f"{row['title']} {row['content']} {row['tags']}"
            dtoks = tokenize(combined)
            doc_tokens_list.append(dtoks)
            doc_lengths.append(len(dtoks))
            unique_terms = set(dtoks)
            for t in unique_terms:
                term_df[t] = term_df.get(t, 0) + 1

        avgdl = sum(doc_lengths) / float(N) if N > 0 else 1.0

        # BM25 Parameters
        k1 = 1.5
        b = 0.75

        scores: List[Tuple[float, int]] = []
        for doc_idx, dtoks in enumerate(doc_tokens_list):
            doc_len = doc_lengths[doc_idx]
            # Term frequencies in this document
            tf_map: Dict[str, int] = {}
            for t in dtoks:
                tf_map[t] = tf_map.get(t, 0) + 1

            score = 0.0
            for q_term in tokens:
                if q_term in tf_map:
                    f = tf_map[q_term]
                    df = term_df.get(q_term, 0)
                    # Lucene / BM25 IDF
                    idf = math.log(1.0 + (N - df + 0.5) / (df + 0.5))
                    term_score = idf * (f * (k1 + 1.0)) / (f + k1 * (1.0 - b + b * (doc_len / avgdl)))
                    score += term_score

            if score > 0.05:
                scores.append((score, doc_idx))

        scores.sort(key=lambda x: x[0], reverse=True)
        top_results = scores[:top_k]

        results = []
        for score, doc_idx in top_results:
            row = all_rows[doc_idx]
            results.append({
                "id": row["id"],
                "branch": row["branch"],
                "title": row["title"],
                "content": row["content"],
                "tags": row["tags"],
                "score": round(score, 3),
            })
        return results


def get_vault_stats() -> Dict[str, Any]:
    """Returns database telemetry metrics for the Knowledge Vault."""
    init_vault_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total_chunks FROM vault_chunks;")
        total_chunks = cursor.fetchone()["total_chunks"]

        cursor.execute("SELECT COUNT(*) AS total_docs FROM vault_documents;")
        total_docs = cursor.fetchone()["total_docs"]

        cursor.execute("""
            SELECT branch, COUNT(*) AS count
            FROM vault_chunks
            GROUP BY branch
            ORDER BY count DESC;
        """)
        branch_counts = {r["branch"]: r["count"] for r in cursor.fetchall()}

        cursor.execute("""
            SELECT id, filename, branch, created_at
            FROM vault_documents
            ORDER BY id DESC LIMIT 5;
        """)
        recent_docs = [dict(r) for r in cursor.fetchall()]

    return {
        "total_chunks": total_chunks,
        "total_documents": total_docs,
        "branch_breakdown": branch_counts,
        "recent_documents": recent_docs,
    }
