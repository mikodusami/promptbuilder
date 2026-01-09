# 🚀 Prompt Builder

A powerful command-line tool for creating exceptional prompts using modern prompt engineering techniques. Features AI-powered optimization, multi-model testing, prompt chains, collaboration tools, and more.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📑 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
  - [Main Menu](#main-menu)
  - [Creating Prompts](#creating-prompts)
  - [AI Features](#ai-features)
- [Prompt Engineering Techniques](#-prompt-engineering-techniques)
- [Advanced Features](#-advanced-features)
- [Programmatic Usage](#-programmatic-usage)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### Core Features (No API Key Required)

| Feature                   | Description                                                                                   |
| ------------------------- | --------------------------------------------------------------------------------------------- |
| **7 Prompt Techniques**   | Chain of Thought, Few-Shot, Role-Based, Structured, ReAct, Tree of Thoughts, Self-Consistency |
| **Prompt History**        | SQLite-backed storage with search, tags, and favorites                                        |
| **Custom Templates**      | YAML-based templates with variables                                                           |
| **Token Counter**         | Accurate token counting and cost estimates for multiple models                                |
| **Export Formats**        | JSON, Markdown, LangChain, LlamaIndex, and more                                               |
| **Clipboard Integration** | Auto-copy prompts to clipboard                                                                |
| **Live Preview**          | See prompts build in real-time                                                                |
| **Prompt Combiner**       | Chain multiple techniques together                                                            |

### AI-Powered Features (Requires API Key)

| Feature                         | Description                                              |
| ------------------------------- | -------------------------------------------------------- |
| **Natural Language Generation** | Describe tasks in plain English, get optimal prompts     |
| **Prompt Optimizer**            | AI analyzes and improves your prompts with scores        |
| **Multi-Model Testing**         | Test prompts across OpenAI, Anthropic, and Google models |
| **Prompt Chains**               | Multi-step workflows with output chaining                |
| **Sharing & Collaboration**     | Export/import prompt libraries with share codes          |
| **Analytics Dashboard**         | Track usage, costs, and performance                      |

---

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/prompt-builder.git
cd prompt-builder
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install
pip install -r requirements.txt

# Run
python main.py
```

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/prompt-builder.git
cd prompt-builder
```

### Step 2: Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Minimal Installation (Core features only)

```bash
pip install rich pyyaml tiktoken
```

---

## ⚙️ Configuration

### API Keys (Optional)

AI features require at least one LLM provider. You can configure keys in three ways:

#### Option 1: Environment Variables

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AI..."
```

#### Option 2: .env File

```bash
cp .env.example .env
# Edit .env with your keys
```

#### Option 3: In-App Settings

Press `c` in the main menu to access Settings and enter your API keys interactively.

### Supported Providers

| Provider      | Models                                           | Environment Variable |
| ------------- | ------------------------------------------------ | -------------------- |
| **OpenAI**    | gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo  | `OPENAI_API_KEY`     |
| **Anthropic** | claude-3-5-sonnet, claude-3-opus, claude-3-haiku | `ANTHROPIC_API_KEY`  |
| **Google**    | gemini-1.5-pro, gemini-1.5-flash, gemini-pro     | `GOOGLE_API_KEY`     |

> **Note:** You only need ONE provider configured to use AI features.

---

## 📖 Usage Guide

### Starting the Application

```bash
python main.py
```

### Main Menu

```
⚡ PROMPT BUILDER ⚡
Modern Prompt Engineering Techniques

Main Menu:
  [n] ✨ New Prompt      - Create a new prompt
  [m] 🔗 Combine         - Chain multiple techniques
  [t] 📦 Templates       - Use custom templates
  [h] 📜 History         - Browse recent prompts
  [f] ⭐ Favorites       - View favorite prompts
  [s] 🔍 Search          - Search saved prompts
  [p] 👁️  Preview Mode   - Toggle live preview
  [a] 🤖 AI Features ●   - Optimize, generate, test, chains
  [c] ⚙️  Settings        - API keys & configuration
  [q] 🚪 Quit            - Exit
```

### Creating Prompts

1. Press `n` for New Prompt
2. Select a technique (1-7)
3. Enter your task/question
4. Add optional context
5. Configure technique-specific options
6. Add constraints if needed
7. Prompt is generated and auto-copied to clipboard!

### AI Features

Press `a` to access AI-powered features:

| Key | Feature       | Description                             |
| --- | ------------- | --------------------------------------- |
| `g` | **Generate**  | Describe what you want in plain English |
| `o` | **Optimize**  | Paste a prompt to get AI improvements   |
| `t` | **Test**      | Test prompts across multiple models     |
| `c` | **Chains**    | Create and run multi-step workflows     |
| `s` | **Share**     | Export/import prompt libraries          |
| `a` | **Analytics** | View usage statistics                   |

---

## 🧠 Prompt Engineering Techniques

| #   | Technique             | Best For                | Description                           |
| --- | --------------------- | ----------------------- | ------------------------------------- |
| 1   | **Chain of Thought**  | Complex reasoning, math | Step-by-step problem solving          |
| 2   | **Few-Shot Learning** | Pattern recognition     | Learn from provided examples          |
| 3   | **Role-Based**        | Domain expertise        | Assign expert persona                 |
| 4   | **Structured Output** | Data extraction, APIs   | Request specific formats (JSON, etc.) |
| 5   | **ReAct**             | Multi-step tasks        | Reasoning + Acting framework          |
| 6   | **Tree of Thoughts**  | Creative problems       | Explore multiple solution paths       |
| 7   | **Self-Consistency**  | High-stakes decisions   | Multiple solutions for consensus      |

---

## 🔧 Advanced Features

### Natural Language Generation

```
🪄 What do you want to do?
> Help me write unit tests for a Python REST API

Technique: role (confidence: 85%)
Generated prompt ready to use!
```

### Prompt Optimization

```
📊 Analysis Scores:
  Clarity:       ████████░░ 8/10
  Specificity:   ██████░░░░ 6/10
  Effectiveness: ███████░░░ 7/10

💡 Suggestions:
  • Be more specific about the expected output format
  • Add constraints for edge cases
  • Include example inputs
```

### Prompt Chains

Create multi-step workflows where each step's output feeds into the next:

```
Chain: research_and_summarize
  Step 1: Research → points
  Step 2: Expand → details
  Step 3: Summarize → final output
```

### Custom Templates

Create reusable templates in `~/.promptbuilder/templates.yaml`:

```yaml
templates:
  code_review:
    name: "Code Review"
    description: "Thorough code review"
    icon: "🔍"
    color: "cyan"
    template: |
      Review this code for:
      1. Bugs and edge cases
      2. Performance issues
      3. Security vulnerabilities

      Code: {task}
    variables:
      - task
```

### Export Formats

Export prompts in multiple formats:

- **JSON** - API-ready format
- **Markdown** - Documentation
- **LangChain** - LangChain compatible
- **LlamaIndex** - LlamaIndex compatible
- **Plain Text** - Simple text file

---

## 💻 Programmatic Usage

```python
from main import quick_build

# Chain of Thought
prompt = quick_build("cot", task="Solve this optimization problem")

# Role-Based
prompt = quick_build(
    "role",
    task="Review this code for security issues",
    role="senior security engineer"
)

# Few-Shot with examples
prompt = quick_build(
    "few_shot",
    task="Classify the sentiment",
    examples=[
        {"input": "I love this!", "output": "positive"},
        {"input": "Terrible.", "output": "negative"}
    ]
)

# Structured output
prompt = quick_build(
    "structured",
    task="Extract entities from this text",
    output_format="JSON"
)
```

---

## 📁 Project Structure

```
prompt-builder/
├── main.py              # CLI application
├── prompt_history.py    # SQLite history storage
├── template_manager.py  # YAML template system
├── token_counter.py     # Token counting & costs
├── export_formats.py    # Export functionality
├── clipboard_utils.py   # Clipboard integration
├── api_config.py        # API key management
├── llm_client.py        # LLM provider client
├── prompt_optimizer.py  # AI optimization
├── prompt_testing.py    # Multi-model testing
├── prompt_chains.py     # Workflow chains
├── prompt_sharing.py    # Library sharing
├── context_manager.py   # Context window handling
├── analytics.py         # Usage analytics
├── natural_language_gen.py  # NL prompt generation
├── plugin_system.py     # Plugin architecture
├── requirements.txt
└── README.md
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with ❤️ for the prompt engineering community
</p>
