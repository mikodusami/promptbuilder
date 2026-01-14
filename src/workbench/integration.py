"""CLI Integration for the contrib discovery system.

This module bridges the feature registry with the interactive CLI menu system.
It provides menu generation, feature execution, and error display functionality.

Requirements: 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 6.4, 6.5, 9.4, 10.1, 10.2, 10.4
"""

import asyncio
from typing import Optional, Any
from rich.console import Console
from rich.table import Table
from rich import box

from .contract import FeatureContext, FeatureResult, FeatureCategory
from .registry import FeatureRegistry, get_registry
from .discovery import LoadedFeature


class CLIIntegration:
    """Integrates discovered features with the CLI menu system.
    
    This class provides methods to:
    - Build menu options from registered features
    - Render feature menus using Rich tables
    - Execute features (both sync and async)
    - Display discovery errors and warnings
    
    Requirements: 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 6.4, 6.5, 9.4, 10.1, 10.2, 10.4
    """

    CATEGORY_DISPLAY = {
        FeatureCategory.CORE: ("Core Features", "bright_white"),
        FeatureCategory.AI: ("AI Features", "bright_magenta"),
        FeatureCategory.STORAGE: ("Storage", "bright_blue"),
        FeatureCategory.EXPORT: ("Export & Share", "bright_green"),
        FeatureCategory.UTILITY: ("Utilities", "bright_yellow"),
    }

    def __init__(
        self,
        console: Console,
        llm_client: Any = None,
        history: Any = None,
        config: Any = None,
        analytics: Any = None,
        prompt_builder: Any = None,
        registry: Optional[FeatureRegistry] = None,
    ):
        """Initialize CLI integration.
        
        Args:
            console: Rich console for output
            llm_client: LLM API client (optional)
            history: HistoryService instance (optional)
            config: APIConfig instance (optional)
            analytics: PromptAnalytics instance (optional)
            prompt_builder: Core PromptBuilder instance (optional)
            registry: Feature registry (defaults to global registry)
        """
        self.console = console
        self.registry = registry or get_registry()

        # Build context for feature execution
        self.context = FeatureContext(
            console=console,
            llm_client=llm_client,
            history=history,
            config=config,
            analytics=analytics,
            prompt_builder=prompt_builder,
        )

    def build_menu_options(
        self,
        category: Optional[FeatureCategory] = None,
        include_disabled: bool = False,
        has_api_key: bool = False,
    ) -> list[tuple[str, LoadedFeature]]:
        """Build menu options for features.
        
        Args:
            category: Filter by specific category (None for all)
            include_disabled: Whether to include disabled features
            has_api_key: Whether an API key is configured
            
        Returns:
            List of (display_string, LoadedFeature) tuples.
            
        Requirements: 5.1, 5.2
        """
        if category:
            features = self.registry.list_by_category(category)
        else:
            features = self.registry.list_all()

        options = []
        for feature in features:
            if not include_disabled and not feature.manifest.enabled:
                continue

            # Build display string with icon, name, and description
            m = feature.manifest
            display = f"{m.icon} {m.display_name:<20} - {m.description}"
            options.append((display, feature))

        return options

    def render_feature_menu(
        self,
        title: str = "Features",
        category: Optional[FeatureCategory] = None,
        has_api_key: bool = False,
    ) -> None:
        """Render a Rich table of available features.
        
        Args:
            title: Table title
            category: Filter by specific category (None for all)
            has_api_key: Whether an API key is configured
            
        Requirements: 5.1, 5.2, 5.3
        """
        table = Table(
            title=title,
            box=box.ROUNDED,
            border_style="dim",
            show_header=True,
            padding=(0, 2),
        )
        table.add_column("Key", style="bold", width=5)
        table.add_column("Feature", width=25)
        table.add_column("Description", style="dim")

        options = self.build_menu_options(category, has_api_key=has_api_key)

        for i, (display, feature) in enumerate(options, 1):
            m = feature.manifest
            key = m.menu_key or str(i)

            # Dim if requires API but none configured
            style = m.color
            if m.requires_api_key and not has_api_key:
                style = "dim"
                key = f"[dim]{key}[/]"

            table.add_row(
                f"[{m.color}]{key}[/]",
                f"{m.icon} [{style}]{m.display_name}[/]",
                m.description,
            )

        self.console.print(table)

    def render_categorized_menu(self, has_api_key: bool = False) -> None:
        """Render features grouped by category.
        
        Displays features organized by their category with visual
        indicators for API key requirements.
        
        Args:
            has_api_key: Whether an API key is configured
            
        Requirements: 5.1, 5.2, 5.3, 9.4
        """
        categories = self.registry.get_categories_with_features()

        for category, features in categories:
            cat_name, cat_color = self.CATEGORY_DISPLAY[category]
            self.console.print(f"\n[bold {cat_color}]{cat_name}[/]")

            for feature in features:
                m = feature.manifest
                style = m.color
                indicator = ""

                if m.requires_api_key:
                    indicator = " ●" if has_api_key else " ○"
                    if not has_api_key:
                        style = "dim"

                self.console.print(
                    f"  [{style}]{m.icon} {m.display_name}{indicator}[/] - {m.description}"
                )


    async def execute_feature(self, feature: LoadedFeature) -> FeatureResult:
        """Execute a feature's run function asynchronously.
        
        Handles both sync and async run functions, calling setup if present.
        
        Args:
            feature: The loaded feature to execute
            
        Returns:
            FeatureResult from the feature execution.
            
        Requirements: 6.1, 6.2, 6.3, 6.4
        """
        try:
            # Call setup if exists
            if feature.setup:
                try:
                    feature.setup(self.context)
                except Exception as e:
                    return FeatureResult(
                        success=False,
                        error=f"Feature setup failed: {str(e)}"
                    )

            # Execute run (handle both sync and async)
            result = feature.run(self.context)

            if asyncio.iscoroutine(result):
                result = await result

            # Ensure we return a FeatureResult
            if not isinstance(result, FeatureResult):
                return FeatureResult(
                    success=True,
                    message="Feature completed",
                    data=result
                )

            return result

        except Exception as e:
            return FeatureResult(
                success=False,
                error=f"Feature execution failed: {str(e)}"
            )

    def execute_feature_sync(self, feature: LoadedFeature) -> FeatureResult:
        """Synchronous wrapper for feature execution.
        
        Creates a new event loop if needed to run the async execute_feature.
        
        Args:
            feature: The loaded feature to execute
            
        Returns:
            FeatureResult from the feature execution.
            
        Requirements: 6.4, 6.5
        """
        try:
            # Check if there's already a running event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're already in an async context, we can't use asyncio.run
                # Create a new task instead
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, 
                        self.execute_feature(feature)
                    )
                    return future.result()
            except RuntimeError:
                # No running event loop, safe to use asyncio.run
                return asyncio.run(self.execute_feature(feature))
        except Exception as e:
            return FeatureResult(
                success=False,
                error=f"Feature execution failed: {str(e)}"
            )


    def show_discovery_errors(self) -> None:
        """Display any errors from feature discovery.
        
        Shows a summary of discovery errors and warnings using
        Rich formatting for clear visibility.
        
        Requirements: 10.1, 10.2, 10.4
        """
        errors = self.registry.get_errors()
        warnings = self.registry.get_warnings()

        if errors:
            self.console.print("\n[bold red]Feature Discovery Errors:[/]")
            for err in errors:
                path_display = err.feature_path if err.feature_path else "(global)"
                self.console.print(f"  [red]✗[/] {path_display}: {err.message}")

        if warnings:
            self.console.print("\n[bold yellow]Warnings:[/]")
            for warn in warnings:
                self.console.print(f"  [yellow]⚠[/] {warn}")

    def has_discovery_issues(self) -> bool:
        """Check if there were any discovery errors or warnings.
        
        Returns:
            True if there are errors or warnings, False otherwise.
        """
        return self.registry.has_errors() or bool(self.registry.get_warnings())

    def get_feature_by_key(
        self,
        key: str,
        category: Optional[FeatureCategory] = None,
    ) -> Optional[LoadedFeature]:
        """Get a feature by its menu key or index.
        
        Args:
            key: Menu key or numeric index (1-based)
            category: Filter by specific category (None for all)
            
        Returns:
            LoadedFeature if found, None otherwise.
        """
        options = self.build_menu_options(category)
        
        # First try to match by menu_key
        for _, feature in options:
            if feature.manifest.menu_key == key:
                return feature
        
        # Then try numeric index
        try:
            index = int(key) - 1
            if 0 <= index < len(options):
                return options[index][1]
        except ValueError:
            pass
        
        return None
