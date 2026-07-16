# Contract Clause Risk Analyzer

[![Tests](https://github.com/senthamizhvelan04/Contract-Clause-Risk-Analyzer/actions/workflows/python-app.yml/badge.svg)](https://github.com/senthamizhvelan04/Contract-Clause-Risk-Analyzer/actions/workflows/python-app.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A production-ready tool that analyzes legal contract clauses and returns structured risk assessments (clause type, risk level, reasoning, recommended action, confidence) to accelerate human legal review. 
*Note: This is a triage tool for legal and compliance teams, not a substitute for formal legal advice.*

## 🎬 Demo

<video src="assets/demo.webm" controls autoplay loop style="max-width: 100%;"></video>

### Screenshots
**High Risk Clause**
![High Risk](assets/high_risk.png)

**Prompt Injection Defense**
![Injection Defense](assets/injection.png)

---

## 📊 Evaluation & Accuracy

We run an automated evaluation suite against a curated set of clauses (similar to the CUAD dataset) to ensure our prompt guardrails and classifications remain accurate.

### Evaluation Results: 80.0% Accuracy on Risk Classification

| ID | Clause Type | Expected Risk | Predicted Risk | Match |
|---|---|---|---|---|
| c1 | Non-Compete | High | High | ✅ |
| c2 | Governing Law | Low | Low | ✅ |
| c3 | Indemnification | Medium | Medium | ✅ |
| c4 | Limitation of Liability | High | High | ✅ |
| c5 | Confidentiality/NDA | Low | Low | ✅ |
| c6 | Auto-Renewal | High | Medium | ❌ |
| c7 | Termination | Medium | Low | ❌ |
| c8 | Data Privacy | High | High | ✅ |
| c9 | Other | Error | Error | ✅ |
| c10 | Other | Error | Error | ✅ |

*(Note: c6 and c7 failed strictly on the binary expectation, demonstrating the model's leniency on standard termination notices).*

---

## Overview
Generic prompting often drifts in format and occasionally invents definitive legal conclusions. This project solves that by treating the system prompt as a versioned, tested artifact and providing a robust application wrapper (CLI and Streamlit UI) that handles schema validation, retries, and clean presentation.

## Architecture

```
.
├── app.py                  # Streamlit Web UI
├── contract_analyzer.py    # Core logic & CLI script
├── requirements.txt        # Dependencies
├── sample_clauses.json     # Test cases representing various edge cases
└── system_prompt.txt       # Versioned (v1.2.0) LLM instruction set
```

## Design Decisions
- **Confidence Field**: Provides metadata on the LLM's certainty, crucial for identifying truncated or out-of-context clauses.
- **Injection Guardrail**: Explicit instructions to treat clause text purely as data, preventing the LLM from obeying rogue commands embedded in the text.
- **Schema Validation + Retries**: Uses exponential backoff and `dataclasses` to enforce strict JSON schemas, recovering gracefully from transient API errors or formatting glitches.
- **No-Definitive-Conclusions Rule**: Prevents the model from making dangerous, unauthorized legal claims (e.g. "this is unenforceable"). Uses calibrated phrasing.

## Usage Instructions

### Prerequisites
1. Ensure Python 3.8+ is installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your Groq API Key:
   ```bash
   # Windows (PowerShell)
   $env:GROQ_API_KEY="your-api-key"
   
   # Mac/Linux
   export GROQ_API_KEY="your-api-key"
   ```

### Command Line Interface (CLI)

**Analyze a single clause:**
```bash
python contract_analyzer.py --clause "This Agreement shall be governed by the laws of Delaware."
```

**Analyze a batch of clauses:**
```bash
python contract_analyzer.py --input sample_clauses.json --output results.json
```

### Streamlit Web UI

Run the interactive dashboard:
```bash
streamlit run app.py
```
This will launch a web interface where you can paste text directly or upload a JSON file (like `sample_clauses.json`) for batch processing.

## Production Path (Fine-Tuning)

To scale this beyond API calls or into fully air-gapped environments, the system prompt logic can be distilled into an open-source model:
1. **Model Selection:** Llama 3 8B or Mistral 7B via QLoRA.
2. **Dataset:** Fine-tune on the CUAD (Contract Understanding Atticus Dataset), augmented with synthetic variations matching this prompt's taxonomy.
3. **Evaluation Plan:** Compare the fine-tuned model against the base model zero-shot using:
   - Precision/Recall/F1 per clause category
   - JSON schema validity rate
   - Confusion matrix for Risk Levels

## Limitations
- **Not Legal Advice:** This tool does not substitute for qualified legal counsel.
- **Clause-Level Only:** Cannot detect cross-clause conflicts (e.g. an indemnification clause contradicting a limitation of liability elsewhere in the document).
- **Generic Calibration:** "Market-standard" is evaluated generically; specific industry or regional nuances may require specialized prompting or fine-tuning.
