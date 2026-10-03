import time
import textwrap
import streamlit as st
from google import genai
from google.genai import types

from models import MODELS, get_model
from providers import ask_provider

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    SUMMARY_REQUEST_PROMPT,
)


# -----------------------------
# Page configuration
# -----------------------------

st.set_page_config(
    page_title="CircuitSnap",
    page_icon="🔧",
    layout="centered",
)


# -----------------------------
# UI theme (CSS only — no backend logic lives here)
#
# NOTE on selectors: a few rules below target Streamlit's internal
# data-testid attributes (e.g. [data-testid="stChatMessage"]) purely as
# styling hooks. These are not a public/stable Streamlit API — if a
# future Streamlit version renames these attributes, the affected rule
# will simply stop applying (the app keeps working, just less styled).
# Each such selector is kept isolated below so it's easy to find and
# update if that happens.
# -----------------------------

CIRCUITSNAP_CSS = """
<style>

/* =========================================================
   CircuitSnap — AI Electronics Workbench
   ========================================================= */

:root {
    --cs-bg: #070B10;
    --cs-bg-soft: #0B1118;
    --cs-surface: #101821;
    --cs-surface-2: #151F2A;
    --cs-surface-3: #1A2632;

    --cs-border: #24313D;
    --cs-border-bright: #304454;

    --cs-text: #F5F7FA;
    --cs-text-primary: #F5F7FA;

    --cs-text-soft: #AAB6C2;
    --cs-text-secondary: #AAB6C2;

--cs-text-muted: #6F7E8C;
--cs-surface-elev: #1A2632;

    --cs-cyan: #38BDF8;
    --cs-cyan-bright: #67D5FF;
    --cs-green: #22C55E;
    --cs-orange: #F59E0B;

    --cs-radius-sm: 8px;
    --cs-radius-md: 12px;
    --cs-radius-lg: 18px;
}

/* =========================================================
   Base
   ========================================================= */

.stApp {
    background:
        radial-gradient(
            circle at 50% -15%,
            rgba(56, 189, 248, 0.075),
            transparent 34%
        ),
        linear-gradient(
            180deg,
            #080D13 0%,
            #070B10 45%,
            #060A0F 100%
        );

    overflow-x: hidden;
}

.block-container {
    width: calc(100% - 32px);
    max-width: 820px;

    padding-top: 1.2rem;
    padding-bottom: 7rem;

    margin: 0 auto;
}

body,
.stApp,
p,
span,
div,
li {
    color: var(--cs-text);
}

/* =========================================================
   CircuitSnap — Premium Header
   ========================================================= */

.cs-header {
    position: relative;

    display: flex;
    align-items: center;
    justify-content: space-between;

    min-height: 68px;

    padding: 14px 20px;

    margin-bottom: 1rem;

    background:
        linear-gradient(
            135deg,
            rgba(19, 32, 43, 0.98),
            rgba(8, 16, 23, 0.98)
        );

    border: 1px solid rgba(56, 189, 248, 0.16);

    border-radius: 16px;

    box-shadow:
        0 16px 40px rgba(0, 0, 0, 0.30),
        inset 0 1px 0 rgba(255, 255, 255, 0.045);

}


/* subtle cyan light across the top */

.cs-header::before {
    content: "";

    position: absolute;

    top: 0;
    left: 8%;

    width: 84%;
    height: 1px;

    background:
        linear-gradient(
            90deg,
            transparent,
            rgba(56, 189, 248, 0.55),
            transparent
        );

    opacity: 0.75;
}


/* small cyan accent at bottom-left */

.cs-header::after {
    content: "";

    position: absolute;

    left: 20px;
    bottom: 0;

    width: 90px;
    height: 2px;

    background:
        linear-gradient(
            90deg,
            var(--cs-cyan),
            rgba(56, 189, 248, 0)
        );

    box-shadow:
        0 0 14px rgba(56, 189, 248, 0.55);
}


/* =========================================================
   Left side
   ========================================================= */

.cs-header-left {
    display: flex;
    align-items: center;

    gap: 13px;

    min-width: 0;
}


/* Logo */

.cs-logo {
    width: 42px;
    height: 42px;

    flex-shrink: 0;

    padding: 5px;

    border-radius: 11px;

    background:
        linear-gradient(
            145deg,
            rgba(56, 189, 248, 0.13),
            rgba(56, 189, 248, 0.035)
        );

    border: 1px solid rgba(56, 189, 248, 0.18);

    box-shadow:
        0 0 18px rgba(56, 189, 248, 0.07);
}


/* Brand title */

.cs-header-title {
    font-size: 1.08rem;

    font-weight: 750;

    letter-spacing: -0.02em;

    line-height: 1.15;

    color: var(--cs-text);
}


/* Subtitle */

.cs-header-subtitle {
    margin-top: 5px;

    font-size: 0.70rem;

    color: var(--cs-text-muted);

    line-height: 1.2;

    white-space: nowrap;
}


/* =========================================================
   Right status
   ========================================================= */

.cs-status {
    display: flex;

    align-items: center;

    gap: 7px;

    flex-shrink: 0;

    padding: 7px 11px;

    font-size: 0.68rem;

    font-weight: 600;

    color: #B8C5D0;

    white-space: nowrap;

    background:
        rgba(34, 197, 94, 0.055);

    border: 1px solid rgba(34, 197, 94, 0.16);

    border-radius: 999px;

    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.025);
}


.cs-status-dot {
    width: 7px;
    height: 7px;

    flex-shrink: 0;

    border-radius: 50%;

    background: var(--cs-green);

    box-shadow:
        0 0 0 3px rgba(34, 197, 94, 0.08),
        0 0 12px rgba(34, 197, 94, 0.50);
}

/* =========================================================
   Animations
   ========================================================= */

@keyframes cs-fade-up {
    from {
        opacity: 0;
        transform: translateY(8px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes cs-glow {
    0%, 100% {
        opacity: 0.55;
    }

    50% {
        opacity: 1;
    }
}

@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation: none !important;
        transition: none !important;
    }
}

/* =========================================================
   Hero / Empty State
   ========================================================= */

.cs-hero {
    position: relative;
    text-align: center;

    padding: 2.0rem 1rem 1.15rem;

    animation: cs-fade-up 300ms ease-out;
}

.cs-hero::before {
    content: "";
    display: block;

    width: 46px;
    height: 2px;

    margin: 0 auto 1.05rem;

    background: var(--cs-cyan);

    box-shadow:
        0 0 12px rgba(56, 189, 248, 0.65);

    animation: cs-glow 2.5s ease-in-out infinite;
}

.cs-hero h1 {
    margin: 0 0 0.45rem;

    font-size: 2rem;
    font-weight: 780;
    letter-spacing: -0.035em;

    background: linear-gradient(
        90deg,
        #F5F7FA,
        #C9EFFF
    );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.cs-hero p {
    max-width: 620px;

    margin: 0 auto 1.25rem;

    font-size: 0.91rem;
    line-height: 1.5;

    color: var(--cs-text-soft);
}

/* -------- AI assistant home -------- */

.cs-home {
    max-width: 680px;
    margin: 0 auto;
    padding: 3.5rem 0 1rem;
    text-align: center;
    animation: cs-fade-in-up 320ms ease-out;
}

.cs-home-icon {
    width: 52px;
    height: 52px;
    margin: 0 auto 1.1rem;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 16px;

    background:
        linear-gradient(
            135deg,
            rgba(56, 189, 248, 0.16),
            rgba(34, 211, 238, 0.06)
        );

    border: 1px solid rgba(56, 189, 248, 0.25);

    font-size: 1.45rem;

    box-shadow:
        0 0 30px rgba(56, 189, 248, 0.08);
}

.cs-home h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.035em;
    color: var(--cs-text-primary);
}

.cs-home-subtitle {
    margin: 0.65rem 0 2rem;

    color: var(--cs-text-secondary);

    font-size: 0.98rem;
    line-height: 1.5;
}

.cs-prompt-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;

    max-width: 590px;
    margin: 0 auto;
}

.cs-prompt-card {
    display: flex;
    align-items: center;

    gap: 12px;

    padding: 14px;

    text-align: left;

    background: rgba(21, 27, 35, 0.72);

    border: 1px solid var(--cs-border);

    border-radius: 12px;

    cursor: default;

    transition:
        border-color 160ms ease,
        background 160ms ease,
        transform 160ms ease;
}

.cs-prompt-card:hover {
    background: rgba(27, 34, 44, 0.95);

    border-color: rgba(56, 189, 248, 0.38);

    transform: translateY(-1px);
}

.cs-prompt-card,
.cs-prompt-card:hover,
.cs-prompt-card:visited,
.cs-prompt-card:active {
    text-decoration: none !important;
    color: inherit !important;
    cursor: pointer !important;
}

.cs-prompt-icon {
    width: 34px;
    height: 34px;

    flex-shrink: 0;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 9px;

    background: var(--cs-surface-elev);

    font-size: 1rem;
}

.cs-prompt-card strong {
    display: block;

    color: var(--cs-text-primary);

    font-size: 0.82rem;
    font-weight: 600;

    margin-bottom: 3px;
}

.cs-prompt-card span {
    display: block;

    color: var(--cs-text-muted);

    font-size: 0.72rem;

    line-height: 1.3;
}

.cs-home-hint {
    margin-top: 1.35rem;

    color: var(--cs-text-muted);

    font-size: 0.72rem;
}


/* Mobile */

@media (max-width: 640px) {

    .cs-home {
        padding-top: 2rem;
    }

    .cs-home h1 {
        font-size: 1.65rem;
    }

    .cs-prompt-grid {
       grid-template-columns: 1fr 1fr;
    }

}

/* =========================================================
   Electronics category cards
   ========================================================= */

.cs-chip-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);

    gap: 9px;

    margin: 0 auto 1rem;

    max-width: 650px;
}

.cs-chip {
    position: relative;

    display: flex;
    align-items: center;
    justify-content: center;

    min-height: 42px;

    padding: 8px 10px;

    font-size: 0.76rem;
    font-weight: 600;

    color: var(--cs-text-soft);

    background:
        linear-gradient(
            145deg,
            rgba(21, 31, 42, 0.95),
            rgba(13, 19, 26, 0.95)
        );

    border: 1px solid var(--cs-border);
    border-radius: var(--cs-radius-md);

    transition:
        border-color 160ms ease,
        background 160ms ease,
        transform 160ms ease;
}

.cs-chip::before {
    content: "•";

    margin-right: 6px;

    color: var(--cs-cyan);
}

.cs-chip:hover {
    border-color: rgba(56, 189, 248, 0.55);

    background:
        linear-gradient(
            145deg,
            rgba(24, 42, 54, 0.98),
            rgba(15, 25, 34, 0.98)
        );

    transform: translateY(-2px);
}

.cs-hero-hint {
    font-size: 0.72rem;
    color: var(--cs-text-muted);
}

/* =========================================================
   Onboarding
   ========================================================= */

.cs-onboard-wrap {
    text-align: center;
    padding: 1.6rem 1rem 0.9rem;

    animation: cs-fade-up 300ms ease-out;
}

.cs-onboard-wrap h1 {
    margin: 0 0 0.35rem;

    font-size: 2rem;
    font-weight: 780;
    letter-spacing: -0.035em;
}

.cs-onboard-wrap p {
    margin: 0;

    font-size: 0.88rem;
    color: var(--cs-text-soft);
}

/* Onboarding form */

div[data-testid="stForm"] {
    max-width: 620px;

    margin: 0 auto;

    padding: 1.35rem;

    background:
        linear-gradient(
            145deg,
            rgba(18, 28, 38, 0.98),
            rgba(11, 17, 24, 0.98)
        );

    border: 1px solid var(--cs-border);
    border-radius: var(--cs-radius-lg);

    box-shadow:
        0 20px 50px rgba(0, 0, 0, 0.22),
        inset 0 1px 0 rgba(255, 255, 255, 0.025);
}

/* =========================================================
   Model selector
   ========================================================= */

div[data-testid="stSelectbox"] {
    margin-top: 0.4rem;
    margin-bottom: 0.25rem;
}

div[data-testid="stSelectbox"] label {
    font-size: 0.68rem;
    font-weight: 700;

    color: var(--cs-cyan);

    text-transform: uppercase;
    letter-spacing: 0.09em;

    margin-bottom: 0.3rem;
}

div[data-testid="stSelectbox"] > div > div {
    min-height: 2.55rem;

    background: var(--cs-surface);
    border-color: var(--cs-border);
    border-radius: var(--cs-radius-md);
}

div[data-testid="stSelectbox"] > div > div:hover {
    border-color: var(--cs-border-bright);
}

div[data-testid="stCaptionContainer"] {
    margin-top: -0.1rem;
    margin-bottom: 0.45rem;

    color: var(--cs-text-muted);
}

div[data-testid="stCaptionContainer"] p {
    font-size: 0.68rem !important;
    color: var(--cs-text-soft) !important;
    font-weight: 500 !important;
}

/* =========================================================
   Chat messages
   ========================================================= */

div[data-testid="stChatMessage"] {
    background:
        linear-gradient(
            145deg,
            rgba(17, 26, 35, 0.96),
            rgba(13, 20, 27, 0.96)
        );

    border: 1px solid var(--cs-border);
    border-radius: var(--cs-radius-lg);

    padding: 0.85rem 1rem;
    margin-bottom: 0.65rem;

    animation: cs-fade-up 220ms ease-out;
}

div[data-testid="stChatMessage"] p {
    color: var(--cs-text-soft);
    line-height: 1.55;
}

div[data-testid="stChatMessage"] strong {
    color: var(--cs-text);
}

div[data-testid="stChatMessage"] h1,
div[data-testid="stChatMessage"] h2,
div[data-testid="stChatMessage"] h3 {
    font-size: 0.9rem;
    color: var(--cs-cyan);

    border-bottom: 1px solid var(--cs-border);

    padding-bottom: 0.3rem;
    margin: 0.9rem 0 0.5rem;
}

div[data-testid="stChatMessage"] code {
    background: var(--cs-surface-3);
    border: 1px solid var(--cs-border);

    border-radius: 5px;

    padding: 0.1rem 0.35rem;

    color: var(--cs-cyan-bright);
}

div[data-testid="stChatMessage"] li {
    color: var(--cs-text-soft);
    margin-bottom: 0.25rem;
}

/* =========================================================
   Uploaded image
   ========================================================= */

div[data-testid="stChatMessage"] div[data-testid="stImage"] img {
    border-radius: var(--cs-radius-md);
    border: 1px solid var(--cs-border);
}

/* =========================================================
   Chat input
   ========================================================= */

div[data-testid="stChatInput"] {
    background:
        linear-gradient(
            145deg,
            rgba(22, 33, 44, 0.98),
            rgba(14, 22, 30, 0.98)
        );

    border: 1px solid var(--cs-border-bright);
    border-radius: 15px;

    box-shadow:
        0 12px 30px rgba(0, 0, 0, 0.28);

    transition:
        border-color 160ms ease,
        box-shadow 160ms ease;
}

div[data-testid="stChatInput"]:focus-within {
    border-color: var(--cs-cyan);

    box-shadow:
        0 0 0 3px rgba(56, 189, 248, 0.10),
        0 12px 30px rgba(0, 0, 0, 0.30);
}

div[data-testid="stChatInput"] textarea {
    color: var(--cs-text) !important;
}



/* =========================================================
   Active quick-action mode
   ========================================================= */

.cs-active-mode {
    position: relative !important;

    display: flex !important;

    align-items: center !important;
    gap: 7px !important;

    padding: 7px 12px !important;

    background: rgba(15, 23, 32, 0.94) !important;

    border: 1px solid rgba(56, 189, 248, 0.22) !important;
    border-radius: 10px !important;

    color: var(--cs-text-soft) !important;

    font-size: 0.72rem !important;
    line-height: 1 !important;

    box-shadow:
        0 4px 16px rgba(0, 0, 0, 0.24) !important;

    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}

.cs-active-mode strong {
    color: var(--cs-text) !important;
    font-weight: 600 !important;
}

.cs-active-mode-dot {
    width: 6px !important;
    height: 6px !important;

    border-radius: 50% !important;

    background: var(--cs-cyan) !important;

    box-shadow:
        0 0 8px rgba(56, 189, 248, 0.55) !important;

    flex-shrink: 0 !important;
}


/* =========================================================
   Buttons
   ========================================================= */

.stButton > button,
button[kind="formSubmit"] {
    background: var(--cs-surface) !important;
    color: var(--cs-text) !important;

    border: 1px solid var(--cs-border) !important;
    border-radius: var(--cs-radius-md) !important;

    font-weight: 600;

    padding: 0.65rem 1rem;

    transition:
        border-color 160ms ease,
        background 160ms ease,
        transform 160ms ease,
        box-shadow 160ms ease;
}

.stButton > button:hover,
button[kind="formSubmit"]:hover {
    background: var(--cs-surface-2) !important;
    border-color: rgba(56, 189, 248, 0.38) !important;

    transform: translateY(-1px);

    box-shadow:
        0 6px 18px rgba(0, 0, 0, 0.22);
}

/* =========================================================
   Quick action cards
   ========================================================= */

.stButton > button {
    white-space: pre-line !important;
    text-align: left !important;
    justify-content: flex-start !important;
    line-height: 1.45 !important;
}

.stButton > button p {
    width: 100% !important;
    white-space: pre-line !important;
    text-align: left !important;
    line-height: 1.45 !important;
}

.stButton > button strong {
    display: inline;
}
.stButton > button > div {
    width: 100% !important;
    text-align: left !important;
}

/* =========================================================
   Name input
   ========================================================= */

div[data-testid="stTextInput"] input {
    background: var(--cs-surface-2);

    border: 1px solid var(--cs-border);
    border-radius: var(--cs-radius-sm);

    color: var(--cs-text);
}

div[data-testid="stTextInput"] input:focus {
    border-color: var(--cs-cyan);

    box-shadow:
        0 0 0 3px rgba(56, 189, 248, 0.006);
}

/* =========================================================
   Hide Streamlit chrome
   ========================================================= */

#MainMenu,
footer {
    visibility: hidden;
}

/* =========================================================
   RESPONSIVE DESIGN
   ========================================================= */

/* ---------- Tablet ---------- */

@media (max-width: 900px) {

    .block-container {
        max-width: 92%;
        padding-top: 4rem;
        padding-bottom: 6rem;
    }

    .cs-header {
        min-height: 72px;
        padding: 14px 16px;

    }

    .cs-hero {
        padding-top: 1.7rem;
    }

    .cs-hero h1 {
        font-size: 1.8rem;
    }

    .cs-chip-row {
        grid-template-columns: repeat(2, 1fr);
        max-width: 560px;
    }

    div[data-testid="stForm"] {
        max-width: 100%;
    }
}

/* ---------- Desktop: 901–1440px ---------- */

@media (min-width: 901px) and (max-width: 1440px) {

    .block-container {
        width: calc(100% - 48px);
        max-width: 820px;

        padding-top: 2.8rem;
        padding-bottom: 7rem;
    }

    .cs-header {
        min-height: 68px;
        padding: 14px 20px;
    }

    .cs-hero {
        padding: 2rem 1rem 1.15rem;
    }

    .cs-hero h1 {
        font-size: 2rem;
    }

    .cs-chip-row {
        grid-template-columns: repeat(4, 1fr);
        max-width: 650px;
    }

    .cs-home {
        max-width: 680px;
        padding-top: 3.5rem;
    }

    .cs-prompt-grid {
        grid-template-columns: repeat(2, 1fr);
        max-width: 590px;
    }

    div[data-testid="stForm"] {
        max-width: 620px;
    }

    div[data-testid="stChatMessage"] {
        padding: 0.85rem 1rem;
    }

    div[data-testid="stChatInput"] {
        border-radius: 15px;
    }
}


/* ---------- Large Desktop: >1440px ---------- */

@media (min-width: 1441px) {

    .block-container {
        width: 100%;
        max-width: 860px;

        padding-top: 1.8rem;
        padding-bottom: 8rem;
    }

    .cs-header {
        min-height: 72px;
        padding: 16px 22px;
        margin-bottom: 1.2rem;
    }

    .cs-home {
        max-width: 720px;
        padding-top: 4.5rem;
    }

    .cs-prompt-grid {
        max-width: 620px;
        gap: 12px;
    }

    .cs-prompt-card {
        padding: 16px;
    }

    .cs-hero {
        padding-top: 2.5rem;
    }
}


/* ---------- Mobile: 381-600px ---------- */

@media (min-width: 381px) and (max-width: 600px) {

    .block-container {
        width: calc(100% - 24px);
        max-width: none;

        padding-left: 0;
        padding-right: 0;

        padding-top: 2.8rem;
        padding-bottom: 6rem;
    }

    /* Header */

    .cs-header {
        min-height: 58px;

        padding: 9px 11px;
        margin-bottom: 0.45rem;

        border-radius: 13px;
    }

    .cs-header-left {
        gap: 8px;
    }

    .cs-logo {
        width: 34px;
        height: 34px;
        padding: 4px;
    }

    .cs-header-title {
        font-size: 0.92rem;
    }

    .cs-header-subtitle {
        max-width: 230px;

        font-size: 0.60rem;

        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .cs-status {
        padding: 6px 8px;

        font-size: 0;
        gap: 0;
    }

    .cs-status-dot {
        width: 7px;
        height: 7px;
    }


    /* Hero */

    .cs-hero {
        padding: 1.35rem 0.25rem 0.8rem;
    }

    .cs-hero::before {
        width: 34px;
        margin-bottom: 0.75rem;
    }

    .cs-hero h1 {
        font-size: clamp(1.35rem, 6vw, 1.65rem);
        line-height: 1.2;
    }

    .cs-hero p {
        max-width: 100%;

        font-size: 0.78rem;
        line-height: 1.45;

        margin-bottom: 1rem;
    }


    /* Electronics cards */

    .cs-chip-row {
        grid-template-columns: repeat(2, minmax(0, 1fr));

        width: 100%;
        max-width: none;

        gap: 7px;
        margin-bottom: 0.8rem;
    }

    .cs-chip {
        min-height: 38px;

        padding: 7px 5px;

        font-size: 0.68rem;

        border-radius: 10px;
    }

    .cs-chip::before {
        margin-right: 4px;
    }

    .cs-hero-hint {
        font-size: 0.65rem;
    }


    /* Home */

    .cs-home {
        width: 100%;
        max-width: none;

        padding: 1.5rem 0 0.7rem;
    }

    .cs-home-icon {
        width: 44px;
        height: 44px;

        margin-bottom: 0.8rem;

        border-radius: 13px;

        font-size: 1.2rem;
    }

    .cs-home h1 {
        font-size: 1.55rem;
        line-height: 1.2;
    }

    .cs-home-subtitle {
        margin-bottom: 1.15rem;

        font-size: 0.80rem;
        line-height: 1.45;
    }

    .cs-prompt-grid {
        grid-template-columns: 1fr;

        width: 100%;
        max-width: none;

        gap: 8px;
    }

    .cs-prompt-card {
        width: 100%;
        min-height: 58px;

        padding: 11px;
    }

    .cs-prompt-card strong {
        font-size: 0.76rem;
    }

    .cs-prompt-card span {
        font-size: 0.66rem;
    }

    .cs-prompt-icon {
        width: 32px;
        height: 32px;

        flex-shrink: 0;

        font-size: 0.92rem;
    }

    .cs-home-hint {
        margin-top: 0.9rem;

        font-size: 0.64rem;
    }


    /* Onboarding */

    .cs-onboard-wrap {
        padding: 1.1rem 0.25rem 0.7rem;
    }

    .cs-onboard-wrap h1 {
        font-size: 1.55rem;
        line-height: 1.2;
    }

    .cs-onboard-wrap p {
        font-size: 0.78rem;
    }

    div[data-testid="stForm"] {
        width: 100%;
        max-width: none;

        padding: 1rem;

        border-radius: 14px;
    }


    /* Model selector */

    div[data-testid="stSelectbox"] {
        width: 100% !important;
        margin-top: 0.3rem;
        margin-bottom: 0.35rem;
    }

    div[data-testid="stSelectbox"] > div > div {
        min-height: 2.25rem;

        font-size: 0.72rem;
    }


    /* Active mode */

    .cs-active-mode {
        width: fit-content;
        max-width: 100%;

        margin: 0 auto 0.45rem !important;

        padding: 6px 9px !important;

        font-size: 0.66rem !important;
    }


    /* Chat messages */

    div[data-testid="stChatMessage"] {
        padding: 0.72rem 0.78rem;

        border-radius: 13px;
        margin-bottom: 0.55rem;
    }

    div[data-testid="stChatMessage"] p {
        font-size: 0.82rem;
        line-height: 1.5;
    }


    /* Chat input */

    div[data-testid="stChatInput"] {
        width: 100%;
        border-radius: 13px;
    }

    div[data-testid="stChatInput"] textarea {
        font-size: 0.80rem !important;
    }


    /* Buttons */

    .stButton > button,
    button[kind="formSubmit"] {
        width: 100%;
        min-height: 2.45rem;
    }
}


/* ---------- Small phones: <=380px ---------- */

@media (max-width: 380px) {

    .block-container {
        width: calc(100% - 18px);
        max-width: none;

        padding-left: 0;
        padding-right: 0;

        padding-top: 2.8rem;
        padding-bottom: 5.8rem;
    }


    /* Header */

    .cs-header {
        min-height: 54px;

        padding: 8px 9px;

        border-radius: 12px;
    }

    .cs-logo {
        width: 31px;
        height: 31px;
        padding: 3px;
    }

    .cs-header-title {
        font-size: 0.86rem;
    }

    .cs-header-subtitle {
        display: none;
    }

    .cs-status {
        padding: 5px 6px;
    }


    /* Home */

    .cs-home {
        padding-top: 1.25rem;
    }

    .cs-home-icon {
        width: 40px;
        height: 40px;

        margin-bottom: 0.7rem;

        border-radius: 12px;

        font-size: 1.05rem;
    }

    .cs-home h1 {
        font-size: 1.32rem;
    }

    .cs-home-subtitle {
        font-size: 0.72rem;
        margin-bottom: 0.95rem;
    }


    /* Cards */

    .cs-prompt-card {
        min-height: 54px;
        padding: 10px;
    }

    .cs-prompt-icon {
        width: 30px;
        height: 30px;

        flex-basis: 30px;

        font-size: 0.88rem;
    }

    .cs-prompt-card strong {
        font-size: 0.72rem;
    }

    .cs-prompt-card span {
        font-size: 0.61rem;
    }

    .cs-home-hint {
        font-size: 0.60rem;
    }


    /* Category cards */

    .cs-chip-row {
        grid-template-columns: 1fr;
        gap: 5px;
    }

    .cs-chip {
        min-height: 34px;

        padding: 6px 3px;

        font-size: 0.61rem;
    }


    /* Onboarding */

    .cs-onboard-wrap {
        padding-top: 0.9rem;
    }

    .cs-onboard-wrap h1 {
        font-size: 1.35rem;
    }

    .cs-onboard-wrap p {
        font-size: 0.72rem;
    }

    div[data-testid="stForm"] {
        padding: 0.85rem;
    }


    /* Model selector */

    div[data-testid="stSelectbox"] {
        width: 100% !important;

        margin-top: 0.25rem;
        margin-bottom: 0.3rem;
    }

    div[data-testid="stSelectbox"] > div > div {
        min-height: 2.1rem;

        font-size: 0.66rem;
    }


    /* Active mode */

    .cs-active-mode {
        max-width: 100%;

        margin-bottom: 0.35rem !important;

        padding: 5px 8px !important;

        font-size: 0.60rem !important;
    }


    /* Chat */

    div[data-testid="stChatMessage"] {
        padding: 0.65rem 0.7rem;
    }

    div[data-testid="stChatMessage"] p {
        font-size: 0.77rem;
        line-height: 1.48;
    }

    div[data-testid="stChatInput"] {
        border-radius: 12px;
    }

    div[data-testid="stChatInput"] textarea {
        font-size: 0.76rem !important;
    }

    .stButton > button,
    button[kind="formSubmit"] {
        min-height: 2.35rem;
        font-size: 0.78rem;
    }
}

</style>
"""

st.markdown(CIRCUITSNAP_CSS, unsafe_allow_html=True)


CS_LOGO_SVG = '<svg class="cs-logo" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="1" y="1" width="34" height="34" rx="9" fill="#151B23" stroke="#252D38"/><circle cx="11" cy="11" r="2.1" fill="#38BDF8"/><circle cx="25" cy="25" r="2.1" fill="#22D3EE"/><path d="M11 13.1V18H25V22.9" stroke="#38BDF8" stroke-width="1.6" stroke-linecap="round"/><circle cx="18" cy="18" r="1.6" fill="#F5F7FA"/></svg>'


def render_header(subtitle):
    st.markdown(
        f'<div class="cs-header">'
        f'<div class="cs-header-left">'
        f'{CS_LOGO_SVG}'
        f'<div>'
        f'<div class="cs-header-title">CircuitSnap</div>'
        f'<div class="cs-header-subtitle">{subtitle}</div>'
        f'</div>'
        f'</div>'
        f'<div class="cs-status">'
        f'<span class="cs-status-dot"></span>'
        f'Multi-Model Vision Ready'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# -----------------------------
# Gemini configuration
# -----------------------------

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

MODEL_NAME = "gemini-3.8-flash"


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


# -----------------------------
# Helper functions
# -----------------------------

def ask_gemini(parts):
    max_attempts = 2

    for attempt in range(max_attempts):
        try:
            response = st.session_state.chat.send_message(parts)
            return response.text

        except Exception as error:
            error_text = str(error)

            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
            ):
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue

                # Fallback to a lower-latency Gemini model
                try:
                    fallback_chat = gemini_client.chats.create(
                        model="gemini-3.5-flash-lite",
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            thinking_config=types.ThinkingConfig(
                                thinking_level="low"
                            ),
                            max_output_tokens=1200,
                        ),
                    )

                    fallback_response = fallback_chat.send_message(parts)
                    return fallback_response.text

                except Exception:
                    return (
                        "⚠️ Gemini is temporarily unavailable. "
                        "Please try again in a few seconds."
                    )

            if "401" in error_text or "UNAUTHENTICATED" in error_text:
                return (
                    "🔐 There is a problem authenticating with Gemini. "
                    "Please check the API configuration."
                )

            return (
                "⚠️ I couldn't process that request right now. "
                "Please try again."
            )


def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])

        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):
    message = {
        "role": role,
        "kind": kind,
        "content": content,
    }

    st.session_state.messages.append(message)
    render_message(message)


# -----------------------------
# Onboarding
# -----------------------------

if not st.session_state.get("onboarded", False):

    render_header("AI Electronics Vision Assistant")

    st.markdown(
        """
        <div class="cs-onboard-wrap">
            <h1>Welcome to CircuitSnap</h1>
            <p>Your AI-powered electronics lab partner.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("onboarding_form"):

        name = st.text_input(
            "Your name"
        )

        submitted = st.form_submit_button(
            "Let's start 🚀"
        )

        if submitted:

            if not name.strip():
                st.warning("Please enter your name.")

            else:
                st.session_state.name = name.strip()
                st.session_state.chat = gemini_client.chats.create(
                    model=MODEL_NAME,
                    config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    thinking_config=types.ThinkingConfig(
                    thinking_level="low"
                        ),
                        max_output_tokens=1200,
                    ),
                )

                st.session_state.messages = []
                st.session_state.onboarded = True

                st.rerun()

    st.stop()


# -----------------------------
# Main application
# -----------------------------

render_header(f"Welcome, {st.session_state.name} — upload an image or ask a question")

# Quick action modes
QUICK_ACTIONS = {
    "identify": {
        "label": "🔌 Identify a component",
        "prompt": (
            "Focus on identifying the electronic component shown. "
            "Explain its function, visible markings, pins or terminals, "
            "and important precautions. Do not guess an exact part number "
            "or specification unless the image clearly supports it."
        ),
    },
    "circuit": {
        "label": "📐 Explain a circuit",
        "prompt": (
            "Focus on analyzing the circuit or schematic shown. "
            "Explain the visible components, connections, and working. "
            "Clearly distinguish confirmed connections from anything "
            "that cannot be determined from the image."
        ),
    },
    "debug": {
        "label": "🧪 Debug my lab setup",
        "prompt": (
            "Focus on troubleshooting the electronics setup shown. "
            "Look for clearly visible wiring, component, polarity, "
            "or connection issues. Do not claim a fault unless the "
            "image provides enough evidence."
        ),
    },
    "learn": {
        "label": "📖 Learn an ECE concept",
        "prompt": (
            "Focus on teaching the electronics or ECE concept involved. "
            "Explain it in simple but technically correct language, "
            "using a practical example when useful."
        ),
    },
}

if "quick_action" not in st.session_state:
    st.session_state.quick_action = None
if "show_home" not in st.session_state:
    st.session_state.show_home = True

quick_action = st.session_state.quick_action

quick_action_prompt = QUICK_ACTIONS.get(
    quick_action, {}
).get("prompt", "")

# -----------------------------
# Display conversation history
# -----------------------------

if st.session_state.show_home:

    st.html(
        textwrap.dedent(
            """
            <div class="cs-home">

                <div class="cs-home-icon">
                    ⚡
                </div>

                <h1>What are we building?</h1>

                <p class="cs-home-subtitle">
                    Your AI assistant for electronics, circuits and ECE.
                </p>

                <div class="cs-home-hint">
                    Upload an image or start a conversation below
                </div>

            </div>
            """
        )
    )

    # Quick action buttons
    quick_cols = st.columns(2)

    with quick_cols[0]:
        if st.button(
            "🔌  Identify a component\nUpload a component photo",
            key="quick_identify",
            use_container_width=True,
        ):
            st.session_state.quick_action = "identify"
            st.session_state.show_home = False
            st.rerun()

    with quick_cols[1]:
        if st.button(
            "📐  Explain a circuit\nUnderstand connections and working",
            key="quick_circuit",
            use_container_width=True,
        ):
            st.session_state.quick_action = "circuit"
            st.session_state.show_home = False
            st.rerun()

    quick_cols = st.columns(2)

    with quick_cols[0]:
        if st.button(
            "🧪  Debug my lab setup\nAnalyze your electronics setup",
            key="quick_debug",
            use_container_width=True,
        ):
            st.session_state.quick_action = "debug"
            st.session_state.show_home = False
            st.rerun()

    with quick_cols[1]:
        if st.button(
            "📖  Learn an ECE concept\nAsk questions in simple language",
            key="quick_learn",
            use_container_width=True,
        ):
            st.session_state.quick_action = "learn"
            st.session_state.show_home = False
            st.rerun()

    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE_TEMPLATE.format(
            name=st.session_state.name
        ),
    )

else:

    for message in st.session_state.messages:
        render_message(message)



# AI model selector + chat input

if "selected_model" not in st.session_state:
    st.session_state.selected_model = "Gemini 3.8 Flash"

selected_model_name = st.selectbox(
    "AI Model",
    options=list(MODELS.keys()),
    index=list(MODELS.keys()).index(
        st.session_state.selected_model
    ),
    key="model_selector",
)

st.session_state.selected_model = selected_model_name

selected_model = get_model(selected_model_name)

if selected_model["provider"] == "Sarvam":
    st.caption("⚠️ Sarvam beta API access is required for this model.")
else:
    st.caption("✓ Vision + text model available")

if quick_action in QUICK_ACTIONS:
    st.markdown(
        f"""
        <div class="cs-active-mode">
            <span class="cs-active-mode-dot"></span>
            <span>Mode:</span>
            <strong>{QUICK_ACTIONS[quick_action]["label"]}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

user_input = st.chat_input(
    "Ask CircuitSnap anything about electronics...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)


photo = None

if user_input:

    if user_input.files:
        photo = user_input.files[0]

    text = user_input.text

    parts = []

    # Data used by Groq/Sarvam providers
    provider_prompt = ""
    photo_bytes = None
    photo_mime_type = None

    # Handle image
    if photo is not None:

        photo_bytes = photo.getvalue()
        photo_mime_type = photo.type

        add_message(
            "user",
            "image",
            photo_bytes,
        )

        parts.append(
            types.Part.from_bytes(
                data=photo_bytes,
                mime_type=photo.type,
            )
        )

    # Handle text
    if text:

        add_message(
            "user",
            "text",
            text,
        )

        provider_prompt = (
            text
            + "\n\n"
            + quick_action_prompt
            + "\n\n"
            + "Answer this as a concise electronics assistant. "
            + "For this simple question, use no more than 80 words. "
            + "Give only the essential explanation. "
            + "Do not add a table, detailed classifications, formulas, "
            + "applications, or extended examples unless specifically asked."
        )

        parts.append(provider_prompt)

    # Image without a question
    elif photo is not None:

        provider_prompt = (
            "Analyze this electronics image.\n\n"
            + quick_action_prompt
            + "\n\n"
            + "Identify the component, circuit, schematic, "
            "or setup if possible.\n\n"
            + "Explain what it is, its function, how it "
            "works, and important connections."
        )

        parts.append(provider_prompt)


    # Ask selected AI model

    with st.spinner(
        f"Analyzing with {selected_model_name}... 🔍"
    ):

        if selected_model["provider"] == "Gemini":

            answer = ask_gemini(parts)

        else:

            if photo is not None and not selected_model["vision"]:

                answer = (
                    f"⚠️ {selected_model_name} does not support "
                    "image analysis. Please select a vision model."
                )

            else:

                answer = ask_provider(
                    provider=selected_model["provider"],
                    model_id=selected_model["model_id"],
                    prompt=provider_prompt,
                    image_bytes=photo_bytes,
                    mime_type=photo_mime_type,
                )

    add_message(
        "assistant",
        "text",
        answer,
    )