"""
Testing feature manifest - test prompts across multiple LLM models.

Requirements: 2.1, 2.2, 2.3
"""

from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)


MANIFEST = FeatureManifest(
    name="testing",
    display_name="Prompt Testing",
    description="Test prompts across multiple LLM models",
    icon="🧪",
    color="red",
    category=FeatureCategory.AI,
    requires_api_key=True,
    menu_key="x",
)


async def run(ctx: FeatureContext) -> FeatureResult:
    """Run the testing feature - test prompts across models."""
    # Import dependencies inside function to avoid module-level import issues
    from rich.prompt import Prompt
    from .service import TestingService
    
    if not ctx.llm_client:
        return FeatureResult(
            success=False,
            error="LLM client not available. Please configure an API key."
        )
    
    testing_service = TestingService(ctx.llm_client)
    
    ctx.console.print("\n[bold red]🧪 Prompt Testing[/]")
    ctx.console.print("[dim]Test your prompt across multiple models.[/]")
    ctx.console.print("[dim]Enter your prompt (empty line to finish):[/]\n")
    
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
    
    # Get available models
    available_models = ctx.llm_client.config.get_available_models()
    
    if not available_models:
        return FeatureResult(
            success=False,
            error="No models available. Please configure API keys."
        )
    
    # Let user select models to test
    ctx.console.print("\n[bold]Available Models:[/]")
    for i, (provider, model) in enumerate(available_models[:6], 1):
        ctx.console.print(f"  {i}. [{provider}] {model}")
    
    ctx.console.print("\n[dim]Enter model numbers to test (comma-separated), or 'all' for first 3:[/]")
    selection = Prompt.ask("Models", default="all")
    
    if selection.lower() == "all":
        models_to_test = available_models[:3]
    else:
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(",")]
            models_to_test = [available_models[i] for i in indices if 0 <= i < len(available_models)]
        except (ValueError, IndexError):
            models_to_test = available_models[:3]
    
    if not models_to_test:
        return FeatureResult(success=False, message="No models selected")
    
    ctx.console.print(f"\n[dim]Testing across {len(models_to_test)} models...[/]\n")
    
    # Run tests
    results = await testing_service.run_across_models(prompt, models_to_test)
    
    # Display results
    _display_results(ctx, results)
    
    return FeatureResult(
        success=True,
        message=f"Tested across {len(results)} models",
        data=results
    )


def _display_results(ctx: FeatureContext, results: list) -> None:
    """Display test results in a table."""
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    
    ctx.console.print("[bold]Test Results:[/]\n")
    
    # Summary table
    table = Table(box=box.ROUNDED, border_style="red")
    table.add_column("Provider", style="cyan")
    table.add_column("Model")
    table.add_column("Status", justify="center")
    table.add_column("Score", justify="center")
    table.add_column("Latency", justify="right")
    table.add_column("Tokens", justify="right")
    
    for result in results:
        status = "[green]✓ Pass[/]" if result.passed else "[red]✗ Fail[/]"
        if result.error:
            status = "[yellow]⚠ Error[/]"
        
        score_color = "green" if result.score >= 80 else "yellow" if result.score >= 50 else "red"
        
        table.add_row(
            result.provider,
            result.model,
            status,
            f"[{score_color}]{result.score:.0f}%[/]",
            f"{result.latency_ms}ms",
            str(result.tokens_used)
        )
    
    ctx.console.print(table)
    
    # Show responses
    ctx.console.print("\n[bold]Responses:[/]")
    for result in results:
        ctx.console.print(f"\n[bold cyan][{result.provider}] {result.model}[/]")
        if result.error:
            ctx.console.print(f"[red]Error: {result.error}[/]")
        else:
            # Truncate long responses
            response = result.response
            if len(response) > 500:
                response = response[:500] + "..."
            ctx.console.print(Panel(response, border_style="dim"))
