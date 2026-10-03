# CircuitSnap 🔧

> AI-powered electronics vision assistant for ECE students.

CircuitSnap is an AI-powered electronics assistant that analyzes images of electronic components, circuits, schematics, breadboards, and laboratory setups. It helps ECE students understand what they are looking at, how it works, and which electronics concepts are involved.

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
- 🎨 Clean dark electronics-inspired interface

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

```bash
pip install -r requirements.txt
```

### 4. Add API keys

Create:

```text
.streamlit/secrets.toml
```

Add the required API keys:

```toml
GEMINI_API_KEY = "your_gemini_api_key"
GROQ_API_KEY = "your_groq_api_key"
SARVAM_API_KEY = "your_sarvam_api_key"
```

**Never commit API keys or `secrets.toml` to GitHub.**

### 5. Run the application

```bash
streamlit run app.py
```

The application will open in your browser at the local Streamlit address.

## 🌐 Live Demo

https://circuitsnap.streamlit.app

## 📦 GitHub

https://github.com/jagannath-badi/CircuitSnap

## 🔐 Safety & Limitations

CircuitSnap is designed to avoid guessing information that cannot be reliably determined from an image.

For example:

- Clearly visible information is reported when supported by the image.
- Unclear component values are not intentionally guessed.
- Uncertain pinouts or connections are identified as uncertain.
- Exact specifications should be verified using datasheets or proper measurements.

CircuitSnap is intended as an educational assistant and should not replace proper laboratory measurements, datasheets, or engineering verification.

## 🎯 Project Goal

CircuitSnap aims to make electronics learning more interactive by combining computer vision, conversational AI, and ECE-focused prompting.

Students can upload an electronics image or ask a question and receive an understandable explanation through a single interactive interface.

## 👨‍💻 Author

**Jagannath Badi**

Electronics & Telecommunication Engineering Student

---

Built with Python, Streamlit, and AI vision models.
