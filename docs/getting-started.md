# Getting Started

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/promptbuilder.git
cd promptbuilder
```

2. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python main.py
```

## First Launch

When you first launch Prompt Builder, you'll see an interactive menu. Use arrow keys (↑↓) to navigate and Enter to select:

```
⚡ PROMPT BUILDER ⚡
Modern Prompt Engineering Techniques

Main Menu (↑↓ to navigate, Enter to select)

  ✨ New Prompt         - Create a new prompt manually
  🔗 Combine            - Chain multiple techniques
  📦 Templates          - Use custom templates
  📜 History            - Browse recent prompts
  ⭐ Favorites          - View favorite prompts
  🔍 Search             - Search saved prompts
  👁️  Preview Mode [OFF] - Live prompt preview
  🤖 AI Features [●]    - Optimize, generate, test, chains
  ⚙️  Settings           - API keys & configuration
  🚪 Quit               - Exit the builder
```

## Setting Up API Keys (Optional)

AI features require at least one LLM provider API key. You can set these up in Settings:

1. Select ⚙️ Settings from the main menu
2. Choose a provider to configure:
   - 🔑 Set OpenAI API Key
   - 🔑 Set Anthropic API Key
   - 🔑 Set Google API Key
3. Enter your API key

Alternatively, set environment variables:

```bash
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
export GOOGLE_API_KEY="your-key-here"
```

## Basic Workflow

1. Select ✨ New Prompt from the main menu
2. Choose a technique (Chain of Thought, Few-Shot, etc.)
3. Enter your task/question
4. Add optional context
5. Configure technique-specific options
6. View the generated prompt
7. Copy to clipboard, save to file, or add to favorites

## Tips

- Enable Preview Mode to see your prompt build in real-time
- All prompts are automatically saved to history
- Use tags to organize your prompts for easy searching
- The filled dot (●) next to AI Features indicates API keys are configured
- Use arrow keys to navigate menus, Enter to select
