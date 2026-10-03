# CircuitSnap 🔧

> AI-powered electronics vision assistant for ECE students.

CircuitSnap is an AI-powered electronics vision assistant built for ECE students. It analyzes electronic components, circuits, schematics, breadboards, and laboratory setups, then explains what is visible, how it works, and what can or cannot be reliably determined from the image.

The application supports multiple AI providers and vision-capable models through a simple interactive chat interface.

## ✨ Features

- 📷 Analyze electronic components from images
- 🔌 Analyze circuits, breadboards, schematics, and lab setups
- 🧠 Explain electronics concepts in simple ECE-oriented language
- 🔍 Identify visible components, markings, pins, and connections when possible
- 💬 Ask electronics questions through an interactive chat
- ⚠️ Highlight uncertainty instead of inventing component specifications
- 📚 Provide practical explanations, formulas, applications, and precautions when relevant
- 🤖 Switch between supported AI models
- 📱 Responsive interface for mobile, tablet, and desktop
- 🎨 Clean dark interface designed for electronics learning

## 🤖 AI Models

| Model | Provider | Vision |
|---|---|---|
| Gemini 3.8 Flash | Google Gemini | ✅ |
| Qwen 3.8 27B | Groq | ✅ |
| Gemma 4 | Sarvam AI | ✅ |
| GLM 5.3 | Sarvam AI | ❌ |
| DeepSeek V4 Flash | Sarvam AI | ❌ |
| Sarvam 105B | Sarvam AI | ❌ |

> Availability of some Sarvam models depends on API access and enabled beta capabilities.

## 🛠️ Tech Stack

- Python
- Streamlit
- Google Gemini API
- Groq API
- Sarvam AI API
- HTML/CSS

## 🧩 How It Works

```text
User
  │
  ├── Uploads an image
  │        or
  └── Asks an electronics question
             │
             ▼
       CircuitSnap UI
             │
             ▼
       Model Selector
             │
      ┌──────┼──────┐
      ▼      ▼      ▼
   Gemini   Groq   Sarvam
      │      │      │
      └──────┼──────┘
             ▼
        AI Analysis
             │
             ▼
   Electronics Explanation
             │
             ▼
            User
```

## 🔎 Evidence-Based Analysis

CircuitSnap is designed to separate visible observations from assumptions when analyzing electronics images.

Responses can distinguish between:

- **CONFIRMED** — directly supported by visible evidence
- **LIKELY** — a reasonable interpretation but not fully confirmed
- **CANNOT CONFIRM** — insufficient visual information

This approach helps reduce unsupported claims about component values, pinouts, connections, specifications, and circuit behavior.

## 📁 Project Structure

```text
CircuitSnap/
├── app.py
├── models.py
├── providers.py
├── prompts.py
├── requirements.txt
├── README.md
└── .streamlit/
    └── config.toml
```

## 🚀 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/jagannath-badi/CircuitSnap.git
cd CircuitSnap
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure API keys

Create:

```text
.streamlit/secrets.toml
```

Add your API keys:

```toml
GEMINI_API_KEY = "your_gemini_api_key"
GROQ_API_KEY = "your_groq_api_key"
SARVAM_API_KEY = "your_sarvam_api_key"
```

Never commit real API keys or `.streamlit/secrets.toml` to GitHub.

### 5. Run the application

```powershell
streamlit run app.py
```

The application will open at the local Streamlit address shown in the terminal.

## 🌐 Live Demo

https://circuitsnap.streamlit.app

## 🎥 Demo

The demo demonstrates:

- Electronics component identification from an image
- Circuit and PCB image analysis
- Electronics question answering
- Evidence-based explanations
- Switching between supported AI models
- Responsive CircuitSnap interface

## 📦 GitHub

https://github.com/jagannath-badi/CircuitSnap

## 🔐 Safety & Limitations

CircuitSnap is designed to avoid guessing information that cannot be reliably determined from an image.

For example:

- Clearly visible information is reported when supported by the image.
- Unclear component values are not intentionally guessed.
- Uncertain pinouts or connections are identified as uncertain.
- Exact specifications should be verified using datasheets or proper measurements.
- Image analysis depends on image quality, lighting, visibility, and camera angle.

CircuitSnap is intended as an educational assistant and should not replace proper laboratory measurements, datasheets, or engineering verification.

## 🎯 Project Goal

CircuitSnap aims to make electronics learning more interactive by combining computer vision, conversational AI, and ECE-focused prompting.

Students can upload an electronics image or ask a question and receive an understandable explanation through a single interactive interface.

## 👨‍💻 Author

**Jagannath Badi**

Electronics & Telecommunication Engineering Student

---

Built with Python, Streamlit, and AI vision models.
