"""
History feature manifest - manages prompt history and favorites.

Requirements: 2.1, 2.2, 2.3
"""

from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)


MANIFEST = FeatureManifest(
    name="history",
    display_name="Prompt History",
    description="View and manage saved prompts and favorites",
    icon="📜",
    color="blue",
    category=FeatureCategory.STORAGE,
    requires_api_key=False,
    menu_key="h",
)


def run(ctx: FeatureContext) -> FeatureResult:
    """Run the history feature - display and manage prompt history."""
    # Import dependencies inside function to avoid module-level import issues
    from rich.prompt import Prompt
    from rich.table import Table
    from rich import box
    from .service import HistoryService
    
    history = HistoryService()
    
    while True:
        ctx.console.print("\n[bold blue]📜 Prompt History[/]")
        ctx.console.print("1. View recent prompts")
        ctx.console.print("2. View favorites")
        ctx.console.print("3. Search prompts")
        ctx.console.print("4. Back to menu")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4"], default="1")
        
        if choice == "1":
            prompts = history.list_recent(limit=10)
            if not prompts:
                ctx.console.print("[dim]No prompts saved yet.[/]")
                continue
            _display_prompts(ctx, prompts, "Recent Prompts")
            _handle_prompt_action(ctx, history, prompts)
            
        elif choice == "2":
            prompts = history.list_favorites()
            if not prompts:
                ctx.console.print("[dim]No favorites yet.[/]")
                continue
            _display_prompts(ctx, prompts, "Favorite Prompts")
            _handle_prompt_action(ctx, history, prompts)
            
        elif choice == "3":
            query = Prompt.ask("Search query")
            if query:
                prompts = history.search(query)
                if not prompts:
                    ctx.console.print(f"[dim]No prompts matching '{query}'[/]")
                    continue
                _display_prompts(ctx, prompts, f"Search Results: {query}")
                _handle_prompt_action(ctx, history, prompts)
                
        elif choice == "4":
            break
    
    return FeatureResult(success=True, message="History browsed")


def _display_prompts(ctx: FeatureContext, prompts: list, title: str) -> None:
    """Display a table of prompts."""
    from rich.table import Table
    from rich import box
    
    table = Table(title=title, box=box.ROUNDED, border_style="blue")
    table.add_column("#", style="dim", width=4)
    table.add_column("Technique", style="cyan", width=15)
    table.add_column("Task", width=30)
    table.add_column("⭐", width=3)
    table.add_column("Date", style="dim", width=12)
    
    for i, p in enumerate(prompts, 1):
        star = "⭐" if p.is_favorite else ""
        date = p.created_at.strftime("%Y-%m-%d") if p.created_at else ""
        table.add_row(str(i), p.technique, p.task[:30], star, date)
    
    ctx.console.print(table)


def _handle_prompt_action(ctx: FeatureContext, history, prompts: list) -> None:
    """Handle actions on displayed prompts."""
    from rich.prompt import Prompt
    
    if not prompts:
        return
        
    ctx.console.print("\n[dim]Enter # to view, 'f#' to toggle favorite, 'd#' to delete, or Enter to skip[/]")
    action = Prompt.ask("Action", default="")
    
    if not action:
        return
        
    try:
        if action.startswith('f'):
            idx = int(action[1:]) - 1
            if 0 <= idx < len(prompts):
                new_status = history.toggle_favorite(prompts[idx].id)
                status_text = "added to" if new_status else "removed from"
                ctx.console.print(f"[green]Prompt {status_text} favorites[/]")
                
        elif action.startswith('d'):
            idx = int(action[1:]) - 1
            if 0 <= idx < len(prompts):
                if history.delete(prompts[idx].id):
                    ctx.console.print("[red]Prompt deleted[/]")
                    
        else:
            idx = int(action) - 1
            if 0 <= idx < len(prompts):
                prompt = prompts[idx]
                ctx.console.print(f"\n[bold]Technique:[/] {prompt.technique}")
                ctx.console.print(f"[bold]Task:[/] {prompt.task}")
                ctx.console.print(f"\n[bold]Prompt:[/]\n{prompt.prompt}")
                if prompt.tags:
                    ctx.console.print(f"\n[bold]Tags:[/] {', '.join(prompt.tags)}")
    except (ValueError, IndexError):
        ctx.console.print("[red]Invalid selection[/]")
