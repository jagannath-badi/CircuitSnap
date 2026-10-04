
# CircuitSnap 🔧

> AI-powered electronics assistant for ECE students.

CircuitSnap is an AI-powered electronics assistant built specifically for Electronics and Telecommunication Engineering students.

It helps students understand electronic components, circuits, schematics, physical lab setups, and ECE concepts through a single conversational interface with image analysis support.

The core experience is:

**See → Understand → Explore → Learn**

---

## ✨ What CircuitSnap Can Do

### 🔍 Identify Components

Upload an image of an electronic component and ask CircuitSnap what can be reliably determined from the image.

It can help with:

- Component type
- Function
- Visible markings
- Visible terminals or pins
- Typical role in a circuit
- Important precautions

CircuitSnap is designed to avoid inventing exact part numbers or specifications when the available evidence is insufficient.

---

### 🔌 Explain Circuits

Upload a circuit diagram, schematic, breadboard, or electronics setup.

CircuitSnap can help explain:

- Visible components
- Visible connections
- Circuit purpose
- Basic working
- Relationships between components
- Relevant electronics concepts

It distinguishes between what is clearly visible and what cannot be confirmed from the image.

---

### 🧪 Troubleshoot Electronics

Use CircuitSnap to investigate possible problems in an electronics setup.

It can help identify:

- Visible wiring concerns
- Polarity concerns
- Component placement issues
- Possible connection problems
- Areas that require measurement or further inspection

A physical arrangement that looks correct is not automatically treated as proof of electrical continuity or circuit correctness.

---

### 🧰 Test Components

CircuitSnap can provide practical guidance for checking common electronic components with tools such as a multimeter.

The response can include:

- Test procedure
- Expected behavior
- Measurements to take
- Interpretation of results
- Safety and handling precautions

Actual measurements should always be verified with appropriate laboratory equipment.

---

### 🧠 Learn ECE Concepts

Ask electronics questions naturally.

CircuitSnap adapts the explanation to the request, for example:

- Simple explanation
- Technical explanation
- Step-by-step derivation
- Numerical calculation
- Comparison
- Practical explanation
- Exam-style answer
- Viva preparation

Follow-up questions can continue from the existing conversation instead of starting from zero.

---

## 🎯 Accuracy First

CircuitSnap is designed around a simple principle:

> **Accuracy is more important than confidence.**

When analyzing an image, the assistant can distinguish between:

**CONFIRMED**

Information directly supported by visible evidence.

**LIKELY**

A reasonable interpretation that is not completely certain.

**CANNOT CONFIRM**

The available image or information is insufficient to determine the claim reliably.

CircuitSnap is designed not to invent:

- Exact component part numbers
- Unsupported component values
- Pin numbers or pinouts
- Electrical connections
- Ratings
- Measurements
- PCB traces
- Circuit topology
- Datasheet specifications
- Unsupported standards or references

Visible physical arrangement is not automatically treated as proof of electrical connectivity.

For important engineering decisions, measurements and component documentation should still be used for verification.

---

## 🤖 Available AI Models

CircuitSnap currently supports:

| Model  | Provider | Vision |
| ------ | -------- | ------ |
| Gemini | Google   | ✅     |
| Groq   | Groq     | ✅     |

The model can be changed from the CircuitSnap composer without intentionally discarding the conversation history.

CircuitSnap uses a provider layer so the application can work with supported AI providers through the same interface.

---

## 🧩 How CircuitSnap Works

```text
                         CircuitSnap
                              │
                            app.py
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
      ui.py                engine.py            models.py
        │                     │                     │
        │                     ▼                     │
        │              Request understanding       │
        │              Intent / workflow           │
        │              Context handling             │
        │              Evidence rules               │
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                        providers.py
                         ┌────┴────┐
                         ▼         ▼
                      Gemini     Groq
                         │         │
                         └────┬────┘
                              ▼
                           Response
                              │
                              ▼
                           Student
```

```

```
