"""Property-based tests for Feature Contract types.

Feature: contrib-discovery
Property 1: Manifest Field Validation
Validates: Requirements 1.1, 1.2, 1.4
"""

import pytest
from hypothesis import given, strategies as st, settings

from src.workbench.contract import (
    FeatureCategory,
    FeatureManifest,
    FeatureContext,
    FeatureResult,
)


# Strategies for generating valid manifest data
non_empty_text = st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
emoji_text = st.sampled_from(["📦", "🔧", "⚡", "🎯", "💡", "🚀", "✨", "🔍"])
color_text = st.sampled_from(["cyan", "green", "yellow", "red", "blue", "magenta", "white"])
category_strategy = st.sampled_from(list(FeatureCategory))


class TestFeatureManifestProperty:
    """Property-based tests for FeatureManifest validation."""

    @settings(max_examples=100)
    @given(
        name=non_empty_text,
        display_name=non_empty_text,
        description=non_empty_text,
        icon=emoji_text,
        color=color_text,
        category=category_strategy,
    )
    def test_manifest_required_fields_property(
        self, name, display_name, description, icon, color, category
    ):
        """
        Feature: contrib-discovery, Property 1: Manifest Field Validation
        
        For any non-empty strings for required fields, manifest creation
        should succeed and all fields should be accessible.
        
        Validates: Requirements 1.1, 1.2, 1.4
        """
        manifest = FeatureManifest(
            name=name,
            display_name=display_name,
            description=description,
            icon=icon,
            color=color,
            category=category,
        )
        
        # All required fields must be set correctly
        assert manifest.name == name
        assert manifest.display_name == display_name
        assert manifest.description == description
        assert manifest.icon == icon
        assert manifest.color == color
        assert manifest.category == category
        
        # Required fields must be non-empty
        assert manifest.name
        assert manifest.display_name
        assert manifest.description
        assert manifest.icon
        assert manifest.color
        assert manifest.category is not None

    @settings(max_examples=100)
    @given(
        name=non_empty_text,
        display_name=non_empty_text,
        description=non_empty_text,
        icon=emoji_text,
        color=color_text,
        category=category_strategy,
        version=st.from_regex(r"[0-9]+\.[0-9]+\.[0-9]+", fullmatch=True),
        requires_api_key=st.booleans(),
        enabled=st.booleans(),
        menu_key=st.one_of(st.none(), st.text(min_size=1, max_size=1)),
    )
    def test_manifest_optional_fields_defaults(
        self, name, display_name, description, icon, color, category,
        version, requires_api_key, enabled, menu_key
    ):
        """
        Feature: contrib-discovery, Property 1: Manifest Field Validation
        
        For any manifest with optional fields specified, those fields
        should be set correctly. When not specified, defaults should apply.
        
        Validates: Requirements 1.1, 1.2, 1.4
        """
        # Test with explicit optional values
        manifest_explicit = FeatureManifest(
            name=name,
            display_name=display_name,
            description=description,
            icon=icon,
            color=color,
            category=category,
            version=version,
            requires_api_key=requires_api_key,
            enabled=enabled,
            menu_key=menu_key,
        )
        
        assert manifest_explicit.version == version
        assert manifest_explicit.requires_api_key == requires_api_key
        assert manifest_explicit.enabled == enabled
        assert manifest_explicit.menu_key == menu_key
        
        # Test defaults when optional fields not specified
        manifest_defaults = FeatureManifest(
            name=name,
            display_name=display_name,
            description=description,
            icon=icon,
            color=color,
            category=category,
        )
        
        # Verify default values
        assert manifest_defaults.version == "1.0.0"
        assert manifest_defaults.requires_api_key is False
        assert manifest_defaults.enabled is True
        assert manifest_defaults.menu_key is None
        assert manifest_defaults.dependencies == []

    @settings(max_examples=100)
    @given(category=category_strategy)
    def test_category_is_valid_enum(self, category):
        """
        Feature: contrib-discovery, Property 1: Manifest Field Validation
        
        For any FeatureManifest, the category field must be one of the
        standard FeatureCategory enum values.
        
        Validates: Requirements 1.1, 9.1
        """
        manifest = FeatureManifest(
            name="test",
            display_name="Test",
            description="Test feature",
            icon="📦",
            color="cyan",
            category=category,
        )
        
        assert isinstance(manifest.category, FeatureCategory)
        assert manifest.category in list(FeatureCategory)


class TestFeatureResultProperty:
    """Property-based tests for FeatureResult."""

    @settings(max_examples=100)
    @given(
        success=st.booleans(),
        message=st.text(max_size=100),
        error=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
    )
    def test_feature_result_creation(self, success, message, error):
        """
        Feature: contrib-discovery, Property 1: Manifest Field Validation
        
        For any combination of success, message, and error values,
        FeatureResult should be created correctly.
        
        Validates: Requirements 1.3
        """
        result = FeatureResult(
            success=success,
            message=message,
            error=error,
        )
        
        assert result.success == success
        assert result.message == message
        assert result.error == error


class TestFeatureCategoryProperty:
    """Property-based tests for FeatureCategory enum."""

    def test_all_standard_categories_exist(self):
        """
        Feature: contrib-discovery, Property 1: Manifest Field Validation
        
        The FeatureCategory enum must define all standard categories:
        core, ai, storage, export, utility.
        
        Validates: Requirements 9.1
        """
        expected_categories = {"core", "ai", "storage", "export", "utility"}
        actual_categories = {cat.value for cat in FeatureCategory}
        
        assert expected_categories == actual_categories
