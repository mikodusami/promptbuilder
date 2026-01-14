"""Property-based tests for CLI Integration.

Feature: contrib-discovery
Property 5: Menu Rendering Completeness
Property 6: Feature Execution Contract
Validates: Requirements 5.1, 5.2, 6.1, 6.2, 6.4
"""

import pytest
import asyncio
from io import StringIO
from hypothesis import given, strategies as st, settings

from rich.console import Console

from src.workbench.integration import CLIIntegration
from src.workbench.registry import FeatureRegistry
from src.workbench.discovery import LoadedFeature
from src.workbench.contract import (
    FeatureCategory,
    FeatureManifest,
    FeatureContext,
    FeatureResult,
)


# Strategies for generating valid feature data
feature_name_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz_"),
    min_size=3,
    max_size=20
).filter(lambda x: x and not x.startswith('_') and x.strip())

simple_text = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789 "),
    min_size=1,
    max_size=30
).filter(lambda x: x.strip())

emoji_text = st.sampled_from(["📦", "🔧", "⚡", "🎯", "💡", "🚀", "✨", "🔍"])
color_text = st.sampled_from(["cyan", "green", "yellow", "red", "blue", "magenta", "white"])
category_strategy = st.sampled_from(list(FeatureCategory))


def create_loaded_feature(
    name: str,
    display_name: str,
    description: str,
    icon: str,
    color: str,
    category: FeatureCategory,
    requires_api_key: bool = False,
    enabled: bool = True,
    run_func=None,
) -> LoadedFeature:
    """Helper to create a LoadedFeature for testing."""
    manifest = FeatureManifest(
        name=name,
        display_name=display_name,
        description=description,
        icon=icon,
        color=color,
        category=category,
        requires_api_key=requires_api_key,
        enabled=enabled,
    )
    
    if run_func is None:
        def run_func(ctx):
            return FeatureResult(success=True, message="Test")
    
    return LoadedFeature(
        manifest=manifest,
        run=run_func,
        module_path=f"/test/{name}",
    )


def create_test_console() -> tuple[Console, StringIO]:
    """Create a console that captures output for testing."""
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=120)
    return console, output


class TestMenuRenderingCompletenessProperty:
    """Property-based tests for Menu Rendering Completeness (Property 5).
    
    For any feature in the registry, the CLI menu rendering shall include
    the feature's icon, display_name, and description, and shall group
    features by their category field.
    
    Validates: Requirements 5.1, 5.2
    """

    @settings(max_examples=100)
    @given(
        feature_names=st.lists(
            feature_name_strategy,
            min_size=1,
            max_size=10,
            unique=True
        ),
        display_names=st.lists(simple_text, min_size=10, max_size=10),
        descriptions=st.lists(simple_text, min_size=10, max_size=10),
        icons=st.lists(emoji_text, min_size=10, max_size=10),
        colors=st.lists(color_text, min_size=10, max_size=10),
        categories=st.lists(category_strategy, min_size=10, max_size=10),
    )
    def test_menu_options_include_all_enabled_features(
        self, feature_names, display_names, descriptions, icons, colors, categories
    ):
        """
        Feature: contrib-discovery, Property 5: Menu Rendering Completeness
        
        For any set of enabled features, build_menu_options should return
        all of them with their icon, display_name, and description.
        
        Validates: Requirements 5.1, 5.2
        """
        registry = FeatureRegistry()
        console, _ = create_test_console()
        
        # Create and register features
        features = []
        for i, name in enumerate(feature_names):
            feature = create_loaded_feature(
                name=name,
                display_name=display_names[i % len(display_names)],
                description=descriptions[i % len(descriptions)],
                icon=icons[i % len(icons)],
                color=colors[i % len(colors)],
                category=categories[i % len(categories)],
                enabled=True,
            )
            features.append(feature)
            registry._register(feature)
        
        cli = CLIIntegration(console=console, registry=registry)
        options = cli.build_menu_options()
        
        # Verify all features are included
        option_names = {f.manifest.name for _, f in options}
        expected_names = {f.manifest.name for f in features}
        assert option_names == expected_names, (
            f"Expected {expected_names}, got {option_names}"
        )
        
        # Verify each option includes icon, display_name, and description
        for display_str, feature in options:
            m = feature.manifest
            assert m.icon in display_str, f"Icon {m.icon} not in display string"
            assert m.display_name in display_str, f"Display name {m.display_name} not in display string"
            assert m.description in display_str, f"Description {m.description} not in display string"

    @settings(max_examples=100)
    @given(
        feature_count=st.integers(min_value=1, max_value=10),
        categories=st.lists(category_strategy, min_size=10, max_size=10),
    )
    def test_menu_options_filter_by_category(self, feature_count, categories):
        """
        Feature: contrib-discovery, Property 5: Menu Rendering Completeness
        
        For any category filter, build_menu_options should return only
        features in that category.
        
        Validates: Requirements 5.1
        """
        registry = FeatureRegistry()
        console, _ = create_test_console()
        
        # Create features with various categories
        features_by_category = {cat: [] for cat in FeatureCategory}
        
        for i in range(feature_count):
            category = categories[i % len(categories)]
            feature = create_loaded_feature(
                name=f"feature_{i}",
                display_name=f"Feature {i}",
                description=f"Test feature {i}",
                icon="📦",
                color="cyan",
                category=category,
            )
            registry._register(feature)
            features_by_category[category].append(feature)
        
        cli = CLIIntegration(console=console, registry=registry)
        
        # Verify filtering by each category
        for category in FeatureCategory:
            options = cli.build_menu_options(category=category)
            expected_names = {f.manifest.name for f in features_by_category[category]}
            result_names = {f.manifest.name for _, f in options}
            
            assert result_names == expected_names, (
                f"Category {category}: expected {expected_names}, got {result_names}"
            )

    @settings(max_examples=100)
    @given(
        feature_count=st.integers(min_value=2, max_value=10),
        enabled_flags=st.lists(st.booleans(), min_size=10, max_size=10),
    )
    def test_menu_options_exclude_disabled_features(self, feature_count, enabled_flags):
        """
        Feature: contrib-discovery, Property 5: Menu Rendering Completeness
        
        For any set of features, build_menu_options should exclude
        disabled features by default.
        
        Validates: Requirements 5.1
        """
        registry = FeatureRegistry()
        console, _ = create_test_console()
        
        # Create features with various enabled states
        enabled_features = []
        
        for i in range(feature_count):
            enabled = enabled_flags[i % len(enabled_flags)]
            feature = create_loaded_feature(
                name=f"feature_{i}",
                display_name=f"Feature {i}",
                description=f"Test feature {i}",
                icon="📦",
                color="cyan",
                category=FeatureCategory.UTILITY,
                enabled=enabled,
            )
            registry._register(feature)
            if enabled:
                enabled_features.append(feature)
        
        cli = CLIIntegration(console=console, registry=registry)
        options = cli.build_menu_options(include_disabled=False)
        
        # Verify only enabled features are included
        expected_names = {f.manifest.name for f in enabled_features}
        result_names = {f.manifest.name for _, f in options}
        
        assert result_names == expected_names, (
            f"Expected enabled features {expected_names}, got {result_names}"
        )



class TestFeatureExecutionContractProperty:
    """Property-based tests for Feature Execution Contract (Property 6).
    
    For any feature execution, the run function shall receive a FeatureContext
    containing all required fields (console, llm_client, history, config, analytics),
    and both sync and async run functions shall be handled correctly.
    
    Validates: Requirements 6.1, 6.2, 6.4
    """

    @settings(max_examples=100)
    @given(
        feature_names=st.lists(
            feature_name_strategy,
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    def test_sync_run_receives_complete_context(self, feature_names):
        """
        Feature: contrib-discovery, Property 6: Feature Execution Contract
        
        For any sync feature execution, the run function should receive
        a FeatureContext with all required fields.
        
        Validates: Requirements 6.1, 6.2
        """
        registry = FeatureRegistry()
        console, _ = create_test_console()
        
        # Track contexts received by features
        received_contexts = []
        
        def capture_context_run(ctx):
            received_contexts.append(ctx)
            return FeatureResult(success=True, message="Captured context")
        
        # Create and register features
        for name in feature_names:
            feature = create_loaded_feature(
                name=name,
                display_name=f"Feature {name}",
                description=f"Test feature {name}",
                icon="📦",
                color="cyan",
                category=FeatureCategory.UTILITY,
                run_func=capture_context_run,
            )
            registry._register(feature)
        
        # Create CLI integration with all context fields
        mock_llm = object()
        mock_history = object()
        mock_config = object()
        mock_analytics = object()
        mock_builder = object()
        
        cli = CLIIntegration(
            console=console,
            llm_client=mock_llm,
            history=mock_history,
            config=mock_config,
            analytics=mock_analytics,
            prompt_builder=mock_builder,
            registry=registry,
        )
        
        # Execute each feature
        for name in feature_names:
            feature = registry.get(name)
            result = cli.execute_feature_sync(feature)
            assert result.success, f"Feature {name} execution failed: {result.error}"
        
        # Verify all contexts have required fields
        assert len(received_contexts) == len(feature_names)
        for ctx in received_contexts:
            assert isinstance(ctx, FeatureContext)
            assert ctx.console is console
            assert ctx.llm_client is mock_llm
            assert ctx.history is mock_history
            assert ctx.config is mock_config
            assert ctx.analytics is mock_analytics
            assert ctx.prompt_builder is mock_builder

    @settings(max_examples=100)
    @given(
        feature_names=st.lists(
            feature_name_strategy,
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    def test_async_run_receives_complete_context(self, feature_names):
        """
        Feature: contrib-discovery, Property 6: Feature Execution Contract
        
        For any async feature execution, the run function should receive
        a FeatureContext with all required fields.
        
        Validates: Requirements 6.1, 6.2, 6.4
        """
        registry = FeatureRegistry()
        console, _ = create_test_console()
        
        # Track contexts received by features
        received_contexts = []
        
        async def async_capture_context_run(ctx):
            received_contexts.append(ctx)
            return FeatureResult(success=True, message="Captured context async")
        
        # Create and register features with async run
        for name in feature_names:
            feature = create_loaded_feature(
                name=name,
                display_name=f"Feature {name}",
                description=f"Test feature {name}",
                icon="📦",
                color="cyan",
                category=FeatureCategory.UTILITY,
                run_func=async_capture_context_run,
            )
            registry._register(feature)
        
        # Create CLI integration
        mock_llm = object()
        mock_history = object()
        mock_config = object()
        mock_analytics = object()
        mock_builder = object()
        
        cli = CLIIntegration(
            console=console,
            llm_client=mock_llm,
            history=mock_history,
            config=mock_config,
            analytics=mock_analytics,
            prompt_builder=mock_builder,
            registry=registry,
        )
        
        # Execute each feature using sync wrapper
        for name in feature_names:
            feature = registry.get(name)
            result = cli.execute_feature_sync(feature)
            assert result.success, f"Async feature {name} execution failed: {result.error}"
        
        # Verify all contexts have required fields
        assert len(received_contexts) == len(feature_names)
        for ctx in received_contexts:
            assert isinstance(ctx, FeatureContext)
            assert ctx.console is console
            assert ctx.llm_client is mock_llm

    @settings(max_examples=100)
    @given(
        success_flags=st.lists(st.booleans(), min_size=1, max_size=10),
        messages=st.lists(simple_text, min_size=10, max_size=10),
    )
    def test_feature_result_propagation(self, success_flags, messages):
        """
        Feature: contrib-discovery, Property 6: Feature Execution Contract
        
        For any feature execution, the FeatureResult returned by the run
        function should be propagated correctly.
        
        Validates: Requirements 6.1
        """
        registry = FeatureRegistry()
        console, _ = create_test_console()
        
        # Create features that return specific results
        expected_results = []
        
        for i, success in enumerate(success_flags):
            message = messages[i % len(messages)]
            expected_result = FeatureResult(
                success=success,
                message=message,
                error=None if success else "Test error",
            )
            expected_results.append(expected_result)
            
            # Create a closure to capture the expected result
            def make_run(result):
                def run(ctx):
                    return result
                return run
            
            feature = create_loaded_feature(
                name=f"feature_{i}",
                display_name=f"Feature {i}",
                description=f"Test feature {i}",
                icon="📦",
                color="cyan",
                category=FeatureCategory.UTILITY,
                run_func=make_run(expected_result),
            )
            registry._register(feature)
        
        cli = CLIIntegration(console=console, registry=registry)
        
        # Execute each feature and verify result propagation
        for i, expected in enumerate(expected_results):
            feature = registry.get(f"feature_{i}")
            result = cli.execute_feature_sync(feature)
            
            assert result.success == expected.success, (
                f"Feature {i}: expected success={expected.success}, got {result.success}"
            )
            assert result.message == expected.message, (
                f"Feature {i}: expected message={expected.message}, got {result.message}"
            )

    @settings(max_examples=100)
    @given(
        error_messages=st.lists(simple_text, min_size=1, max_size=5),
    )
    def test_exception_handling_returns_error_result(self, error_messages):
        """
        Feature: contrib-discovery, Property 6: Feature Execution Contract
        
        For any feature that raises an exception, execute_feature should
        return a FeatureResult with success=False and the error message.
        
        Validates: Requirements 6.3
        """
        registry = FeatureRegistry()
        console, _ = create_test_console()
        
        for i, error_msg in enumerate(error_messages):
            # Create a feature that raises an exception
            def make_failing_run(msg):
                def run(ctx):
                    raise RuntimeError(msg)
                return run
            
            feature = create_loaded_feature(
                name=f"failing_feature_{i}",
                display_name=f"Failing Feature {i}",
                description=f"Test failing feature {i}",
                icon="📦",
                color="cyan",
                category=FeatureCategory.UTILITY,
                run_func=make_failing_run(error_msg),
            )
            registry._register(feature)
        
        cli = CLIIntegration(console=console, registry=registry)
        
        # Execute each failing feature
        for i, error_msg in enumerate(error_messages):
            feature = registry.get(f"failing_feature_{i}")
            result = cli.execute_feature_sync(feature)
            
            assert result.success is False, f"Feature {i} should have failed"
            assert result.error is not None, f"Feature {i} should have error message"
            assert error_msg in result.error, (
                f"Feature {i}: expected '{error_msg}' in error, got '{result.error}'"
            )
