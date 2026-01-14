# AI Features

AI-powered features require at least one LLM provider API key configured.

## Accessing AI Features

Select 🤖 AI Features from the main menu to access AI-powered features.

```
🤖 AI Features (↑↓ to navigate, Enter to select)

  🪄 Generate from Description  - Describe task in plain English
  ✨ Optimize Prompt            - AI-powered prompt improvement
  🧪 Test Prompt                - Test against multiple models
  ⛓️  Prompt Chains              - Multi-step workflows
  📊 Analytics                  - View usage statistics
  🔙 Back                       - Return to main menu
```

## Generate from Description 🪄

Create prompts by describing what you want in plain English.

### How to Use

1. Select 🪄 Generate from Description from AI Features menu
2. Describe your task naturally
3. Optionally add context
4. AI generates the optimal prompt with the best technique

### Example

```
📝 What do you want to do?
> I need to analyze customer reviews and categorize them by sentiment

Additional context (optional):
> For an e-commerce platform, reviews are in English

Generating prompt...

Technique: few_shot (confidence: 85%)
The task involves classification which benefits from examples...

╔══════════════════════════════════════════════════════════════╗
║ 📝 Generated Prompt                                          ║
╠══════════════════════════════════════════════════════════════╣
║ Analyze the following customer review and categorize it...   ║
╚══════════════════════════════════════════════════════════════╝
```

### How It Works

The AI:

1. Analyzes your description
2. Selects the best prompt engineering technique
3. Generates an optimized prompt
4. Provides confidence score and explanation

---

## Optimize Prompt ✨

Improve existing prompts using AI analysis.

### How to Use

1. Select ✨ Optimize Prompt from AI Features menu
2. Paste your existing prompt
3. Optionally describe what it's for
4. AI analyzes and improves it

### Example

```
📝 Your prompt:
> Write code to sort a list

What's this prompt for? (optional):
> Getting Python code from an AI assistant

Analyzing and optimizing...

📊 Analysis Scores:
  Clarity:       ████░░░░░░ 4/10
  Specificity:   ███░░░░░░░ 3/10
  Effectiveness: ████░░░░░░ 4/10

💡 Suggestions:
  • Specify the programming language
  • Describe the type of data in the list
  • Mention any performance requirements
  • Include expected input/output examples

Optimized prompt generated...
```

### Scores Explained

| Score         | Meaning                                       |
| ------------- | --------------------------------------------- |
| Clarity       | How clear and unambiguous the prompt is       |
| Specificity   | How detailed and precise the requirements are |
| Effectiveness | How likely to produce desired results         |

---

## Test Prompt 🧪

Test your prompts across multiple LLM models to compare responses.

### How to Use

1. Select 🧪 Test Prompt from AI Features menu
2. Enter the prompt to test
3. AI runs it against available models
4. Compare responses side-by-side

### Example

```
📝 Prompt to test:
> Explain quantum computing in one paragraph

Available models:
  [1] openai: gpt-4o
  [2] openai: gpt-4o-mini
  [3] anthropic: claude-3-5-sonnet

Testing across models...

📊 Results:

╭─ openai/gpt-4o ───────────────────────────────────────────────╮
│ Quantum computing harnesses the principles of quantum         │
│ mechanics to process information in fundamentally different   │
│ ways than classical computers...                              │
├───────────────────────────────────────────────────────────────┤
│ 245 tokens                                                    │
╰───────────────────────────────────────────────────────────────╯

╭─ anthropic/claude-3-5-sonnet ─────────────────────────────────╮
│ Quantum computing represents a paradigm shift in computation  │
│ that leverages quantum mechanical phenomena...                │
├───────────────────────────────────────────────────────────────┤
│ 198 tokens                                                    │
╰───────────────────────────────────────────────────────────────╯
```

### Use Cases

- Compare response quality across models
- Find the most cost-effective model for your use case
- Verify prompt works consistently
- Benchmark response times

---

## Requirements

### Supported Providers

| Provider  | Models                                             | Environment Variable |
| --------- | -------------------------------------------------- | -------------------- |
| OpenAI    | gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo    | `OPENAI_API_KEY`     |
| Anthropic | claude-3-5-sonnet, claude-3-opus, claude-3-haiku   | `ANTHROPIC_API_KEY`  |
| Google    | gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash | `GOOGLE_API_KEY`     |

### Setting Up

1. Get API keys from your provider(s)
2. Set via environment variables or Settings menu
3. The green dot (●) indicates AI features are available

### Cost Considerations

- AI features make API calls that may incur costs
- Token estimates are shown before generation
- Use gpt-4o-mini or claude-3-haiku for lower costs
- Analytics tracks your usage and costs
