"""Property-based tests for Discovery Engine.

Feature: contrib-discovery
Property 3: Discovery Completeness
Property 7: Dependency Resolution Correctness
Validates: Requirements 3.1, 3.2, 3.3, 7.2, 7.4
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume

from src.workbench.discovery import (
    DiscoveryEngine,
    LoadedFeature,
    DiscoveryResult,
    DiscoveryError,
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

# Use simple alphanumeric text to avoid escaping issues in generated Python code
simple_text = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789 "),
    min_size=1,
    max_size=30
).filter(lambda x: x.strip())

emoji_text = st.sampled_from(["📦", "🔧", "⚡", "🎯", "💡", "🚀", "✨", "🔍"])
color_text = st.sampled_from(["cyan", "green", "yellow", "red", "blue", "magenta", "white"])
category_strategy = st.sampled_from(list(FeatureCategory))


def escape_string(s: str) -> str:
    """Escape special characters for Python string literals."""
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


def create_manifest_file(path: Path, name: str, display_name: str, description: str,
                         icon: str, color: str, category: FeatureCategory,
                         dependencies: list[str] = None):
    """Helper to create a valid manifest.py file."""
    deps_str = str(dependencies or [])
    # Escape special characters in string fields
    name_escaped = escape_string(name)
    display_name_escaped = escape_string(display_name)
    description_escaped = escape_string(description)
    
    content = f'''"""Auto-generated manifest for testing."""
from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)

MANIFEST = FeatureManifest(
    name="{name_escaped}",
    display_name="{display_name_escaped}",
    description="{description_escaped}",
    icon="{icon}",
    color="{color}",
    category=FeatureCategory.{category.name},
    dependencies={deps_str},
)

def run(ctx: FeatureContext) -> FeatureResult:
    return FeatureResult(success=True, message="Test feature executed")
'''
    path.mkdir(parents=True, exist_ok=True)
    (path / "manifest.py").write_text(content)
    (path / "__init__.py").write_text("")


def create_legacy_service_file(path: Path):
    """Helper to create a legacy service.py file."""
    content = '''"""Legacy service for testing."""

class LegacyService:
    def run(self):
        pass
'''
    path.mkdir(parents=True, exist_ok=True)
    (path / "service.py").write_text(content)
    (path / "__init__.py").write_text("")


class TestDiscoveryCompletenessProperty:
    """Property-based tests for Discovery Completeness (Property 3).
    
    For any set of subdirectories in src/contrib/ containing valid manifest.py files,
    the Discovery_System shall find, import, validate, and register all of them.
    
    Validates: Requirements 3.1, 3.2, 3.3
    """

    @settings(max_examples=100)
    @given(
        feature_names=st.lists(
            feature_name_strategy,
            min_size=1,
            max_size=5,
            unique=True
        ),
        display_names=st.lists(simple_text, min_size=5, max_size=5),
        descriptions=st.lists(simple_text, min_size=5, max_size=5),
        icons=st.lists(emoji_text, min_size=5, max_size=5),
        colors=st.lists(color_text, min_size=5, max_size=5),
        categories=st.lists(category_strategy, min_size=5, max_size=5),
    )
    def test_all_valid_manifests_discovered(
        self, feature_names, display_names, descriptions, icons, colors, categories
    ):
        """
        Feature: contrib-discovery, Property 3: Discovery Completeness
        
        For any set of valid manifest.py files in subdirectories,
        all should be discovered and loaded.
        
        Validates: Requirements 3.1, 3.2, 3.3
        """
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create feature directories with valid manifests
            for i, name in enumerate(feature_names):
                feature_path = contrib_path / name
                create_manifest_file(
                    feature_path,
                    name=name,
                    display_name=display_names[i % len(display_names)],
                    description=descriptions[i % len(descriptions)],
                    icon=icons[i % len(icons)],
                    color=colors[i % len(colors)],
                    category=categories[i % len(categories)],
                )
            
            # Run discovery
            engine = DiscoveryEngine(contrib_path=contrib_path)
            result = engine.discover()
            
            # All valid features should be discovered
            discovered_names = {f.manifest.name for f in result.features}
            expected_names = set(feature_names)
            
            assert discovered_names == expected_names, (
                f"Expected {expected_names}, got {discovered_names}. "
                f"Errors: {[e.message for e in result.errors]}"
            )

    @settings(max_examples=100)
    @given(
        valid_count=st.integers(min_value=1, max_value=3),
        legacy_count=st.integers(min_value=1, max_value=3),
    )
    def test_mixed_manifest_and_legacy_discovery(self, valid_count, legacy_count):
        """
        Feature: contrib-discovery, Property 3: Discovery Completeness
        
        For any mix of manifest.py and legacy service.py features,
        all should be discovered (legacy with warnings).
        
        Validates: Requirements 3.1, 3.2, 8.2
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create manifest-based features
            manifest_names = [f"manifest_feature_{i}" for i in range(valid_count)]
            for name in manifest_names:
                feature_path = contrib_path / name
                create_manifest_file(
                    feature_path,
                    name=name,
                    display_name=f"Manifest {name}",
                    description="Test manifest feature",
                    icon="📦",
                    color="cyan",
                    category=FeatureCategory.UTILITY,
                )
            
            # Create legacy features
            legacy_names = [f"legacy_feature_{i}" for i in range(legacy_count)]
            for name in legacy_names:
                feature_path = contrib_path / name
                create_legacy_service_file(feature_path)
            
            # Run discovery
            engine = DiscoveryEngine(contrib_path=contrib_path)
            result = engine.discover()
            
            # All features should be discovered
            discovered_names = {f.manifest.name for f in result.features}
            expected_names = set(manifest_names) | set(legacy_names)
            
            assert discovered_names == expected_names
            
            # Legacy features should generate warnings
            assert len(result.warnings) == legacy_count


class TestDependencyResolutionProperty:
    """Property-based tests for Dependency Resolution (Property 7).
    
    For any set of features with dependencies, the Discovery_System shall load them
    in valid topological order (dependencies before dependents), and shall detect
    and report circular dependencies.
    
    Validates: Requirements 7.2, 7.4
    """

    @settings(max_examples=100)
    @given(
        chain_length=st.integers(min_value=2, max_value=5),
    )
    def test_linear_dependency_chain_ordering(self, chain_length):
        """
        Feature: contrib-discovery, Property 7: Dependency Resolution Correctness
        
        For any linear dependency chain A -> B -> C -> ...,
        features should be loaded in correct order.
        
        Validates: Requirements 7.2
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create a linear dependency chain
            feature_names = [f"feature_{i}" for i in range(chain_length)]
            
            for i, name in enumerate(feature_names):
                feature_path = contrib_path / name
                # Each feature depends on the previous one (except the first)
                deps = [feature_names[i - 1]] if i > 0 else []
                create_manifest_file(
                    feature_path,
                    name=name,
                    display_name=f"Feature {i}",
                    description=f"Test feature {i}",
                    icon="📦",
                    color="cyan",
                    category=FeatureCategory.UTILITY,
                    dependencies=deps,
                )
            
            # Run discovery
            engine = DiscoveryEngine(contrib_path=contrib_path)
            result = engine.discover()
            
            # All features should be loaded
            assert len(result.features) == chain_length
            assert len(result.errors) == 0
            
            # Features should be in dependency order
            loaded_names = [f.manifest.name for f in result.features]
            for i in range(1, chain_length):
                dep_idx = loaded_names.index(feature_names[i - 1])
                feat_idx = loaded_names.index(feature_names[i])
                assert dep_idx < feat_idx, (
                    f"Dependency {feature_names[i-1]} should come before {feature_names[i]}"
                )

    @settings(max_examples=100)
    @given(
        cycle_size=st.integers(min_value=2, max_value=4),
    )
    def test_circular_dependency_detection(self, cycle_size):
        """
        Feature: contrib-discovery, Property 7: Dependency Resolution Correctness
        
        For any circular dependency (A -> B -> ... -> A),
        the system should detect and report it.
        
        Validates: Requirements 7.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create a circular dependency
            feature_names = [f"circular_{i}" for i in range(cycle_size)]
            
            for i, name in enumerate(feature_names):
                feature_path = contrib_path / name
                # Each feature depends on the next one (wrapping around)
                next_idx = (i + 1) % cycle_size
                deps = [feature_names[next_idx]]
                create_manifest_file(
                    feature_path,
                    name=name,
                    display_name=f"Circular {i}",
                    description=f"Circular feature {i}",
                    icon="📦",
                    color="cyan",
                    category=FeatureCategory.UTILITY,
                    dependencies=deps,
                )
            
            # Run discovery
            engine = DiscoveryEngine(contrib_path=contrib_path)
            result = engine.discover()
            
            # Should detect circular dependency
            circular_errors = [
                e for e in result.errors
                if "Circular dependency" in e.message
            ]
            assert len(circular_errors) > 0, "Should detect circular dependency"

    @settings(max_examples=100)
    @given(
        feature_count=st.integers(min_value=1, max_value=3),
    )
    def test_missing_dependency_handling(self, feature_count):
        """
        Feature: contrib-discovery, Property 7: Dependency Resolution Correctness
        
        For any feature with a missing dependency,
        the system should report the error and exclude the feature.
        
        Validates: Requirements 7.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create features with missing dependencies
            for i in range(feature_count):
                name = f"missing_dep_{i}"
                feature_path = contrib_path / name
                create_manifest_file(
                    feature_path,
                    name=name,
                    display_name=f"Missing Dep {i}",
                    description=f"Feature with missing dep {i}",
                    icon="📦",
                    color="cyan",
                    category=FeatureCategory.UTILITY,
                    dependencies=["nonexistent_feature"],
                )
            
            # Run discovery
            engine = DiscoveryEngine(contrib_path=contrib_path)
            result = engine.discover()
            
            # Should report missing dependencies
            missing_errors = [
                e for e in result.errors
                if "Missing dependencies" in e.message
            ]
            assert len(missing_errors) == feature_count
            
            # Features with missing deps should not be loaded
            assert len(result.features) == 0
