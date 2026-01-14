"""Property-based tests for Manifest Module Contract.

Feature: contrib-discovery
Property 2: Manifest Module Contract
Validates: Requirements 2.2, 2.3
"""

import pytest
import inspect
import importlib.util
from pathlib import Path
from hypothesis import given, strategies as st, settings

from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)


# List of all manifest file paths to test (relative to workspace root)
MANIFEST_FILES = [
    "src/workbench/contrib/history/manifest.py",
    "src/workbench/contrib/optimizer/manifest.py",
    "src/workbench/contrib/chains/manifest.py",
    "src/workbench/contrib/templates/manifest.py",
    "src/workbench/contrib/analytics/manifest.py",
    "src/workbench/contrib/testing/manifest.py",
    "src/workbench/contrib/nlgen/manifest.py",
    "src/workbench/contrib/variables/manifest.py",
]


def load_manifest_module(file_path: str):
    """Load a manifest module directly from file without triggering package __init__.py."""
    path = Path(file_path)
    module_name = f"manifest_{path.parent.name}"
    
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {file_path}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestManifestModuleContractProperty:
    """Property-based tests for Manifest Module Contract (Property 2).
    
    For any valid manifest module, it must export both a MANIFEST constant
    of type FeatureManifest and a run function that accepts FeatureContext
    and returns FeatureResult or Awaitable[FeatureResult].
    
    Validates: Requirements 2.2, 2.3
    """

    @pytest.mark.parametrize("file_path", MANIFEST_FILES)
    def test_manifest_module_exports_manifest_constant(self, file_path):
        """
        Feature: contrib-discovery, Property 2: Manifest Module Contract
        
        For any manifest module, it must export a MANIFEST constant
        of type FeatureManifest.
        
        Validates: Requirements 2.2
        """
        module = load_manifest_module(file_path)
        
        # Must have MANIFEST constant
        assert hasattr(module, 'MANIFEST'), f"{file_path} must export MANIFEST constant"
        
        # MANIFEST must be a FeatureManifest instance
        manifest = module.MANIFEST
        assert isinstance(manifest, FeatureManifest), (
            f"{file_path}.MANIFEST must be FeatureManifest, got {type(manifest)}"
        )

    @pytest.mark.parametrize("file_path", MANIFEST_FILES)
    def test_manifest_module_exports_run_function(self, file_path):
        """
        Feature: contrib-discovery, Property 2: Manifest Module Contract
        
        For any manifest module, it must export a run function.
        
        Validates: Requirements 2.3
        """
        module = load_manifest_module(file_path)
        
        # Must have run function
        assert hasattr(module, 'run'), f"{file_path} must export run function"
        
        # run must be callable
        run_func = module.run
        assert callable(run_func), f"{file_path}.run must be callable"

    @pytest.mark.parametrize("file_path", MANIFEST_FILES)
    def test_manifest_has_required_fields(self, file_path):
        """
        Feature: contrib-discovery, Property 2: Manifest Module Contract
        
        For any manifest module, the MANIFEST must have all required fields
        with non-empty values.
        
        Validates: Requirements 2.2, 1.1
        """
        module = load_manifest_module(file_path)
        manifest = module.MANIFEST
        
        # Check required fields are non-empty
        assert manifest.name and manifest.name.strip(), f"{file_path}: name must be non-empty"
        assert manifest.display_name and manifest.display_name.strip(), f"{file_path}: display_name must be non-empty"
        assert manifest.description and manifest.description.strip(), f"{file_path}: description must be non-empty"
        assert manifest.icon and manifest.icon.strip(), f"{file_path}: icon must be non-empty"
        assert manifest.color and manifest.color.strip(), f"{file_path}: color must be non-empty"
        assert isinstance(manifest.category, FeatureCategory), f"{file_path}: category must be FeatureCategory"

    @pytest.mark.parametrize("file_path", MANIFEST_FILES)
    def test_run_function_accepts_context(self, file_path):
        """
        Feature: contrib-discovery, Property 2: Manifest Module Contract
        
        For any manifest module, the run function must accept a FeatureContext
        parameter.
        
        Validates: Requirements 2.3
        """
        module = load_manifest_module(file_path)
        run_func = module.run
        
        # Get function signature
        sig = inspect.signature(run_func)
        params = list(sig.parameters.values())
        
        # Must have at least one parameter (ctx)
        assert len(params) >= 1, f"{file_path}.run must accept at least one parameter"
        
        # First parameter should be named 'ctx' or similar
        first_param = params[0]
        assert first_param.name in ('ctx', 'context'), (
            f"{file_path}.run first parameter should be named 'ctx' or 'context', got '{first_param.name}'"
        )

    @pytest.mark.parametrize("file_path", MANIFEST_FILES)
    def test_manifest_category_matches_api_requirement(self, file_path):
        """
        Feature: contrib-discovery, Property 2: Manifest Module Contract
        
        For any manifest module with category=AI, requires_api_key should be True.
        
        Validates: Requirements 2.2, 1.5
        """
        module = load_manifest_module(file_path)
        manifest = module.MANIFEST
        
        # AI features should require API key
        if manifest.category == FeatureCategory.AI:
            assert manifest.requires_api_key is True, (
                f"{file_path}: AI features should have requires_api_key=True"
            )

    @settings(max_examples=100)
    @given(file_idx=st.integers(min_value=0, max_value=len(MANIFEST_FILES) - 1))
    def test_manifest_name_matches_directory(self, file_idx):
        """
        Feature: contrib-discovery, Property 2: Manifest Module Contract
        
        For any manifest module, the manifest name should be consistent
        with the module's directory name.
        
        Validates: Requirements 2.2
        """
        file_path = MANIFEST_FILES[file_idx]
        module = load_manifest_module(file_path)
        manifest = module.MANIFEST
        
        # Extract expected name from file path
        # e.g., "src/workbench/contrib/history/manifest.py" -> "history"
        path = Path(file_path)
        expected_name = path.parent.name
        
        assert manifest.name == expected_name, (
            f"Manifest name '{manifest.name}' should match directory name '{expected_name}'"
        )


class TestManifestModuleUniqueness:
    """Tests for manifest uniqueness across all modules."""

    def test_all_manifest_names_unique(self):
        """
        Feature: contrib-discovery, Property 2: Manifest Module Contract
        
        All manifest modules must have unique names.
        
        Validates: Requirements 2.2, 4.5
        """
        names = []
        for file_path in MANIFEST_FILES:
            module = load_manifest_module(file_path)
            names.append(module.MANIFEST.name)
        
        assert len(names) == len(set(names)), (
            f"Duplicate manifest names found: {[n for n in names if names.count(n) > 1]}"
        )

    def test_all_menu_keys_unique_or_none(self):
        """
        Feature: contrib-discovery, Property 2: Manifest Module Contract
        
        All manifest modules with menu_key set must have unique keys.
        
        Validates: Requirements 2.2
        """
        keys = []
        for file_path in MANIFEST_FILES:
            module = load_manifest_module(file_path)
            key = module.MANIFEST.menu_key
            if key is not None:
                keys.append((key, module.MANIFEST.name))
        
        key_values = [k for k, _ in keys]
        assert len(key_values) == len(set(key_values)), (
            f"Duplicate menu keys found: {[(k, n) for k, n in keys if key_values.count(k) > 1]}"
        )


class TestManifestCategoryDistribution:
    """Tests for proper category distribution across manifests."""

    def test_categories_properly_assigned(self):
        """
        Feature: contrib-discovery, Property 2: Manifest Module Contract
        
        Manifests should be assigned to appropriate categories based on
        their functionality.
        
        Validates: Requirements 2.2, 9.1
        """
        expected_categories = {
            "history": FeatureCategory.STORAGE,
            "optimizer": FeatureCategory.AI,
            "chains": FeatureCategory.AI,
            "templates": FeatureCategory.CORE,
            "analytics": FeatureCategory.UTILITY,
            "testing": FeatureCategory.AI,
            "nlgen": FeatureCategory.AI,
            "variables": FeatureCategory.UTILITY,
        }
        
        for file_path in MANIFEST_FILES:
            module = load_manifest_module(file_path)
            manifest = module.MANIFEST
            
            if manifest.name in expected_categories:
                expected = expected_categories[manifest.name]
                assert manifest.category == expected, (
                    f"{manifest.name} should have category {expected}, got {manifest.category}"
                )
