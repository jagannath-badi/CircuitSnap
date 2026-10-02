
# CircuitSnap 🔧

> AI-powered electronics vision assistant for ECE students.

CircuitSnap is an AI-powered electronics assistant that analyzes images of electronic components, circuits, schematics, and laboratory setups using Gemini Vision.

It helps ECE students understand what they are looking at, how it works, what connections are visible, and which electronics concepts are involved.

## ✨ Features

- 📷 Analyze electronic components from images
- 🔌 Analyze circuits, breadboards, schematics, and lab setups
- 🧠 Explain electronics concepts in simple ECE-oriented language
- 🔎 Identify visible components, markings, pins, and connections when possible
- 💬 Ask follow-up electronics questions through an interactive chat
- ⚠️ Highlight uncertainty instead of inventing component specifications
- 📚 Provide practical explanations, formulas, applications, and precautions when relevant
- 🎨 Clean dark electronics-inspired interface

## 🛠️ Tech Stack

- **Python**
- **Streamlit**
- **Google Gemini API**
- **Gemini Vision**
- **HTML/CSS** for interface customization

## 🧩 How It Works

```text
User
  │
  ├── Uploads an image
  │       │
  │       ▼
  │   CircuitSnap
  │       │
  │       ▼
  │   Gemini Vision
  │       │
  │       ▼
  │   Image + Question Analysis
  │       │
  │       ▼
  │   Structured Electronics Explanation
  │
  └── Asks an electronics question
          │
          ▼
      Gemini-powered response
```
