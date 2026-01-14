"""Property-based tests for Error Collection Completeness.

Feature: contrib-discovery
Property 10: Error Collection Completeness
Validates: Requirements 10.2, 10.4
"""

import pytest
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings

from src.workbench.discovery import (
    DiscoveryEngine,
    DiscoveryResult,
    DiscoveryError,
)
from src.workbench.registry import FeatureRegistry
from src.workbench.contract import FeatureCategory


# Strategies for generating test data
feature_name_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz_"),
    min_size=3,
    max_size=15
).filter(lambda x: x and not x.startswith('_') and x.strip())

simple_text = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789 "),
    min_size=1,
    max_size=20
).filter(lambda x: x.strip())


def create_valid_manifest(path: Path, name: str):
    """Create a valid manifest.py file."""
    content = f'''"""Valid manifest for testing."""
from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)

MANIFEST = FeatureManifest(
    name="{name}",
    display_name="Valid {name}",
    description="A valid feature",
    icon="📦",
    color="cyan",
    category=FeatureCategory.UTILITY,
)

def run(ctx: FeatureContext) -> FeatureResult:
    return FeatureResult(success=True, message="OK")
'''
    path.mkdir(parents=True, exist_ok=True)
    (path / "manifest.py").write_text(content)
    (path / "__init__.py").write_text("")


def create_import_error_manifest(path: Path, name: str):
    """Create a manifest.py with a syntax/import error."""
    content = '''"""Manifest with syntax error."""
from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
)

# Intentional syntax error - missing closing parenthesis
MANIFEST = FeatureManifest(
    name="broken",
    display_name="Broken"
    # Missing fields and closing paren
'''
    path.mkdir(parents=True, exist_ok=True)
    (path / "manifest.py").write_text(content)
    (path / "__init__.py").write_text("")


def create_missing_manifest_constant(path: Path, name: str):
    """Create a manifest.py missing the MANIFEST constant."""
    content = '''"""Manifest missing MANIFEST constant."""
from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)

# Note: MANIFEST constant is missing!

def run(ctx: FeatureContext) -> FeatureResult:
    return FeatureResult(success=True, message="OK")
'''
    path.mkdir(parents=True, exist_ok=True)
    (path / "manifest.py").write_text(content)
    (path / "__init__.py").write_text("")


def create_missing_run_function(path: Path, name: str):
    """Create a manifest.py missing the run function."""
    content = f'''"""Manifest missing run function."""
from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
)

MANIFEST = FeatureManifest(
    name="{name}",
    display_name="Missing Run {name}",
    description="Missing run function",
    icon="📦",
    color="cyan",
    category=FeatureCategory.UTILITY,
)

# Note: run function is missing!
'''
    path.mkdir(parents=True, exist_ok=True)
    (path / "manifest.py").write_text(content)
    (path / "__init__.py").write_text("")


def create_missing_required_field(path: Path, name: str, missing_field: str):
    """Create a manifest.py with a missing required field."""
    fields = {
        "name": f'"{name}"',
        "display_name": f'"Display {name}"',
        "description": '"A description"',
        "icon": '"📦"',
        "color": '"cyan"',
        "category": "FeatureCategory.UTILITY",
    }
    
    # Remove the specified field
    if missing_field in fields:
        del fields[missing_field]
    
    fields_str = ",\n    ".join(f"{k}={v}" for k, v in fields.items())
    
    content = f'''"""Manifest with missing field: {missing_field}."""
from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)

MANIFEST = FeatureManifest(
    {fields_str}
)

def run(ctx: FeatureContext) -> FeatureResult:
    return FeatureResult(success=True, message="OK")
'''
    path.mkdir(parents=True, exist_ok=True)
    (path / "manifest.py").write_text(content)
    (path / "__init__.py").write_text("")


def create_missing_dependency(path: Path, name: str, missing_dep: str):
    """Create a manifest.py with a dependency on a non-existent feature."""
    content = f'''"""Manifest with missing dependency."""
from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)

MANIFEST = FeatureManifest(
    name="{name}",
    display_name="Missing Dep {name}",
    description="Has missing dependency",
    icon="📦",
    color="cyan",
    category=FeatureCategory.UTILITY,
    dependencies=["{missing_dep}"],
)

def run(ctx: FeatureContext) -> FeatureResult:
    return FeatureResult(success=True, message="OK")
'''
    path.mkdir(parents=True, exist_ok=True)
    (path / "manifest.py").write_text(content)
    (path / "__init__.py").write_text("")


def create_circular_dependency(path: Path, name: str, depends_on: str):
    """Create a manifest.py that creates a circular dependency."""
    content = f'''"""Manifest with circular dependency."""
from src.workbench.contract import (
    FeatureManifest,
    FeatureCategory,
    FeatureContext,
    FeatureResult,
)

MANIFEST = FeatureManifest(
    name="{name}",
    display_name="Circular {name}",
    description="Has circular dependency",
    icon="📦",
    color="cyan",
    category=FeatureCategory.UTILITY,
    dependencies=["{depends_on}"],
)

def run(ctx: FeatureContext) -> FeatureResult:
    return FeatureResult(success=True, message="OK")
'''
    path.mkdir(parents=True, exist_ok=True)
    (path / "manifest.py").write_text(content)
    (path / "__init__.py").write_text("")


class TestErrorCollectionCompletenessProperty:
    """Property-based tests for Error Collection Completeness (Property 10).
    
    For any set of discovery errors (import failures, validation failures,
    dependency errors), all errors shall be collected and included in the
    DiscoveryResult.errors list with their file paths and error messages.
    
    Validates: Requirements 10.2, 10.4
    """

    @settings(max_examples=100)
    @given(
        valid_count=st.integers(min_value=0, max_value=3),
        import_error_count=st.integers(min_value=0, max_value=2),
    )
    def test_import_errors_collected(self, valid_count, import_error_count):
        """
        Feature: contrib-discovery, Property 10: Error Collection Completeness
        
        For any set of features with import errors, all import errors
        should be collected in the errors list with file paths.
        
        Validates: Requirements 10.2, 10.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create valid features
            for i in range(valid_count):
                create_valid_manifest(contrib_path / f"valid_{i}", f"valid_{i}")
            
            # Create features with import errors
            import_error_paths = []
            for i in range(import_error_count):
                path = contrib_path / f"import_error_{i}"
                create_import_error_manifest(path, f"import_error_{i}")
                import_error_paths.append(str(path))
            
            # Run discovery
            engine = DiscoveryEngine(contrib_path=contrib_path)
            result = engine.discover()
            
            # Verify valid features are loaded
            assert len(result.features) == valid_count
            
            # Verify import errors are collected
            import_errors = [e for e in result.errors if e.error_type == "import"]
            assert len(import_errors) == import_error_count
            
            # Verify each error has file path and message
            for error in import_errors:
                assert error.feature_path, "Error should have feature_path"
                assert error.message, "Error should have message"

    @settings(max_examples=100)
    @given(
        valid_count=st.integers(min_value=0, max_value=3),
        missing_manifest_count=st.integers(min_value=0, max_value=2),
        missing_run_count=st.integers(min_value=0, max_value=2),
    )
    def test_validation_errors_collected(
        self, valid_count, missing_manifest_count, missing_run_count
    ):
        """
        Feature: contrib-discovery, Property 10: Error Collection Completeness
        
        For any set of features with validation errors (missing MANIFEST,
        missing run), all validation errors should be collected.
        
        Validates: Requirements 10.2, 10.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create valid features
            for i in range(valid_count):
                create_valid_manifest(contrib_path / f"valid_{i}", f"valid_{i}")
            
            # Create features missing MANIFEST constant
            for i in range(missing_manifest_count):
                path = contrib_path / f"no_manifest_{i}"
                create_missing_manifest_constant(path, f"no_manifest_{i}")
            
            # Create features missing run function
            for i in range(missing_run_count):
                path = contrib_path / f"no_run_{i}"
                create_missing_run_function(path, f"no_run_{i}")
            
            # Run discovery
            engine = DiscoveryEngine(contrib_path=contrib_path)
            result = engine.discover()
            
            # Verify valid features are loaded
            assert len(result.features) == valid_count
            
            # Verify validation errors are collected
            validation_errors = [e for e in result.errors if e.error_type == "validation"]
            expected_validation_errors = missing_manifest_count + missing_run_count
            assert len(validation_errors) == expected_validation_errors
            
            # Verify each error has file path and descriptive message
            for error in validation_errors:
                assert error.feature_path, "Error should have feature_path"
                assert error.message, "Error should have message"
                # Message should indicate what's missing
                assert "Missing" in error.message or "missing" in error.message.lower()

    @settings(max_examples=100)
    @given(
        valid_count=st.integers(min_value=1, max_value=3),
        missing_dep_count=st.integers(min_value=1, max_value=3),
    )
    def test_dependency_errors_collected(self, valid_count, missing_dep_count):
        """
        Feature: contrib-discovery, Property 10: Error Collection Completeness
        
        For any set of features with missing dependencies, all dependency
        errors should be collected with the missing dependency names.
        
        Validates: Requirements 10.2, 10.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create valid features (no dependencies)
            for i in range(valid_count):
                create_valid_manifest(contrib_path / f"valid_{i}", f"valid_{i}")
            
            # Create features with missing dependencies
            for i in range(missing_dep_count):
                path = contrib_path / f"missing_dep_{i}"
                create_missing_dependency(
                    path,
                    f"missing_dep_{i}",
                    f"nonexistent_feature_{i}"
                )
            
            # Run discovery
            engine = DiscoveryEngine(contrib_path=contrib_path)
            result = engine.discover()
            
            # Verify valid features are loaded
            assert len(result.features) == valid_count
            
            # Verify dependency errors are collected
            dep_errors = [e for e in result.errors if e.error_type == "dependency"]
            assert len(dep_errors) == missing_dep_count
            
            # Verify each error mentions the missing dependency
            for i, error in enumerate(dep_errors):
                assert error.feature_path, "Error should have feature_path"
                assert error.message, "Error should have message"
                assert "Missing dependencies" in error.message

    @settings(max_examples=100)
    @given(
        cycle_size=st.integers(min_value=2, max_value=4),
    )
    def test_circular_dependency_errors_collected(self, cycle_size):
        """
        Feature: contrib-discovery, Property 10: Error Collection Completeness
        
        For any circular dependency, the error should be collected
        with information about the circular features.
        
        Validates: Requirements 10.2, 10.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create a circular dependency chain
            feature_names = [f"circular_{i}" for i in range(cycle_size)]
            
            for i, name in enumerate(feature_names):
                path = contrib_path / name
                # Each feature depends on the next (wrapping around)
                next_idx = (i + 1) % cycle_size
                create_circular_dependency(path, name, feature_names[next_idx])
            
            # Run discovery
            engine = DiscoveryEngine(contrib_path=contrib_path)
            result = engine.discover()
            
            # Verify circular dependency error is collected
            circular_errors = [
                e for e in result.errors
                if "Circular dependency" in e.message
            ]
            assert len(circular_errors) > 0, "Should detect circular dependency"
            
            # Verify error message mentions the circular features
            error_msg = circular_errors[0].message
            for name in feature_names:
                assert name in error_msg, f"Error should mention {name}"

    @settings(max_examples=100)
    @given(
        valid_count=st.integers(min_value=0, max_value=2),
        import_error_count=st.integers(min_value=0, max_value=2),
        validation_error_count=st.integers(min_value=0, max_value=2),
        dep_error_count=st.integers(min_value=0, max_value=2),
    )
    def test_mixed_errors_all_collected(
        self, valid_count, import_error_count, validation_error_count, dep_error_count
    ):
        """
        Feature: contrib-discovery, Property 10: Error Collection Completeness
        
        For any mix of error types (import, validation, dependency),
        all errors should be collected in the errors list.
        
        Validates: Requirements 10.2, 10.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create valid features
            for i in range(valid_count):
                create_valid_manifest(contrib_path / f"valid_{i}", f"valid_{i}")
            
            # Create features with import errors
            for i in range(import_error_count):
                path = contrib_path / f"import_err_{i}"
                create_import_error_manifest(path, f"import_err_{i}")
            
            # Create features with validation errors (missing run)
            for i in range(validation_error_count):
                path = contrib_path / f"validation_err_{i}"
                create_missing_run_function(path, f"validation_err_{i}")
            
            # Create features with dependency errors
            for i in range(dep_error_count):
                path = contrib_path / f"dep_err_{i}"
                create_missing_dependency(path, f"dep_err_{i}", f"nonexistent_{i}")
            
            # Run discovery
            engine = DiscoveryEngine(contrib_path=contrib_path)
            result = engine.discover()
            
            # Verify valid features are loaded
            assert len(result.features) == valid_count
            
            # Verify total error count
            expected_errors = import_error_count + validation_error_count + dep_error_count
            assert len(result.errors) == expected_errors, (
                f"Expected {expected_errors} errors, got {len(result.errors)}: "
                f"{[e.message for e in result.errors]}"
            )
            
            # Verify error types are correct
            import_errors = [e for e in result.errors if e.error_type == "import"]
            validation_errors = [e for e in result.errors if e.error_type == "validation"]
            dep_errors = [e for e in result.errors if e.error_type == "dependency"]
            
            assert len(import_errors) == import_error_count
            assert len(validation_errors) == validation_error_count
            assert len(dep_errors) == dep_error_count

    @settings(max_examples=100)
    @given(
        error_count=st.integers(min_value=1, max_value=5),
    )
    def test_errors_accessible_through_registry(self, error_count):
        """
        Feature: contrib-discovery, Property 10: Error Collection Completeness
        
        For any discovery errors, they should be accessible through
        the registry's get_errors() method after loading.
        
        Validates: Requirements 10.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create features with errors
            for i in range(error_count):
                path = contrib_path / f"error_feature_{i}"
                create_missing_run_function(path, f"error_feature_{i}")
            
            # Run discovery through registry
            engine = DiscoveryEngine(contrib_path=contrib_path)
            registry = FeatureRegistry()
            registry.load(engine)
            
            # Verify errors are accessible through registry
            assert registry.has_errors()
            errors = registry.get_errors()
            assert len(errors) == error_count
            
            # Verify each error has required fields
            for error in errors:
                assert isinstance(error, DiscoveryError)
                assert error.feature_path
                assert error.error_type
                assert error.message

    @settings(max_examples=100)
    @given(
        legacy_count=st.integers(min_value=1, max_value=3),
    )
    def test_legacy_warnings_collected(self, legacy_count):
        """
        Feature: contrib-discovery, Property 10: Error Collection Completeness
        
        For any legacy features (service.py without manifest.py),
        warnings should be collected.
        
        Validates: Requirements 10.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            contrib_path = Path(tmpdir) / "contrib"
            contrib_path.mkdir()
            
            # Create legacy features (service.py without manifest.py)
            for i in range(legacy_count):
                path = contrib_path / f"legacy_{i}"
                path.mkdir()
                (path / "__init__.py").write_text("")
                (path / "service.py").write_text('''
class LegacyService:
    pass
''')
            
            # Run discovery
            engine = DiscoveryEngine(contrib_path=contrib_path)
            result = engine.discover()
            
            # Verify legacy features are loaded (with default manifest)
            assert len(result.features) == legacy_count
            
            # Verify warnings are collected
            assert len(result.warnings) == legacy_count
            
            # Verify each warning mentions legacy format
            for warning in result.warnings:
                assert "legacy" in warning.lower()
