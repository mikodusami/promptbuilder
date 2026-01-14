# Programmatic Usage

Use Prompt Builder as a library in your Python projects.

## Quick Build Function

The simplest way to generate prompts programmatically:

```python
from main import quick_build

# Chain of Thought
prompt = quick_build(
    technique="cot",
    task="Calculate the compound interest on $10,000 at 5% for 3 years"
)

# Role-Based
prompt = quick_build(
    technique="role",
    task="Review this Python code for security issues",
    role="senior security engineer",
    context="Web application handling user authentication"
)

# Few-Shot
prompt = quick_build(
    technique="few_shot",
    task="Classify this customer feedback",
    examples=[
        {"input": "Great product!", "output": "positive"},
        {"input": "Terrible service", "output": "negative"},
        {"input": "It's okay", "output": "neutral"}
    ]
)

# Structured Output
prompt = quick_build(
    technique="structured",
    task="Extract contact information from this text",
    output_format="JSON with fields: name, email, phone",
    constraints=["Include confidence scores", "Handle missing fields"]
)
```

## Using the PromptBuilder Class

For more control:

```python
from main import PromptBuilder, PromptConfig, PromptType

builder = PromptBuilder()

# Create configuration
config = PromptConfig(
    task="Explain quantum entanglement",
    context="For a high school physics class",
    role="physics teacher",
    constraints=["Use analogies", "Avoid complex math"]
)

# Build prompt
prompt = builder.build(PromptType.ROLE_BASED, config)
print(prompt)
```

## Available Techniques

```python
from main import PromptType

# All available techniques
techniques = [
    PromptType.CHAIN_OF_THOUGHT,    # "cot"
    PromptType.FEW_SHOT,            # "few_shot"
    PromptType.ROLE_BASED,          # "role"
    PromptType.STRUCTURED,          # "structured"
    PromptType.REACT,               # "react"
    PromptType.TREE_OF_THOUGHTS,    # "tot"
    PromptType.SELF_CONSISTENCY,    # "self_consistency"
]
```

## Using Services Directly

### History Service

```python
from src.workbench.contrib.history.service import HistoryService

history = HistoryService()

# Save a prompt
prompt_id = history.save(
    technique="role",
    task="Code review",
    prompt="You are a senior developer...",
    tags=["python", "review"]
)

# Get a prompt
saved = history.get(prompt_id)
print(saved.prompt)

# List recent
recent = history.list_recent(10)

# Search
results = history.search("python")

# Favorites
history.toggle_favorite(prompt_id)
favorites = history.list_favorites()

# Delete
history.delete(prompt_id)
```

### Template Service

```python
from src.workbench.contrib.templates.service import TemplateService

templates = TemplateService()

# List templates
for t in templates.list_templates():
    print(f"{t.name}: {t.description}")

# Get template
template = templates.get_template("code_review")

# Build prompt from template
prompt = templates.build_prompt("code_review", {
    "task": "Review this function",
    "context": "Python web application"
})
```

### Token Counter

```python
from src.services.token_counter import TokenCounter

counter = TokenCounter()

# Count tokens
tokens = counter.count_tokens("Your prompt here", model="gpt-4o")
print(f"Tokens: {tokens}")

# Estimate cost
estimate = counter.estimate_cost("Your prompt here", model="gpt-4o")
print(f"Cost: {estimate.formatted_cost}")

# Compare across models
estimates = counter.estimate_all_models("Your prompt here")
for e in estimates:
    print(f"{e.model}: {e.token_count} tokens, {e.formatted_cost}")
```

### LLM Client

```python
import asyncio
from src.services.llm.client import LLMClient
from src.services.llm.config import LLMConfig

config = LLMConfig()
client = LLMClient(config)

async def generate():
    response = await client.complete(
        prompt="Explain machine learning in one sentence",
        provider="openai",
        model="gpt-4o-mini",
        max_tokens=100,
        temperature=0.7
    )

    if response.error:
        print(f"Error: {response.error}")
    else:
        print(response.content)
        print(f"Tokens: {response.input_tokens + response.output_tokens}")

asyncio.run(generate())
```

### Prompt Optimizer

```python
import asyncio
from src.workbench.contrib.optimizer.service import OptimizerService
from src.services.llm.client import LLMClient

client = LLMClient()
optimizer = OptimizerService(client)

async def optimize():
    result = await optimizer.optimize(
        prompt="Write code to sort list",
        context="Python programming"
    )

    print(f"Clarity: {result.clarity_score}/10")
    print(f"Specificity: {result.specificity_score}/10")
    print(f"Suggestions: {result.suggestions}")
    print(f"Optimized: {result.optimized_prompt}")

asyncio.run(optimize())
```

### Prompt Chains

```python
import asyncio
from src.workbench.contrib.chains.service import ChainService
from src.workbench.contrib.chains.common import ChainStep, PromptChain
from src.services.llm.client import LLMClient

client = LLMClient()
executor = ChainService(client)

# Create a chain
chain = PromptChain(
    name="research",
    description="Research and summarize",
    steps=[
        ChainStep(
            name="research",
            prompt_template="List 5 facts about {topic}",
            output_key="facts"
        ),
        ChainStep(
            name="summarize",
            prompt_template="Summarize these facts: {facts}",
            output_key="summary"
        )
    ]
)

async def run_chain():
    result = await executor.execute(
        chain,
        input_context={"topic": "quantum computing"}
    )

    print(f"Success: {result.success}")
    print(f"Steps: {result.steps_completed}/{result.total_steps}")
    print(f"Output: {result.final_output}")

asyncio.run(run_chain())
```

### Analytics

```python
from src.workbench.contrib.analytics.service import PromptAnalytics

analytics = PromptAnalytics()

# Record usage
analytics.record_usage(
    technique="role",
    provider="openai",
    model="gpt-4o",
    input_tokens=150,
    output_tokens=500,
    cost=0.0065,
    latency_ms=1234,
    success=True,
    tags=["project-x"]
)

# Get summary
summary = analytics.get_summary(days=30)
print(f"Total prompts: {summary.total_prompts}")
print(f"Total cost: ${summary.total_cost:.2f}")

# Export data
json_data = analytics.export_data(days=30)
```

## Integration Example

Complete example integrating multiple services:

```python
import asyncio
from main import quick_build
from src.services.llm.client import LLMClient
from src.services.token_counter import TokenCounter
from src.workbench.contrib.history.service import HistoryService
from src.workbench.contrib.analytics.service import PromptAnalytics

async def main():
    # Initialize services
    client = LLMClient()
    counter = TokenCounter()
    history = HistoryService()
    analytics = PromptAnalytics()

    # Build prompt
    prompt = quick_build(
        technique="role",
        task="Explain recursion with an example",
        role="computer science professor"
    )

    # Check tokens
    tokens = counter.count_tokens(prompt)
    print(f"Prompt tokens: {tokens}")

    # Execute
    response = await client.complete(prompt, max_tokens=500)

    if response.error:
        print(f"Error: {response.error}")
        return

    # Save to history
    prompt_id = history.save(
        technique="role",
        task="Explain recursion",
        prompt=prompt,
        tags=["teaching", "cs"]
    )

    # Record analytics
    analytics.record_usage(
        technique="role",
        provider=response.provider,
        model=response.model,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        success=True
    )

    print(f"Response: {response.content}")
    print(f"Saved as ID: {prompt_id}")

asyncio.run(main())
```

## Using the Discovery System

Access features through the workbench discovery system:

```python
from src.workbench import get_registry, CLIIntegration, FeatureCategory

# Get the feature registry
registry = get_registry()

# Query features
optimizer = registry.get("optimizer")
ai_features = registry.list_by_category(FeatureCategory.AI)
all_features = registry.list_all()

# Check what's available
for feature in ai_features:
    m = feature.manifest
    print(f"{m.icon} {m.display_name}: {m.description}")
```
