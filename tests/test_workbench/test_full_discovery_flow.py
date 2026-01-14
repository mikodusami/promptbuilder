"""Integration tests for the full discovery flow.

Tests the complete pipeline: discovery → registry → menu → execution

Feature: contrib-discovery
Validates: Requirements 3.1, 3.2, 3.3, 4.1, 5.1, 6.1
"""

import pytest
import tempfile
from pathlib import Path
from io import StringIO

from rich.console import Console

from src.workbench.discovery import DiscoveryEngine, DiscoveryResult
from src.workbench.registry import FeatureRegistry
from src.workbench.integration import CLIIntegration
from src.workbench.contract import (
    FeatureCategory,
    FeatureManifest,
    FeatureContext,
    FeatureResult,
)


def create_manifest_file(
    path: Path,
    name: str,
    display_name: str,
    description: str,
    icon: str,
    color: str,
    category: FeatureCategory,
    requires_api_key: bool = False,
    is_async: bool = False,
    return_data: str = None,
):
    """Helper to create a valid manifest.py file for testing."""
    async_prefix = "async " if is_async else ""
    await_keyword = "await " if is_async else ""
    data_str = f'"{return_data}"' if return_data else "None"
    
    content = f'''"""Auto-generated manifest for integration testing."""
from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)

MANIFEST = FeatureManifest(
    name="{name}",
    display_name="{display_name}",
    description="{description}",
    icon="{icon}",
    color="{color}",
    category=FeatureCategory.{category.name},
    requires_api_key={requires_api_key},
)

{async_prefix}def run(ctx: FeatureContext) -> FeatureResult:
    """Execute the feature."""
    return FeatureResult(
        success=True,
        message="Feature {name} executed successfully",
        data={data_str},
    )
'''
    path.mkdir(parents=True, exist_ok=True)
    (path / "manifest.py").write_text(content)
    (path / "__init__.py").write_text("")


def create_test_console() -> tuple[Console, StringIO]:
    """Create a console that captures output for testing."""
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=120)
    return console, output


class TestFullDiscoveryFlow:
    """Integration tests for the complete discovery → registry → menu → execution flow.
    
    Validates: Requirements 3.1, 3.2, 3.3, 4.1, 5.1, 6.1
    """

    def test_discovery_to_registry_to_menu_to_execution(self):
        """Test the complete flow from discovery to feature execution.
        
        This test verifies:
        1. Discovery finds all valid manifest.py files
        2. Registry stores all discovered features
        3. Menu options include all registered features
        4. Feature execution works correctly
        
        Validates: Requirements 3.1, 3.2, 3.3, 4.1, 5.1, 6.1
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create multiple features across different categories
            features_config = [
                ("core_feature", "Core Feature", "A core feature", "⚙️", "white", FeatureCategory.CORE),
                ("ai_feature", "AI Feature", "An AI feature", "🤖", "magenta", FeatureCategory.AI),
                ("storage_feature", "Storage Feature", "A storage feature", "💾", "blue", FeatureCategory.STORAGE),
            ]
            
            for name, display, desc, icon, color, category in features_config:
                create_manifest_file(
                    contrib_path / name,
                    name=name,
                    display_name=display,
                    description=desc,
                    icon=icon,
                    color=color,
                    category=category,
                    return_data=f"data_from_{name}",
                )
            
            # Phase 1: Discovery
            engine = DiscoveryEngine(contrib_path=contrib_path)
            discovery_result = engine.discover()
            
            assert len(discovery_result.features) == 3, (
                f"Expected 3 features, got {len(discovery_result.features)}. "
                f"Errors: {[e.message for e in discovery_result.errors]}"
            )
            assert len(discovery_result.errors) == 0
            
            # Phase 2: Registry
            registry = FeatureRegistry()
            registry.load(engine)
            
            assert len(registry.list_all()) == 3
            
            # Verify each feature is accessible by name
            for name, _, _, _, _, _ in features_config:
                feature = registry.get(name)
                assert feature is not None, f"Feature {name} not found in registry"
            
            # Phase 3: Menu
            console, output = create_test_console()
            cli = CLIIntegration(console=console, registry=registry)
            
            menu_options = cli.build_menu_options()
            assert len(menu_options) == 3
            
            # Verify menu options contain correct display info
            for display_str, feature in menu_options:
                m = feature.manifest
                assert m.icon in display_str
                assert m.display_name in display_str
                assert m.description in display_str
            
            # Phase 4: Execution
            for name, _, _, _, _, _ in features_config:
                feature = registry.get(name)
                result = cli.execute_feature_sync(feature)
                
                assert result.success is True, f"Feature {name} failed: {result.error}"
                assert f"Feature {name} executed successfully" in result.message
                assert result.data == f"data_from_{name}"

    def test_async_feature_execution_in_flow(self):
        """Test that async features work correctly in the full flow.
        
        Validates: Requirements 6.1, 6.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create an async feature
            create_manifest_file(
                contrib_path / "async_feature",
                name="async_feature",
                display_name="Async Feature",
                description="An async feature",
                icon="⚡",
                color="yellow",
                category=FeatureCategory.AI,
                is_async=True,
                return_data="async_result",
            )
            
            # Run through the full flow
            engine = DiscoveryEngine(contrib_path=contrib_path)
            registry = FeatureRegistry()
            registry.load(engine)
            
            console, _ = create_test_console()
            cli = CLIIntegration(console=console, registry=registry)
            
            feature = registry.get("async_feature")
            result = cli.execute_feature_sync(feature)
            
            assert result.success is True
            assert result.data == "async_result"

    def test_category_filtering_in_flow(self):
        """Test that category filtering works correctly through the flow.
        
        Validates: Requirements 4.2, 5.1
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create features in different categories
            create_manifest_file(
                contrib_path / "ai_one",
                name="ai_one",
                display_name="AI One",
                description="First AI feature",
                icon="🤖",
                color="magenta",
                category=FeatureCategory.AI,
            )
            create_manifest_file(
                contrib_path / "ai_two",
                name="ai_two",
                display_name="AI Two",
                description="Second AI feature",
                icon="🧠",
                color="purple",
                category=FeatureCategory.AI,
            )
            create_manifest_file(
                contrib_path / "utility_one",
                name="utility_one",
                display_name="Utility One",
                description="A utility feature",
                icon="🔧",
                color="cyan",
                category=FeatureCategory.UTILITY,
            )
            
            # Run discovery and registration
            engine = DiscoveryEngine(contrib_path=contrib_path)
            registry = FeatureRegistry()
            registry.load(engine)
            
            console, _ = create_test_console()
            cli = CLIIntegration(console=console, registry=registry)
            
            # Filter by AI category
            ai_options = cli.build_menu_options(category=FeatureCategory.AI)
            assert len(ai_options) == 2
            ai_names = {f.manifest.name for _, f in ai_options}
            assert ai_names == {"ai_one", "ai_two"}
            
            # Filter by UTILITY category
            utility_options = cli.build_menu_options(category=FeatureCategory.UTILITY)
            assert len(utility_options) == 1
            assert utility_options[0][1].manifest.name == "utility_one"

    def test_api_key_requirement_in_flow(self):
        """Test that API key requirements are tracked through the flow.
        
        Validates: Requirements 4.3, 5.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create features with different API key requirements
            create_manifest_file(
                contrib_path / "needs_api",
                name="needs_api",
                display_name="Needs API",
                description="Requires API key",
                icon="🔑",
                color="red",
                category=FeatureCategory.AI,
                requires_api_key=True,
            )
            create_manifest_file(
                contrib_path / "no_api",
                name="no_api",
                display_name="No API",
                description="Does not require API key",
                icon="📦",
                color="green",
                category=FeatureCategory.UTILITY,
                requires_api_key=False,
            )
            
            # Run discovery and registration
            engine = DiscoveryEngine(contrib_path=contrib_path)
            registry = FeatureRegistry()
            registry.load(engine)
            
            # Verify API key requirement tracking
            api_features = registry.list_requiring_api()
            assert len(api_features) == 1
            assert api_features[0].manifest.name == "needs_api"

    def test_dependency_ordering_in_flow(self):
        """Test that dependencies are resolved correctly in the flow.
        
        Validates: Requirements 7.2
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create base feature (no dependencies)
            base_content = '''"""Base feature manifest."""
from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)

MANIFEST = FeatureManifest(
    name="base_feature",
    display_name="Base Feature",
    description="Base feature with no dependencies",
    icon="📦",
    color="cyan",
    category=FeatureCategory.CORE,
    dependencies=[],
)

def run(ctx: FeatureContext) -> FeatureResult:
    return FeatureResult(success=True, message="Base executed")
'''
            base_path = contrib_path / "base_feature"
            base_path.mkdir()
            (base_path / "manifest.py").write_text(base_content)
            (base_path / "__init__.py").write_text("")
            
            # Create dependent feature
            dependent_content = '''"""Dependent feature manifest."""
from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)

MANIFEST = FeatureManifest(
    name="dependent_feature",
    display_name="Dependent Feature",
    description="Feature that depends on base",
    icon="🔗",
    color="yellow",
    category=FeatureCategory.CORE,
    dependencies=["base_feature"],
)

def run(ctx: FeatureContext) -> FeatureResult:
    return FeatureResult(success=True, message="Dependent executed")
'''
            dep_path = contrib_path / "dependent_feature"
            dep_path.mkdir()
            (dep_path / "manifest.py").write_text(dependent_content)
            (dep_path / "__init__.py").write_text("")
            
            # Run discovery
            engine = DiscoveryEngine(contrib_path=contrib_path)
            result = engine.discover()
            
            assert len(result.features) == 2
            assert len(result.errors) == 0
            
            # Verify ordering: base should come before dependent
            feature_names = [f.manifest.name for f in result.features]
            base_idx = feature_names.index("base_feature")
            dep_idx = feature_names.index("dependent_feature")
            assert base_idx < dep_idx, "Base feature should be loaded before dependent"

    def test_error_handling_in_flow(self):
        """Test that errors are properly collected and accessible in the flow.
        
        Validates: Requirements 10.2, 10.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create a valid feature
            create_manifest_file(
                contrib_path / "valid_feature",
                name="valid_feature",
                display_name="Valid Feature",
                description="A valid feature",
                icon="✅",
                color="green",
                category=FeatureCategory.UTILITY,
            )
            
            # Create an invalid feature (missing run function)
            invalid_path = contrib_path / "invalid_feature"
            invalid_path.mkdir()
            (invalid_path / "__init__.py").write_text("")
            (invalid_path / "manifest.py").write_text('''
from src.workbench.contract import FeatureManifest, FeatureCategory

MANIFEST = FeatureManifest(
    name="invalid_feature",
    display_name="Invalid Feature",
    description="Missing run function",
    icon="❌",
    color="red",
    category=FeatureCategory.UTILITY,
)
# Note: Missing run function!
''')
            
            # Run discovery and registration
            engine = DiscoveryEngine(contrib_path=contrib_path)
            registry = FeatureRegistry()
            registry.load(engine)
            
            # Valid feature should be loaded
            assert len(registry.list_all()) == 1
            assert registry.get("valid_feature") is not None
            
            # Error should be recorded
            assert registry.has_errors()
            errors = registry.get_errors()
            assert len(errors) == 1
            assert "Missing run function" in errors[0].message

    def test_menu_rendering_in_flow(self):
        """Test that menu rendering works correctly with discovered features.
        
        Validates: Requirements 5.1, 5.2, 5.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create features
            create_manifest_file(
                contrib_path / "test_feature",
                name="test_feature",
                display_name="Test Feature",
                description="A test feature for menu rendering",
                icon="🧪",
                color="cyan",
                category=FeatureCategory.UTILITY,
            )
            
            # Run discovery and registration
            engine = DiscoveryEngine(contrib_path=contrib_path)
            registry = FeatureRegistry()
            registry.load(engine)
            
            console, output = create_test_console()
            cli = CLIIntegration(console=console, registry=registry)
            
            # Render the menu
            cli.render_feature_menu(title="Test Menu")
            
            # Verify output contains feature info
            rendered = output.getvalue()
            assert "Test Feature" in rendered or "test_feature" in rendered

    def test_feature_execution_with_context(self):
        """Test that features receive proper context during execution.
        
        Validates: Requirements 6.1, 6.2
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create a feature that validates its context
            context_check_content = '''"""Context checking feature."""
from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)

MANIFEST = FeatureManifest(
    name="context_checker",
    display_name="Context Checker",
    description="Validates context fields",
    icon="🔍",
    color="cyan",
    category=FeatureCategory.UTILITY,
)

def run(ctx: FeatureContext) -> FeatureResult:
    # Verify context has all expected fields
    has_console = ctx.console is not None
    has_llm = hasattr(ctx, 'llm_client')
    has_history = hasattr(ctx, 'history')
    has_config = hasattr(ctx, 'config')
    has_analytics = hasattr(ctx, 'analytics')
    
    all_present = all([has_console, has_llm, has_history, has_config, has_analytics])
    
    return FeatureResult(
        success=all_present,
        message="Context validation complete",
        data={
            "has_console": has_console,
            "has_llm": has_llm,
            "has_history": has_history,
            "has_config": has_config,
            "has_analytics": has_analytics,
        }
    )
'''
            feature_path = contrib_path / "context_checker"
            feature_path.mkdir()
            (feature_path / "manifest.py").write_text(context_check_content)
            (feature_path / "__init__.py").write_text("")
            
            # Run discovery and registration
            engine = DiscoveryEngine(contrib_path=contrib_path)
            registry = FeatureRegistry()
            registry.load(engine)
            
            console, _ = create_test_console()
            
            # Create CLI with all context fields
            cli = CLIIntegration(
                console=console,
                llm_client="mock_llm",
                history="mock_history",
                config="mock_config",
                analytics="mock_analytics",
                prompt_builder="mock_builder",
                registry=registry,
            )
            
            feature = registry.get("context_checker")
            result = cli.execute_feature_sync(feature)
            
            assert result.success is True, f"Context validation failed: {result.data}"
            assert result.data["has_console"] is True
            assert result.data["has_llm"] is True
            assert result.data["has_history"] is True
            assert result.data["has_config"] is True
            assert result.data["has_analytics"] is True
