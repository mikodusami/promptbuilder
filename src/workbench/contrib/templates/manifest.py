"""
Templates feature manifest - custom prompt template management.

Requirements: 2.1, 2.2, 2.3
"""

from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)


MANIFEST = FeatureManifest(
    name="templates",
    display_name="Custom Templates",
    description="Manage and use custom prompt templates",
    icon="📋",
    color="green",
    category=FeatureCategory.CORE,
    requires_api_key=False,
    menu_key="t",
)


def run(ctx: FeatureContext) -> FeatureResult:
    """Run the templates feature - manage and use custom templates."""
    # Import dependencies inside function to avoid module-level import issues
    from rich.prompt import Prompt
    from .service import TemplateService
    
    template_service = TemplateService()
    
    while True:
        ctx.console.print("\n[bold green]📋 Custom Templates[/]")
        ctx.console.print("1. List templates")
        ctx.console.print("2. Use a template")
        ctx.console.print("3. View template details")
        ctx.console.print("4. Open config file")
        ctx.console.print("5. Back to menu")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5"], default="1")
        
        if choice == "1":
            _list_templates(ctx, template_service)
        elif choice == "2":
            _use_template(ctx, template_service)
        elif choice == "3":
            _view_template(ctx, template_service)
        elif choice == "4":
            config_path = template_service.get_config_path()
            ctx.console.print(f"\n[bold]Config file:[/] {config_path}")
            ctx.console.print("[dim]Edit this file to add or modify templates.[/]")
        elif choice == "5":
            break
    
    return FeatureResult(success=True, message="Templates session complete")


def _list_templates(ctx: FeatureContext, service) -> None:
    """List all available templates."""
    from rich.table import Table
    from rich import box
    
    templates = service.list_templates()
    
    if not templates:
        ctx.console.print("[dim]No templates available. Add some to templates.yaml[/]")
        return
    
    table = Table(title="Available Templates", box=box.ROUNDED, border_style="green")
    table.add_column("", width=3)
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Variables", style="dim")
    
    for tpl in templates:
        vars_str = ", ".join(tpl.variables) if tpl.variables else "-"
        table.add_row(tpl.icon, tpl.name, tpl.description, vars_str)
    
    ctx.console.print(table)


def _use_template(ctx: FeatureContext, service) -> None:
    """Use a template to generate a prompt."""
    from rich.prompt import Prompt
    from rich.panel import Panel
    
    templates = service.list_templates()
    
    if not templates:
        ctx.console.print("[dim]No templates available.[/]")
        return
    
    ctx.console.print("\n[bold]Select a template:[/]")
    template_keys = list(service.templates.keys())
    for i, key in enumerate(template_keys, 1):
        tpl = service.templates[key]
        ctx.console.print(f"  {i}. {tpl.icon} [cyan]{tpl.name}[/]")
    
    selection = Prompt.ask("Template #", default="1")
    
    try:
        idx = int(selection) - 1
        if 0 <= idx < len(template_keys):
            key = template_keys[idx]
            tpl = service.templates[key]
            
            # Collect variable values
            variables = {}
            if tpl.variables:
                ctx.console.print(f"\n[bold]Enter values for {tpl.name}:[/]")
                for var in tpl.variables:
                    value = Prompt.ask(f"  {var}")
                    variables[var] = value
            
            # Build and display prompt
            prompt = service.build_prompt(key, variables)
            ctx.console.print("\n[bold green]Generated Prompt:[/]")
            ctx.console.print(Panel(prompt, border_style="green"))
            
            # Offer to copy
            if Prompt.ask("Copy to clipboard?", choices=["y", "n"], default="y") == "y":
                try:
                    from src.platform.clipboard import copy_to_clipboard
                    copy_to_clipboard(prompt)
                    ctx.console.print("[green]✓ Copied to clipboard[/]")
                except Exception:
                    ctx.console.print("[yellow]Could not copy to clipboard[/]")
                    
    except (ValueError, IndexError):
        ctx.console.print("[red]Invalid selection[/]")


def _view_template(ctx: FeatureContext, service) -> None:
    """View details of a specific template."""
    from rich.prompt import Prompt
    from rich.panel import Panel
    
    templates = service.list_templates()
    
    if not templates:
        ctx.console.print("[dim]No templates available.[/]")
        return
    
    ctx.console.print("\n[bold]Select a template to view:[/]")
    template_keys = list(service.templates.keys())
    for i, key in enumerate(template_keys, 1):
        tpl = service.templates[key]
        ctx.console.print(f"  {i}. {tpl.icon} [cyan]{tpl.name}[/]")
    
    selection = Prompt.ask("Template #", default="1")
    
    try:
        idx = int(selection) - 1
        if 0 <= idx < len(template_keys):
            key = template_keys[idx]
            tpl = service.templates[key]
            
            ctx.console.print(f"\n[bold]{tpl.icon} {tpl.name}[/]")
            ctx.console.print(f"[dim]{tpl.description}[/]")
            ctx.console.print(f"\n[bold]Variables:[/] {', '.join(tpl.variables) if tpl.variables else 'None'}")
            ctx.console.print(f"\n[bold]Template:[/]")
            ctx.console.print(Panel(tpl.template, border_style=tpl.color))
            
    except (ValueError, IndexError):
        ctx.console.print("[red]Invalid selection[/]")
