"""
Natural Language Generation feature manifest - generate prompts from descriptions.

Requirements: 2.1, 2.2, 2.3
"""

from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)


MANIFEST = FeatureManifest(
    name="nlgen",
    display_name="Natural Language Generator",
    description="Generate optimized prompts from plain English descriptions",
    icon="💬",
    color="bright_magenta",
    category=FeatureCategory.AI,
    requires_api_key=True,
    menu_key="n",
)


async def run(ctx: FeatureContext) -> FeatureResult:
    """Run the nlgen feature - generate prompts from descriptions."""
    # Import dependencies inside function to avoid module-level import issues
    from rich.prompt import Prompt
    from rich.panel import Panel
    from .service import NaturalLanguageGenerator
    
    if not ctx.llm_client:
        return FeatureResult(
            success=False,
            error="LLM client not available. Please configure an API key."
        )
    
    generator = NaturalLanguageGenerator(ctx.llm_client)
    
    ctx.console.print("\n[bold bright_magenta]💬 Natural Language Prompt Generator[/]")
    ctx.console.print("[dim]Describe what you want to accomplish in plain English.[/]\n")
    
    description = Prompt.ask("What do you want to do?")
    
    if not description.strip():
        return FeatureResult(success=False, message="No description provided")
    
    # Optional context
    ctx.console.print("[dim]Any additional context? (press Enter to skip)[/]")
    context = Prompt.ask("Context", default="")
    
    ctx.console.print("\n[dim]Generating optimized prompt...[/]\n")
    
    result = await generator.generate(
        description=description,
        context=context if context else None
    )
    
    if result.error:
        return FeatureResult(success=False, error=result.error)
    
    # Display results
    ctx.console.print(f"[bold]Recommended Technique:[/] [cyan]{result.technique}[/]")
    ctx.console.print(f"[bold]Confidence:[/] {result.confidence * 100:.0f}%")
    
    ctx.console.print("\n[bold green]✨ Generated Prompt:[/]")
    ctx.console.print(Panel(result.prompt, border_style="green"))
    
    if result.explanation:
        ctx.console.print(f"\n[bold]Why this approach:[/] {result.explanation}")
    
    # Show alternatives
    if result.alternatives:
        ctx.console.print("\n[bold]Alternative Prompts:[/]")
        for i, alt in enumerate(result.alternatives, 1):
            ctx.console.print(f"\n[dim]Alternative {i}:[/]")
            # Truncate long alternatives
            display_alt = alt if len(alt) <= 200 else alt[:200] + "..."
            ctx.console.print(f"  {display_alt}")
    
    # Offer to copy
    if Prompt.ask("\nCopy to clipboard?", choices=["y", "n"], default="y") == "y":
        try:
            from src.platform.clipboard import copy_to_clipboard
            copy_to_clipboard(result.prompt)
            ctx.console.print("[green]✓ Copied to clipboard[/]")
        except Exception:
            ctx.console.print("[yellow]Could not copy to clipboard[/]")
    
    return FeatureResult(
        success=True,
        message="Prompt generated",
        data=result
    )
