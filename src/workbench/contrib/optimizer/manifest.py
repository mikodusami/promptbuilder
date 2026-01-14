"""
Optimizer feature manifest - AI-powered prompt optimization.

Requirements: 2.1, 2.2, 2.3, 1.5
"""

from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)


MANIFEST = FeatureManifest(
    name="optimizer",
    display_name="Prompt Optimizer",
    description="AI-powered prompt analysis and improvement",
    icon="🔧",
    color="cyan",
    category=FeatureCategory.AI,
    requires_api_key=True,
    menu_key="o",
)


async def run(ctx: FeatureContext) -> FeatureResult:
    """Run the optimizer feature - analyze and improve prompts."""
    # Import dependencies inside function to avoid module-level import issues
    from rich.prompt import Prompt
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    from .service import OptimizerService
    
    if not ctx.llm_client:
        return FeatureResult(
            success=False,
            error="LLM client not available. Please configure an API key."
        )
    
    ctx.console.print("\n[bold cyan]🔧 Prompt Optimizer[/]")
    ctx.console.print("[dim]Paste your prompt to analyze and optimize.[/]")
    ctx.console.print("[dim]Enter an empty line when done.[/]\n")
    
    # Collect multi-line prompt
    lines = []
    while True:
        line = Prompt.ask("", default="")
        if not line:
            break
        lines.append(line)
    
    prompt = "\n".join(lines)
    
    if not prompt.strip():
        return FeatureResult(success=False, message="No prompt provided")
    
    ctx.console.print("\n[dim]Analyzing prompt...[/]")
    
    optimizer = OptimizerService(ctx.llm_client)
    result = await optimizer.optimize(prompt)
    
    if result.error:
        return FeatureResult(success=False, error=result.error)
    
    # Display results
    ctx.console.print("\n[bold green]✨ Optimized Prompt:[/]")
    ctx.console.print(Panel(result.optimized_prompt, border_style="green"))
    
    # Display scores
    scores_table = Table(box=box.SIMPLE, show_header=False)
    scores_table.add_column("Metric", style="bold")
    scores_table.add_column("Score", justify="center")
    scores_table.add_column("Bar", width=20)
    
    for name, score in [
        ("Clarity", result.clarity_score),
        ("Specificity", result.specificity_score),
        ("Effectiveness", result.effectiveness_score),
    ]:
        bar = "█" * score + "░" * (10 - score)
        color = "green" if score >= 7 else "yellow" if score >= 5 else "red"
        scores_table.add_row(name, f"[{color}]{score}/10[/]", f"[{color}]{bar}[/]")
    
    ctx.console.print("\n[bold]Scores:[/]")
    ctx.console.print(scores_table)
    
    # Display suggestions
    if result.suggestions:
        ctx.console.print("\n[bold]Suggestions:[/]")
        for i, suggestion in enumerate(result.suggestions, 1):
            ctx.console.print(f"  {i}. {suggestion}")
    
    # Display explanation
    if result.explanation:
        ctx.console.print(f"\n[bold]Explanation:[/] {result.explanation}")
    
    return FeatureResult(
        success=True,
        message="Optimization complete",
        data=result
    )
