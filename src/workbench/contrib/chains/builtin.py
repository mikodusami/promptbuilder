"""
Chains feature - built-in chain templates.
"""

from .common import ChainStep, PromptChain


BUILTIN_CHAINS = {
    "research_and_summarize": PromptChain(
        name="research_and_summarize",
        description="Research a topic and create a summary",
        steps=[
            ChainStep(
                name="research",
                prompt_template="List 5 key points about: {topic}",
                output_key="points"
            ),
            ChainStep(
                name="expand",
                prompt_template="Expand on these points:\n{points}",
                output_key="expanded"
            ),
            ChainStep(
                name="summarize",
                prompt_template="Create a concise summary:\n{expanded}",
                output_key="summary"
            )
        ]
    ),
    "code_review_chain": PromptChain(
        name="code_review_chain",
        description="Multi-step code review",
        steps=[
            ChainStep(
                name="analyze",
                prompt_template="Analyze this code for issues:\n```\n{code}\n```",
                output_key="analysis"
            ),
            ChainStep(
                name="suggest",
                prompt_template="Based on:\n{analysis}\n\nSuggest improvements.",
                output_key="suggestions"
            ),
            ChainStep(
                name="refactor",
                prompt_template="Refactor applying:\n{suggestions}\n\nCode:\n```\n{code}\n```",
                output_key="refactored"
            )
        ]
    )
}
