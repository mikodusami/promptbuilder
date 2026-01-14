"""
Variables feature manifest - variable interpolation for reusable prompts.

Requirements: 2.1, 2.2, 2.3
"""

from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)


MANIFEST = FeatureManifest(
    name="variables",
    display_name="Variable Templates",
    description="Create and use templates with dynamic variables",
    icon="🔤",
    color="bright_cyan",
    category=FeatureCategory.UTILITY,
    requires_api_key=False,
    menu_key="v",
)


def run(ctx: FeatureContext) -> FeatureResult:
    """Run the variables feature - manage variable templates."""
    # Import dependencies inside function to avoid module-level import issues
    from rich.prompt import Prompt
    from .service import VariableInterpolator
    
    interpolator = VariableInterpolator()
    
    while True:
        ctx.console.print("\n[bold bright_cyan]🔤 Variable Templates[/]")
        ctx.console.print("1. List templates")
        ctx.console.print("2. Use a template")
        ctx.console.print("3. Create new template")
        ctx.console.print("4. Quick interpolate")
        ctx.console.print("5. Delete template")
        ctx.console.print("6. Back to menu")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "6"], default="1")
        
        if choice == "1":
            _list_templates(ctx, interpolator)
        elif choice == "2":
            _use_template(ctx, interpolator)
        elif choice == "3":
            _create_template(ctx, interpolator)
        elif choice == "4":
            _quick_interpolate(ctx, interpolator)
        elif choice == "5":
            _delete_template(ctx, interpolator)
        elif choice == "6":
            break
    
    return FeatureResult(success=True, message="Variables session complete")


def _list_templates(ctx: FeatureContext, interpolator) -> None:
    """List all saved templates."""
    from rich.table import Table
    from rich import box
    
    templates = interpolator.list_templates()
    
    if not templates:
        ctx.console.print("[dim]No templates saved yet.[/]")
        return
    
    table = Table(title="Variable Templates", box=box.ROUNDED, border_style="bright_cyan")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Variables", style="dim")
    table.add_column("Tags", style="dim")
    
    for tpl in templates:
        vars_str = ", ".join(v.name for v in tpl.variables) if tpl.variables else "-"
        tags_str = ", ".join(tpl.tags) if tpl.tags else "-"
        table.add_row(tpl.name, tpl.description, vars_str, tags_str)
    
    ctx.console.print(table)


def _use_template(ctx: FeatureContext, interpolator) -> None:
    """Use a saved template."""
    from rich.prompt import Prompt
    from rich.panel import Panel
    
    templates = interpolator.list_templates()
    
    if not templates:
        ctx.console.print("[dim]No templates available. Create one first.[/]")
        return
    
    ctx.console.print("\n[bold]Select a template:[/]")
    for i, tpl in enumerate(templates, 1):
        ctx.console.print(f"  {i}. [cyan]{tpl.name}[/] - {tpl.description}")
    
    selection = Prompt.ask("Template #", default="1")
    
    try:
        idx = int(selection) - 1
        if 0 <= idx < len(templates):
            tpl = templates[idx]
            
            # Collect variable values
            values = {}
            if tpl.variables:
                ctx.console.print(f"\n[bold]Enter values for {tpl.name}:[/]")
                for var in tpl.variables:
                    default = var.default or ""
                    prompt_text = f"  {var.name}"
                    if var.description:
                        prompt_text += f" ({var.description})"
                    value = Prompt.ask(prompt_text, default=default)
                    values[var.name] = value
            
            # Validate and interpolate
            valid, errors = interpolator.validate_variables(tpl, values)
            if not valid:
                ctx.console.print("[red]Validation errors:[/]")
                for error in errors:
                    ctx.console.print(f"  • {error}")
                return
            
            result = interpolator.interpolate(tpl.template, values)
            
            ctx.console.print("\n[bold green]Generated Prompt:[/]")
            ctx.console.print(Panel(result, border_style="green"))
            
            # Offer to copy
            if Prompt.ask("Copy to clipboard?", choices=["y", "n"], default="y") == "y":
                try:
                    from src.platform.clipboard import copy_to_clipboard
                    copy_to_clipboard(result)
                    ctx.console.print("[green]✓ Copied to clipboard[/]")
                except Exception:
                    ctx.console.print("[yellow]Could not copy to clipboard[/]")
                    
    except (ValueError, IndexError):
        ctx.console.print("[red]Invalid selection[/]")


def _create_template(ctx: FeatureContext, interpolator) -> None:
    """Create a new template."""
    from rich.prompt import Prompt
    
    ctx.console.print("\n[bold]Create New Template[/]")
    
    name = Prompt.ask("Template name")
    if not name:
        ctx.console.print("[red]Name is required[/]")
        return
    
    description = Prompt.ask("Description", default="")
    
    ctx.console.print("\n[dim]Enter template with {{variable}} placeholders.[/]")
    ctx.console.print("[dim]Use {{var:default}} for default values.[/]")
    ctx.console.print("[dim]Enter empty line when done:[/]\n")
    
    lines = []
    while True:
        line = Prompt.ask("", default="")
        if not line:
            break
        lines.append(line)
    
    template = "\n".join(lines)
    
    if not template:
        ctx.console.print("[red]Template content is required[/]")
        return
    
    tags_input = Prompt.ask("Tags (comma-separated)", default="")
    tags = [t.strip() for t in tags_input.split(",") if t.strip()]
    
    tpl = interpolator.create_template(name, template, description, tags)
    
    ctx.console.print(f"\n[green]✓ Template '{name}' created with {len(tpl.variables)} variables[/]")
    
    # Show extracted variables
    if tpl.variables:
        ctx.console.print("[bold]Variables found:[/]")
        for var in tpl.variables:
            default_str = f" (default: {var.default})" if var.default else ""
            ctx.console.print(f"  • {var.name}{default_str}")


def _quick_interpolate(ctx: FeatureContext, interpolator) -> None:
    """Quick interpolation without saving template."""
    from rich.prompt import Prompt
    from rich.panel import Panel
    
    ctx.console.print("\n[bold]Quick Interpolate[/]")
    ctx.console.print("[dim]Enter template with {{variable}} placeholders:[/]\n")
    
    lines = []
    while True:
        line = Prompt.ask("", default="")
        if not line:
            break
        lines.append(line)
    
    template = "\n".join(lines)
    
    if not template:
        ctx.console.print("[red]Template is required[/]")
        return
    
    # Extract and collect variables
    variables = interpolator.extract_variables(template)
    
    if not variables:
        ctx.console.print("[dim]No variables found in template.[/]")
        ctx.console.print(Panel(template, border_style="green"))
        return
    
    ctx.console.print(f"\n[bold]Found {len(variables)} variables:[/]")
    values = {}
    for var in variables:
        default = var.default or ""
        value = Prompt.ask(f"  {var.name}", default=default)
        values[var.name] = value
    
    result = interpolator.interpolate(template, values)
    
    ctx.console.print("\n[bold green]Result:[/]")
    ctx.console.print(Panel(result, border_style="green"))


def _delete_template(ctx: FeatureContext, interpolator) -> None:
    """Delete a saved template."""
    from rich.prompt import Prompt
    
    templates = interpolator.list_templates()
    
    if not templates:
        ctx.console.print("[dim]No templates to delete.[/]")
        return
    
    ctx.console.print("\n[bold]Select template to delete:[/]")
    for i, tpl in enumerate(templates, 1):
        ctx.console.print(f"  {i}. [cyan]{tpl.name}[/]")
    
    selection = Prompt.ask("Template #", default="")
    
    if not selection:
        return
    
    try:
        idx = int(selection) - 1
        if 0 <= idx < len(templates):
            tpl = templates[idx]
            if Prompt.ask(f"Delete '{tpl.name}'?", choices=["y", "n"], default="n") == "y":
                if interpolator.delete_template(tpl.name):
                    ctx.console.print(f"[green]✓ Template '{tpl.name}' deleted[/]")
                else:
                    ctx.console.print("[red]Failed to delete template[/]")
    except (ValueError, IndexError):
        ctx.console.print("[red]Invalid selection[/]")
