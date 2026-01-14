"""Property-based tests for Feature Registry.

Feature: contrib-discovery
Property 4: Registry Query Correctness
Validates: Requirements 4.1, 4.2, 4.3, 4.4
"""

import pytest
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume

from src.workbench.registry import (
    FeatureRegistry,
    get_registry,
    reset_registry,
)
from src.workbench.discovery import (
    DiscoveryEngine,
    LoadedFeature,
)
from src.workbench.contract import (
    FeatureCategory,
    FeatureManifest,
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
    
    def run(ctx):
        return FeatureResult(success=True, message="Test")
    
    return LoadedFeature(
        manifest=manifest,
        run=run,
        module_path=f"/test/{name}",
    )


class TestRegistryQueryCorrectnessProperty:
    """Property-based tests for Registry Query Correctness (Property 4).
    
    For any set of registered features, the Feature_Registry shall:
    - Return the correct feature when queried by name
    - Return exactly the features matching a category when filtered
    - Correctly report the requires_api_key status for each feature
    
    Validates: Requirements 4.1, 4.2, 4.3, 4.4
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
    def test_get_returns_correct_feature_by_name(
        self, feature_names, display_names, descriptions, icons, colors, categories
    ):
        """
        Feature: contrib-discovery, Property 4: Registry Query Correctness
        
        For any registered feature, get(name) should return that exact feature.
        
        Validates: Requirements 4.4
        """
        registry = FeatureRegistry()
        
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
            )
            features.append(feature)
            registry._register(feature)
        
        # Verify each feature can be retrieved by name
        for feature in features:
            retrieved = registry.get(feature.manifest.name)
            assert retrieved is not None, f"Feature {feature.manifest.name} not found"
            assert retrieved.manifest.name == feature.manifest.name
            assert retrieved.manifest.display_name == feature.manifest.display_name
            assert retrieved.manifest.category == feature.manifest.category
        
        # Verify non-existent names return None
        assert registry.get("nonexistent_feature_xyz") is None

    @settings(max_examples=100)
    @given(
        feature_count=st.integers(min_value=1, max_value=10),
        categories=st.lists(category_strategy, min_size=10, max_size=10),
    )
    def test_list_by_category_returns_exact_matches(self, feature_count, categories):
        """
        Feature: contrib-discovery, Property 4: Registry Query Correctness
        
        For any category filter, list_by_category should return exactly
        the features in that category.
        
        Validates: Requirements 4.2
        """
        registry = FeatureRegistry()
        
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
        
        # Verify each category returns correct features
        for category in FeatureCategory:
            result = registry.list_by_category(category)
            expected_names = {f.manifest.name for f in features_by_category[category]}
            result_names = {f.manifest.name for f in result}
            
            assert result_names == expected_names, (
                f"Category {category}: expected {expected_names}, got {result_names}"
            )


    @settings(max_examples=100)
    @given(
        feature_count=st.integers(min_value=1, max_value=10),
        api_key_flags=st.lists(st.booleans(), min_size=10, max_size=10),
    )
    def test_list_requiring_api_returns_correct_features(self, feature_count, api_key_flags):
        """
        Feature: contrib-discovery, Property 4: Registry Query Correctness
        
        For any set of features, list_requiring_api should return exactly
        those features where requires_api_key is True.
        
        Validates: Requirements 4.3
        """
        registry = FeatureRegistry()
        
        # Create features with various API key requirements
        expected_api_features = []
        
        for i in range(feature_count):
            requires_api = api_key_flags[i % len(api_key_flags)]
            feature = create_loaded_feature(
                name=f"feature_{i}",
                display_name=f"Feature {i}",
                description=f"Test feature {i}",
                icon="📦",
                color="cyan",
                category=FeatureCategory.UTILITY,
                requires_api_key=requires_api,
            )
            registry._register(feature)
            if requires_api:
                expected_api_features.append(feature)
        
        # Verify list_requiring_api returns correct features
        result = registry.list_requiring_api()
        expected_names = {f.manifest.name for f in expected_api_features}
        result_names = {f.manifest.name for f in result}
        
        assert result_names == expected_names, (
            f"Expected API features {expected_names}, got {result_names}"
        )

    @settings(max_examples=100)
    @given(
        feature_names=st.lists(
            feature_name_strategy,
            min_size=1,
            max_size=10,
            unique=True
        ),
    )
    def test_list_all_returns_all_registered_features(self, feature_names):
        """
        Feature: contrib-discovery, Property 4: Registry Query Correctness
        
        For any set of registered features, list_all should return all of them.
        
        Validates: Requirements 4.1
        """
        registry = FeatureRegistry()
        
        # Register features
        for name in feature_names:
            feature = create_loaded_feature(
                name=name,
                display_name=f"Feature {name}",
                description=f"Test feature {name}",
                icon="📦",
                color="cyan",
                category=FeatureCategory.UTILITY,
            )
            registry._register(feature)
        
        # Verify list_all returns all features
        result = registry.list_all()
        result_names = {f.manifest.name for f in result}
        expected_names = set(feature_names)
        
        assert result_names == expected_names, (
            f"Expected {expected_names}, got {result_names}"
        )
        assert len(result) == len(feature_names)

    @settings(max_examples=100)
    @given(
        feature_count=st.integers(min_value=2, max_value=10),
    )
    def test_duplicate_names_keep_first(self, feature_count):
        """
        Feature: contrib-discovery, Property 4: Registry Query Correctness
        
        When duplicate feature names are registered, the first one should be kept.
        
        Validates: Requirements 4.5
        """
        registry = FeatureRegistry()
        
        # Register first feature with a name
        first_feature = create_loaded_feature(
            name="duplicate_name",
            display_name="First Feature",
            description="First feature with this name",
            icon="📦",
            color="cyan",
            category=FeatureCategory.UTILITY,
        )
        result1 = registry._register(first_feature)
        assert result1 is True, "First registration should succeed"
        
        # Try to register more features with the same name
        for i in range(1, feature_count):
            duplicate_feature = create_loaded_feature(
                name="duplicate_name",
                display_name=f"Duplicate Feature {i}",
                description=f"Duplicate feature {i}",
                icon="🔧",
                color="red",
                category=FeatureCategory.AI,
            )
            result = registry._register(duplicate_feature)
            assert result is False, f"Duplicate registration {i} should fail"
        
        # Verify only first feature is stored
        retrieved = registry.get("duplicate_name")
        assert retrieved is not None
        assert retrieved.manifest.display_name == "First Feature"
        assert retrieved.manifest.category == FeatureCategory.UTILITY
        
        # Verify only one feature in registry
        all_features = registry.list_all()
        assert len(all_features) == 1
