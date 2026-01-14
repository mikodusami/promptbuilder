"""
Chains feature manifest - multi-step prompt chain execution.

Requirements: 2.1, 2.2, 2.3
"""

from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)


MANIFEST = FeatureManifest(
    name="chains",
    display_name="Prompt Chains",
    description="Execute multi-step prompt workflows",
    icon="🔗",
    color="magenta",
    category=FeatureCategory.AI,
    requires_api_key=True,
    menu_key="c",
)


async def run(ctx: FeatureContext) -> FeatureResult:
    """Run the chains feature - execute multi-step prompt workflows."""
    # Import dependencies inside function to avoid module-level import issues
    from rich.prompt import Prompt
    from .service import ChainService
    from .builtin import BUILTIN_CHAINS
    
    if not ctx.llm_client:
        return FeatureResult(
            success=False,
            error="LLM client not available. Please configure an API key."
        )
    
    chain_service = ChainService(ctx.llm_client)
    
    while True:
        ctx.console.print("\n[bold magenta]🔗 Prompt Chains[/]")
        ctx.console.print("1. Run a built-in chain")
        ctx.console.print("2. Run a saved chain")
        ctx.console.print("3. List saved chains")
        ctx.console.print("4. Back to menu")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4"], default="1")
        
        if choice == "1":
            await _run_builtin_chain(ctx, chain_service)
        elif choice == "2":
            await _run_saved_chain(ctx, chain_service)
        elif choice == "3":
            _list_chains(ctx, chain_service)
        elif choice == "4":
            break
    
    return FeatureResult(success=True, message="Chains session complete")


async def _run_builtin_chain(ctx: FeatureContext, service) -> None:
    """Run a built-in chain template."""
    from rich.prompt import Prompt
    from .builtin import BUILTIN_CHAINS
    
    ctx.console.print("\n[bold]Built-in Chains:[/]")
    
    chains = list(BUILTIN_CHAINS.items())
    for i, (name, chain) in enumerate(chains, 1):
        ctx.console.print(f"  {i}. [cyan]{chain.name}[/] - {chain.description}")
    
    selection = Prompt.ask("Select chain", default="1")
    
    try:
        idx = int(selection) - 1
        if 0 <= idx < len(chains):
            name, chain = chains[idx]
            await _execute_chain(ctx, service, chain)
    except (ValueError, IndexError):
        ctx.console.print("[red]Invalid selection[/]")


async def _run_saved_chain(ctx: FeatureContext, service) -> None:
    """Run a saved chain."""
    from rich.prompt import Prompt
    
    chains = service.list_chains()
    
    if not chains:
        ctx.console.print("[dim]No saved chains. Create one first.[/]")
        return
    
    ctx.console.print("\n[bold]Saved Chains:[/]")
    for i, chain in enumerate(chains, 1):
        ctx.console.print(f"  {i}. [cyan]{chain.name}[/] - {chain.description}")
    
    selection = Prompt.ask("Select chain", default="1")
    
    try:
        idx = int(selection) - 1
        if 0 <= idx < len(chains):
            await _execute_chain(ctx, service, chains[idx])
    except (ValueError, IndexError):
        ctx.console.print("[red]Invalid selection[/]")


async def _execute_chain(ctx: FeatureContext, service, chain) -> None:
    """Execute a chain and display results."""
    from rich.prompt import Prompt
    from rich.panel import Panel
    
    ctx.console.print(f"\n[bold]Running chain: {chain.name}[/]")
    ctx.console.print(f"[dim]Steps: {len(chain.steps)}[/]\n")
    
    # Collect input variables
    input_context = {}
    
    # Find variables in the first step
    first_step = chain.steps[0] if chain.steps else None
    if first_step:
        import re
        vars_found = re.findall(r'\{(\w+)\}', first_step.prompt_template)
        for var in vars_found:
            if var not in chain.initial_context:
                value = Prompt.ask(f"Enter value for '{var}'")
                input_context[var] = value
    
    ctx.console.print("[dim]Executing chain...[/]\n")
    
    result = await service.execute(chain, input_context)
    
    # Display results
    if result.success:
        ctx.console.print("[bold green]✓ Chain completed successfully[/]")
    else:
        ctx.console.print("[bold red]✗ Chain failed[/]")
    
    ctx.console.print(f"Steps completed: {result.steps_completed}/{result.total_steps}")
    ctx.console.print(f"Total tokens: {result.total_tokens}")
    ctx.console.print(f"Total latency: {result.total_latency_ms}ms")
    
    if result.errors:
        ctx.console.print("\n[bold red]Errors:[/]")
        for error in result.errors:
            ctx.console.print(f"  • {error}")
    
    if result.final_output:
        ctx.console.print("\n[bold]Final Output:[/]")
        ctx.console.print(Panel(result.final_output, border_style="green"))


def _list_chains(ctx: FeatureContext, service) -> None:
    """List all saved chains."""
    from rich.table import Table
    from rich import box
    
    chains = service.list_chains()
    
    if not chains:
        ctx.console.print("[dim]No saved chains.[/]")
        return
    
    table = Table(title="Saved Chains", box=box.ROUNDED, border_style="magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Steps", justify="center")
    
    for chain in chains:
        table.add_row(chain.name, chain.description, str(len(chain.steps)))
    
    ctx.console.print(table)
