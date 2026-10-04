# CircuitSnap 🔧

> AI-powered electronics assistant for ECE students.

 **See → Understand → Explore → Learn**

---

## ✨ What CircuitSnap Can Do

### 🔍 Identify Components

Upload a photo of an electronic component and ask CircuitSnap to identify
what can be reliably determined from the image.

It can explain:

- Component type
- Function
- Visible markings
- Visible terminals or pins
- Typical role in a circuit
- Important precautions

CircuitSnap avoids inventing exact part numbers or specifications when
the image does not provide enough evidence.

---

### 🔌 Explain Circuits

Upload a circuit, schematic, or electronics setup.

CircuitSnap can explain:

- Visible components
- Visible connections
- Circuit purpose
- Basic working
- Important relationships between components

It distinguishes between what is clearly visible and what cannot be
confirmed from the image.

---

### 🧪 Debug a Lab Setup

Use an image of an electronics lab setup to look for clearly visible
issues such as:

- Incorrect-looking wiring
- Polarity concerns
- Component placement problems
- Possible connection issues

The system does not automatically claim that a circuit is electrically
correct simply because the physical arrangement looks reasonable.

---

### 🧠 Learn ECE Concepts

Ask electronics questions in natural language.

CircuitSnap can adapt its explanation depending on the request:

- Simple explanation
- Technical explanation
- Step-by-step calculation
- Exam-style answer
- Practical/lab explanation

---

## 🎯 Accuracy First

CircuitSnap is designed around a simple rule:

> **Accuracy is more important than confidence.**

When analyzing an image, the assistant should distinguish between:

**CONFIRMED**

Information directly supported by visible evidence.

**LIKELY**

A reasonable interpretation that is not completely certain.

**CANNOT CONFIRM**

The image does not provide enough evidence.

CircuitSnap should not invent:

- Exact component part numbers
- Component values
- Pin numbers
- Pinouts
- Electrical connections
- Ratings
- Datasheet specifications
- PCB traces
- Circuit topology

When evidence is insufficient, it should say so.

---

## 🤖 Available AI Models

CircuitSnap currently supports:

| Model  | Provider | Purpose        |
| ------ | -------- | -------------- |
| Gemini | Google   | Recommended    |
| Groq   | Groq     | Fast responses |

Both are used through CircuitSnap's provider layer.

The model can be changed without intentionally discarding the
conversation history.

---

## 🏗️ Architecture

```text
                     CircuitSnap
                          │
                       app.py
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
      ui.py           models.py        providers.py
        │                 │                 │
        ▼                 ▼                 ├── Gemini
   UI & styling      Model registry         └── Groq
                          │
                          ▼
                     prompts.py
```
