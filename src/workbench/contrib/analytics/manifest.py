"""
Analytics feature manifest - prompt usage analytics dashboard.

Requirements: 2.1, 2.2, 2.3
"""

from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)


MANIFEST = FeatureManifest(
    name="analytics",
    display_name="Analytics Dashboard",
    description="View prompt usage statistics and insights",
    icon="📊",
    color="yellow",
    category=FeatureCategory.UTILITY,
    requires_api_key=False,
    menu_key="a",
)


def run(ctx: FeatureContext) -> FeatureResult:
    """Run the analytics feature - display usage statistics."""
    # Import dependencies inside function to avoid module-level import issues
    from rich.prompt import Prompt
    from .service import PromptAnalytics
    
    analytics = PromptAnalytics()
    
    while True:
        ctx.console.print("\n[bold yellow]📊 Analytics Dashboard[/]")
        ctx.console.print("1. View summary (30 days)")
        ctx.console.print("2. View cost breakdown")
        ctx.console.print("3. View recent usage")
        ctx.console.print("4. Export data")
        ctx.console.print("5. Back to menu")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5"], default="1")
        
        if choice == "1":
            _show_summary(ctx, analytics)
        elif choice == "2":
            _show_cost_breakdown(ctx, analytics)
        elif choice == "3":
            _show_recent_usage(ctx, analytics)
        elif choice == "4":
            _export_data(ctx, analytics)
        elif choice == "5":
            break
    
    return FeatureResult(success=True, message="Analytics session complete")


def _show_summary(ctx: FeatureContext, analytics) -> None:
    """Display analytics summary."""
    from rich.table import Table
    from rich import box
    
    summary = analytics.get_summary(days=30)
    
    ctx.console.print("\n[bold]📈 30-Day Summary[/]")
    
    # Overview stats
    stats_table = Table(box=box.SIMPLE, show_header=False)
    stats_table.add_column("Metric", style="bold")
    stats_table.add_column("Value", justify="right")
    
    stats_table.add_row("Total Prompts", str(summary.total_prompts))
    stats_table.add_row("Total Tokens", f"{summary.total_tokens:,}")
    stats_table.add_row("Total Cost", f"${summary.total_cost:.4f}")
    stats_table.add_row("Avg Latency", f"{summary.avg_latency_ms:.0f}ms")
    stats_table.add_row("Success Rate", f"{summary.success_rate:.1f}%")
    
    ctx.console.print(stats_table)
    
    # Top techniques
    if summary.top_techniques:
        ctx.console.print("\n[bold]Top Techniques:[/]")
        for technique, count in summary.top_techniques[:5]:
            ctx.console.print(f"  • {technique}: {count} uses")
    
    # Top models
    if summary.top_models:
        ctx.console.print("\n[bold]Top Models:[/]")
        for model, count in summary.top_models[:5]:
            ctx.console.print(f"  • {model}: {count} uses")


def _show_cost_breakdown(ctx: FeatureContext, analytics) -> None:
    """Display cost breakdown."""
    from rich.table import Table
    from rich import box
    
    breakdown = analytics.get_cost_breakdown(days=30)
    
    ctx.console.print("\n[bold]💰 Cost Breakdown (30 days)[/]")
    
    # By provider
    if breakdown["by_provider"]:
        ctx.console.print("\n[bold]By Provider:[/]")
        table = Table(box=box.SIMPLE)
        table.add_column("Provider", style="cyan")
        table.add_column("Cost", justify="right")
        table.add_column("Count", justify="right")
        
        for provider, data in breakdown["by_provider"].items():
            table.add_row(provider, f"${data['cost']:.4f}", str(data['count']))
        
        ctx.console.print(table)
    
    # By model
    if breakdown["by_model"]:
        ctx.console.print("\n[bold]By Model:[/]")
        table = Table(box=box.SIMPLE)
        table.add_column("Model", style="cyan")
        table.add_column("Cost", justify="right")
        table.add_column("Count", justify="right")
        
        for model, data in breakdown["by_model"].items():
            table.add_row(model, f"${data['cost']:.4f}", str(data['count']))
        
        ctx.console.print(table)


def _show_recent_usage(ctx: FeatureContext, analytics) -> None:
    """Display recent usage records."""
    from rich.table import Table
    from rich import box
    
    records = analytics.get_recent_usage(limit=10)
    
    if not records:
        ctx.console.print("[dim]No usage records yet.[/]")
        return
    
    ctx.console.print("\n[bold]Recent Usage:[/]")
    
    table = Table(box=box.ROUNDED, border_style="yellow")
    table.add_column("Time", style="dim", width=16)
    table.add_column("Technique", style="cyan")
    table.add_column("Model")
    table.add_column("Tokens", justify="right")
    table.add_column("Cost", justify="right")
    table.add_column("Status", justify="center")
    
    for record in records:
        timestamp = record.timestamp[:16] if record.timestamp else ""
        tokens = record.input_tokens + record.output_tokens
        status = "[green]✓[/]" if record.success else "[red]✗[/]"
        
        table.add_row(
            timestamp,
            record.technique,
            record.model or "-",
            str(tokens),
            f"${record.cost:.4f}",
            status
        )
    
    ctx.console.print(table)


def _export_data(ctx: FeatureContext, analytics) -> None:
    """Export analytics data."""
    from rich.prompt import Prompt
    
    days = Prompt.ask("Export data for how many days?", default="30")
    
    try:
        days_int = int(days)
        data = analytics.export_data(days=days_int)
        
        # Save to file
        from pathlib import Path
        export_path = Path.cwd() / f"analytics_export_{days_int}d.json"
        
        with open(export_path, 'w') as f:
            f.write(data)
        
        ctx.console.print(f"[green]✓ Exported to {export_path}[/]")
        
    except ValueError:
        ctx.console.print("[red]Invalid number of days[/]")
    except Exception as e:
        ctx.console.print(f"[red]Export failed: {e}[/]")
