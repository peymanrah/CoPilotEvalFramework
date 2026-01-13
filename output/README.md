# CoPilot Evaluation Framework

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Playwright-1.57+-green.svg" alt="Playwright">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/Status-POC-orange.svg" alt="Status">
</p>

An automated UX evaluation framework for benchmarking **Microsoft Copilot** against competitors (ChatGPT, Gemini) using stealth browser agents and LLM-as-judge evaluation.

## 🎯 Overview

This framework enables:
- **Automated competitive benchmarking** across multiple AI chatbots
- **Synthetic prompt generation** from user feedback data
- **Dual-mode evaluation** (text responses + visual screenshots)
- **LLM-as-judge scoring** across 7 UX dimensions

### Key Capabilities

| Feature | Description |
|---------|-------------|
| 🤖 **Stealth Browser Agent** | Playwright-based automation with bot detection avoidance |
| 📝 **Synthetic Prompt Generation** | Create realistic prompts from intent taxonomy |
| 📸 **Screenshot Capture** | Visual response capture with scroll-based pagination |
| 🎯 **Multi-Chatbot Support** | Copilot, ChatGPT, Gemini (extensible) |
| 📊 **Evaluation Pipeline** | OpenAI GPT-4 powered response scoring |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Feedback Data                           │
│                    (Intent Taxonomy)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                Synthetic Prompt Generator                        │
│         (synthetic_prompt_generator.py)                         │
│                                                                  │
│  • Parse Action/Object/Subject intents                          │
│  • Generate prompt variants (simple → expert)                   │
│  • Add context URLs from public documents                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Stealth Browser Agent                          │
│              (chatbot_stealth_agent.py)                         │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Copilot  │    │ ChatGPT  │    │  Gemini  │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│                                                                  │
│  Output: Full text + Screenshots per response                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Evaluation Layer                               │
│                                                                  │
│  • Text Analysis (GPT-4 Judge)                                  │
│  • Visual Analysis (GPT-4 Vision)                               │
│  • Dimension Scoring (7 UX metrics)                             │
│  • Competitive Leaderboards                                     │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
CoPilotEvalFramework/
├── README.md                          # This file
├── docs/
│   └── UX_Evaluation_Framework_Technical_Guide.md   # Full technical documentation
│   └── UX_Evaluation_Framework_Technical_Guide.docx # Word version
├── chatbot_stealth_agent.py           # Main stealth browser automation
├── synthetic_prompt_generator.py      # Prompt generation from intents
├── add_context_to_prompts_v4.py       # Context URL enrichment
├── generate_synthetic_prompts.py      # Generation orchestrator (v1)
├── generate_synthetic_prompts_v2.py   # Generation orchestrator (v2)
├── generate_synthetic_prompts_v3.py   # Generation orchestrator (v3)
├── run_generation.py                  # CLI runner for generation
├── chatbot_evaluation_agent.py        # Non-stealth evaluation agent
├── chatbot_evaluation_webapp.py       # Web UI for evaluation
├── test_simple_submit.py              # Test utilities
├── test_submit_methods.py             # Submit method tests
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git ignore rules
└── evaluation_results/                # Output directory (gitignored)
    └── screenshots/                   # Captured screenshots
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js (for Playwright)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/peymanrah/CoPilotEvalFramework.git
cd CoPilotEvalFramework

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Running Evaluations

```bash
# Run evaluation on N prompts across all chatbots
python chatbot_stealth_agent.py 10

# This will:
# 1. Load synthetic prompts from input CSV
# 2. Submit each prompt to Copilot, ChatGPT, and Gemini
# 3. Capture full text responses
# 4. Take screenshots of each response
# 5. Save results to evaluation_results/
```

### Generating Synthetic Prompts

```bash
# Generate prompts from intent data
python run_generation.py

# Or use the generator directly
python synthetic_prompt_generator.py
```

## 📊 Evaluation Dimensions

The framework evaluates responses across 7 UX dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Factuality** | 20% | Accuracy and grounding in source context |
| **Helpfulness** | 20% | Task completion and actionability |
| **Safety** | 15% | Absence of harmful or inappropriate content |
| **Robustness** | 10% | Consistency across prompt variations |
| **Latency** | 10% | Response time performance |
| **Formatting** | 15% | Visual structure and readability |
| **Memory** | 10% | Context retention (multi-turn) |

## 🔧 Configuration

### Chatbot URLs

Edit `chatbot_stealth_agent.py` to modify target chatbots:

```python
CHATBOT_URLS = {
    "copilot": "https://copilot.microsoft.com/",
    "chatgpt": "https://chatgpt.com/",
    "gemini": "https://gemini.google.com/app",
}
```

### Stealth Settings

The agent uses multiple techniques to avoid bot detection:
- Playwright-stealth for fingerprint masking
- Persistent browser profiles
- Human-like delays and interactions
- Realistic viewport and user agent

## 📈 Output Format

### Consolidated Results CSV

Each evaluation run produces a consolidated CSV with columns:

| Column | Description |
|--------|-------------|
| `synthetic_prompt_id` | Unique prompt identifier |
| `source_intent` | Original intent (e.g., "GET + UPDATES") |
| `synthetic_prompt` | The generated prompt text |
| `response_copilot` | Full text response from Copilot |
| `response_chatgpt` | Full text response from ChatGPT |
| `response_gemini` | Full text response from Gemini |
| `screenshots_*` | Paths to captured screenshots |
| `response_time_seconds_*` | Latency per chatbot |
| `bot_detected_*` | Bot detection flags |

### Screenshots

Screenshots are organized by prompt and chatbot:

```
evaluation_results/screenshots/
├── SP_000001/
│   ├── copilot/
│   │   ├── response_1_183324.png
│   │   ├── response_2_183324.png
│   │   └── ...
│   ├── chatgpt/
│   └── gemini/
├── SP_000002/
└── ...
```

## 📖 Documentation

For comprehensive technical documentation, see:
- [Technical Guide (Markdown)](docs/UX_Evaluation_Framework_Technical_Guide.md)
- [Technical Guide (Word)](docs/UX_Evaluation_Framework_Technical_Guide.docx)

## ⚠️ Important Notes

### Data Privacy

This repository **does not include**:
- User feedback data (CSV files)
- Evaluation results with responses
- Screenshots containing potentially sensitive content
- Any PII or proprietary Microsoft data

All data files are excluded via `.gitignore`.

### Usage Guidelines

- This framework is for **internal evaluation purposes only**
- Respect rate limits and terms of service for each chatbot
- Do not use for production traffic or user-facing applications
- Ensure compliance with Microsoft data handling policies

## 🛠️ Development

### Adding New Chatbots

1. Add URL to `CHATBOT_URLS` dictionary
2. Add selectors to `CHATBOT_SELECTORS` dictionary
3. Test with `test_simple_submit.py`

### Extending Evaluation Dimensions

Edit `synthetic_prompt_generator.py` to add new dimensions:

```python
class EvaluationDimension(Enum):
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    # Add new dimensions here
```

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

## 👥 Contributors

- Evaluation Framework Team
- Microsoft AI Quality Engineering

---

**Last Updated:** January 13, 2026
