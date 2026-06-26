# VisualQ (VQP)

<p align="center">
  <img src="./frontend/public/banner.png" alt="VisualQ Banner" width="100%">
</p>

<p align="center">
  <strong>AI-Powered Physics Question Paper & Diagram Intelligence Engine</strong>
</p>

<p align="center">
  Generate CBSE-compliant Physics question papers, automatically detect diagram-based questions, create accurate SVG diagrams, and export ready-to-use assessments.
</p>

---

## 🚀 Overview

VisualQ is an educational AI platform focused on solving one of the most difficult problems in automated assessment generation:

> Generating Physics question papers along with their required diagrams.

Unlike traditional paper generators, VisualQ contains a dedicated Diagram Intelligence Engine capable of detecting diagram-based questions and generating structured Physics diagrams through deterministic rendering systems.

The platform combines:

* Question Paper Generation
* Diagram Classification
* Diagram Intelligence
* SVG Rendering
* PDF Export
* Diagram Revision Workflows

---
## 🖥️ Interface

<p align="center">
  <img src="./frontend/public/vqp.png" alt="VisualQ Interface" width="100%">
</p>

---

## ✨ Key Features

### 📄 Question Paper Generation

* Unit Test (20 Marks)
* Full Paper (70 Marks)
* PYQ + AI Hybrid Generation
* Chapter-based selection
* Difficulty balancing

### 🧠 Diagram Intelligence

Automatic detection of:

* Ray Diagrams
* Circuit Diagrams
* Free Body Diagrams
* Magnetic Field Diagrams
* Semiconductor Diagrams
* Physics Graphs

### 🎨 Deterministic Diagram Rendering

Instead of generating images directly using AI:

Question

↓

Blueprint

↓

Compiler

↓

SVG

Result:

* Consistent output
* Physics accuracy
* Validation support
* Revision support

### 📑 PDF Export

* Printable papers
* Embedded diagrams
* CBSE-style formatting
* Ready for classroom use

---

# 🏗 Architecture

```text
Question

    ↓

Paper Engine

    ↓

Diagram Intelligence Engine

    ↓

Blueprint Generation

    ↓

Validation Layer

    ↓

Compiler System

    ↓

SVG Diagram

    ↓

PDF Export
```

---

# 🔬 Evolution of VisualQ

## Detailed Approach History

| Approach | Why | Implemented | Problem | Why Next | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Approach 1** — Direct AI Image Generation | Wanted AI to directly generate Physics diagrams from questions. | ChatGPT Image Generation, Flux Schnell, prompt engineering. | Diagrams were inconsistent, labels were missing, and outputs could not be validated. | Needed a deterministic and controllable solution. | ❌ Rejected |
| **Approach 1.5** — Diagram Knowledge Base Creation | Understand what information is actually needed to recreate CBSE diagrams. | Collected Physics diagrams and extracted diagram structure, components, labels, and relationships. | Knowledge existed but there was no generation mechanism. | Needed a structured representation of diagrams. | ✅ Foundation |
| **Approach 2** — Schema-Based Diagram System | Represent diagrams as structured data instead of images. | Created schemas for Ray, Circuit, FBD, Magnetic, Semiconductor, and Graph diagrams. | Schemas defined structure but could not generate visuals. | Needed a rendering engine. | ⚠ Partial Success |
| **Approach 2.5** — Manual Blueprint Generation | Test whether schemas could be converted into actual diagrams. | Handwritten blueprints and simple renderers. | Worked only for predefined cases and could not generalize. | Needed automated diagram generation. | ⚠ Partial Success |
| **Approach 3** — APPROCH2 Rendering Engine | Build deterministic Physics diagram generation. | Validator, Layout Engine, Renderer, Compiler for all diagram families. | Could render diagrams but could not understand questions. | Needed AI reasoning before rendering. | ✅ Stable |
| **Approach 3.1** — LLM-Based Blueprint Generation | Convert questions into blueprints automatically. | Question → Blueprint using LLM. | Blueprints were inconsistent and often inaccurate. | Needed example-guided generation. | ⚠ Partial Success |
| **Approach 3.2** — Example Retrieval System | Reuse successful diagrams instead of generating everything from scratch. | Question → Similarity Search → Best Example → Blueprint Modification. | Some questions had no similar examples. | Needed fallback generation. | ✅ Better Accuracy |
| **Approach 3.3** — Hybrid Diagram Generation | Handle both known and unseen questions. | Similarity >= 0.85 → Example Based \| Similarity < 0.85 → Schema Based. | Blueprint quality still varied. | Needed validation and correction. | ✅ Current Production |
| **Approach 4** — Diagram Intelligence Engine V2 | Create a complete end-to-end pipeline. | Classifier, Schema Router, Retriever, Blueprint Generator, Evaluator, Compiler. | — | Needed user feedback and revisions. | ✅ Current Architecture |
| **Approach 4.1** — Quality & Validation Layer | Improve diagram correctness. | Family Validator, Confidence Score, Explanation Engine, Schema Fallback, Traceability. | — | Needed compiler compatibility. | ✅ Current Architecture |
| **Approach 4.2** — Adapter Layer | Backend schemas and APPROCH2 compilers used different formats. | Adapters for all six diagram families. | — | Needed production verification. | ✅ Current Architecture |
| **Approach 4.3** — End-to-End Testing | Verify every diagram family. | Test Runner, Validation Suite, SVG Verification. | — | Needed a reusable service layer. | ✅ Current Architecture |
| **Approach 4.4** — Diagram Engine | Create a single public API. | `DiagramEngine.generate_diagram()` | — | Needed paper generation integration. | ✅ Current Architecture |
| **Approach 4.5** — Paper Generation Integration | Generate diagrams directly from generated papers. | Paper → Diagram Detection → Diagram Engine → SVG. | — | Needed scaling and reliability. | ✅ Current Architecture |
| **Approach 4.8** — Production Optimizations | Handle real-world paper generation. | Parallel Generation, Semiconductor Routing, Component Mapping, SVG Validation, Versioned Outputs. | — | Need revision workflows. | ✅ Current Architecture |
| **Approach 5** — Diagram Revision Engine (Current) | Allow users to improve generated diagrams. | Generated Diagram → AI Suggestions → User Feedback → Revision Prompt → New Blueprint → New SVG Version. | — | — | 🚧 In Progress |

## One-Line Summary

| Approach | Summary |
| :--- | :--- |
| **Approach 1** | AI generated images. |
| **Approach 2** | Represent diagrams as data. |
| **Approach 3** | Build deterministic renderers. |
| **Approach 4** | Add AI reasoning around renderers. |
| **Approach 5** | Add human-guided diagram revisions. |

---

# 🧩 Diagram Families

| Family                  | Status |
| ----------------------- | ------ |
| Ray Diagrams            | ✅      |
| Circuit Diagrams        | ✅      |
| Free Body Diagrams      | ✅      |
| Magnetic Field Diagrams | ✅      |
| Semiconductor Diagrams  | ✅      |
| Graphs                  | ✅      |

---

# 🎯 Results

<p align="center">
  <img src="./frontend/public/results/Q3.svg" alt="Ray Diagram" width="30%">
  <img src="./frontend/public/results/C10_meter_bridge.svg" alt="Circuit Diagram" width="30%">
  <img src="./frontend/public/results/F9.svg" alt="Free Body Diagram" width="30%">
</p>
<p align="center">
  <em>Ray · Circuit · Free Body Diagram</em>
</p>

<p align="center">
  <img src="./approch2/graph/output/G7.svg" alt="Graph" width="30%">
  <img src="./approch2/magnetic_field/output1/M9.svg" alt="Magnetic Field Diagram" width="30%">
  <img src="./approch2/semiconductor/output/S3.svg" alt="Semiconductor Diagram" width="30%">
</p>
<p align="center">
  <em>Graph · Magnetic Field · Semiconductor</em>
</p>

---

# ⚙️ Tech Stack

## 🖥️ Frontend

![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![ShadCN](https://img.shields.io/badge/ShadCN_UI-000000?style=for-the-badge&logo=shadcnui&logoColor=white)

## ⚙️ Backend

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SVG Rendering](https://img.shields.io/badge/SVG_Rendering-FFB13B?style=for-the-badge)
![PDF Export](https://img.shields.io/badge/PDF_Export-EC1C24?style=for-the-badge)

## 🗄️ Database

![Neon](https://img.shields.io/badge/Neon_PostgreSQL-00E599?style=for-the-badge)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)

## 🤖 AI Models

![GPT OSS 120B](https://img.shields.io/badge/GPT_OSS_120B-412991?style=for-the-badge)
![Gemini 3.5 Flash](https://img.shields.io/badge/Gemini_3.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)
![OpenRouter](https://img.shields.io/badge/OpenRouter-000000?style=for-the-badge&logo=openrouter&logoColor=white)

## 🎨 Diagram Engine

![SVG](https://img.shields.io/badge/SVG_Rendering-FFB13B?style=for-the-badge)
![Physics Engine](https://img.shields.io/badge/Physics_Diagram_Engine-7B61FF?style=for-the-badge)
![Blueprint Compiler](https://img.shields.io/badge/Blueprint_Compiler-22C55E?style=for-the-badge)

## 🛠️ Development

![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)

---

# 🤖 LLM Infrastructure

| Provider              | Model                 | Usage                      | Avg Response Time | Cost Category  | Status           |
| --------------------- | --------------------- | -------------------------- | ----------------- | -------------- | ---------------- |
| OpenRouter            | GPT OSS 120B          | Question Generation        | 5–15 sec          | Low            | ✅ Current        |
| OpenRouter            | GPT OSS 120B          | Blueprint Generation       | 5–20 sec          | Low            | ✅ Current        |
| Google Gemini API     | Gemini 3.5 Flash      | Evaluation & Validation    | 2–8 sec           | Very Low       | ✅ Current        |
| OpenRouter            | Qwen 3 235B Thinking  | Diagram Evaluation         | 15–45 sec         | Medium         | ⚠ Tested         |
| OpenRouter            | DeepSeek R1           | Diagram Reasoning          | 20–60 sec         | Medium–High    | ⚠ Tested         |
| Flux Schnell          | —                     | Diagram Image Research     | 3–10 sec          | Low            | ❌ Discarded      |
| ChatGPT Image Gen     | —                     | Diagram Knowledge Extraction | 10–30 sec       | High           | ⚠ Research Phase |

## 💰 Cost Considerations

### ✅ Current Production Stack

| Stage                  | Provider     |
| ---------------------- | ------------ |
| Question Generation    | GPT OSS 120B (OpenRouter) |
| Blueprint Generation   | GPT OSS 120B (OpenRouter) |
| Evaluation & Validation | Gemini 3.5 Flash |
| Diagram Rendering      | Local SVG Compilers |
| PDF Export             | Local Python Engine |

### 🔻 Why Costs Are Low

VisualQ does **not** generate images using AI image models.

Instead:

```
Question → LLM → Blueprint → SVG Compiler → Diagram
```

Rather than:

```
Question → Image Model → PNG
```

> This removes the most expensive step from the pipeline.

### 📊 Estimated Cost Per Paper

**Unit Test (20 Marks)**

| Stage                  | Cost Source   |
| ---------------------- | ------------- |
| Question Selection     | Local         |
| PYQ Retrieval          | Local         |
| Question Generation    | OpenRouter    |
| Diagram Classification | OpenRouter    |
| Blueprint Generation   | OpenRouter    |
| Evaluation             | Gemini        |
| SVG Rendering          | Local         |
| PDF Export             | Local         |

**Estimated Cost: ₹0 – ₹0.50 per paper**

**Full CBSE Paper (70 Marks)**

| Metric             | Value     |
| ------------------ | --------- |
| Questions          | 30–35     |
| Diagram Questions  | 5–8       |
| LLM Calls          | ~40–60    |
| SVG Compilations   | 5–8       |
| PDF Exports        | 1         |

**Estimated Cost: ₹0.50 – ₹5 per paper**

### 🎯 Cost Optimization Strategy

VisualQ follows a hybrid architecture:

```
OpenRouter → Reasoning & Content Generation
Gemini → Evaluation & Correction
Local Engines → Rendering & Export
```

> This architecture minimizes API usage while maintaining high diagram accuracy and deterministic outputs.

### 📌 Summary

> VisualQ reduces generation costs by using LLMs only for reasoning and blueprint creation, while all diagram rendering and PDF generation are executed locally through deterministic engines. This significantly lowers operational costs compared to AI image generation workflows.

---

# 📂 Project Structure

```text
VQP/

├── frontend/
│
├── backend/
│
├── backend_v2/
│
├── approch2/
│   ├── ray/
│   ├── circuit/
│   ├── fbd/
│   ├── magnetic/
│   ├── semiconductor/
│   └── graph/
│
├── datapipeline/
│
└── approaches/
```

---

# 📊 Current Status

---

# 🎯 Design Principle

VisualQ follows a simple rule:

```text
LLM

↓

Blueprint

↓

Deterministic Renderer

↓

SVG
```

Never:

```text
LLM

↓

Raw Diagram
```

The renderer is the source of truth.

The AI only provides structured intent.

---

# 👨‍💻 Authors

Built as part of the VisualQ research initiative focused on Physics Question Paper Generation, Diagram Intelligence, and Educational AI Systems.

---

## License

Research & Educational Use.
