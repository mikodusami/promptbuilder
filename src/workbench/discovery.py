"""Discovery Engine for the contrib feature system.

This module handles scanning, loading, and validating contrib features.
It scans `src/contrib/` but lives in workbench to protect the infrastructure.

Requirements: 3.1, 3.2, 2.1, 2.2, 2.3, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3, 8.4
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable
import importlib.util
import logging

from .contract import FeatureManifest, FeatureCategory, FeatureRunner, FeatureResult


logger = logging.getLogger(__name__)


@dataclass
class LoadedFeature:
    """A successfully loaded and validated feature.
    
    Attributes:
        manifest: The feature's metadata
        run: The feature's run function
        setup: Optional one-time initialization function
        module_path: Path to the feature's directory
    """
    manifest: FeatureManifest
    run: FeatureRunner
    setup: Optional[Callable] = None
    module_path: str = ""


@dataclass
class DiscoveryError:
    """Error encountered during feature discovery.
    
    Attributes:
        feature_path: Path to the feature that caused the error
        error_type: Type of error ("import", "validation", "dependency")
        message: Human-readable error message
    """
    feature_path: str
    error_type: str  # "import", "validation", "dependency"
    message: str


@dataclass
class DiscoveryResult:
    """Result of the discovery process.
    
    Attributes:
        features: List of successfully loaded features
        errors: List of errors encountered during discovery
        warnings: List of warning messages
    """
    features: list[LoadedFeature] = field(default_factory=list)
    errors: list[DiscoveryError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class DiscoveryEngine:
    """Scans and loads contrib features from the filesystem.
    
    The discovery process has three phases:
    1. Scan for manifest.py files in contrib directories
    2. Load and validate each manifest
    3. Resolve dependencies and order features
    
    Requirements: 3.1, 3.2, 2.1, 2.2, 2.3
    """

    def __init__(self, contrib_path: Optional[Path] = None):
        """Initialize the discovery engine.
        
        Args:
            contrib_path: Path to the contrib directory. Defaults to src/workbench/contrib/
        """
        if contrib_path is None:
            # Default to src/workbench/contrib/ relative to this file
            self.contrib_path = Path(__file__).parent / "contrib"
        else:
            self.contrib_path = contrib_path
        self.verbose = False

    def discover(self) -> DiscoveryResult:
        """Scan contrib directory and load all valid features.
        
        Returns:
            DiscoveryResult containing loaded features, errors, and warnings.
            
        Requirements: 3.1, 3.2, 3.3
        """
        result = DiscoveryResult()

        # Phase 1: Scan for manifest files
        candidates = self._scan_directories()

        # Phase 2: Load and validate each manifest
        loaded = []
        for path in candidates:
            feature = self._load_feature(path, result)
            if feature:
                loaded.append(feature)

        # Phase 3: Resolve dependencies and order
        result.features = self._resolve_dependencies(loaded, result)

        return result

    def _scan_directories(self) -> list[Path]:
        """Find all directories with manifest.py or service.py files.
        
        Returns:
            List of paths to candidate feature directories.
            
        Requirements: 3.1
        """
        candidates = []

        if not self.contrib_path.exists():
            return candidates

        for item in self.contrib_path.iterdir():
            if item.is_dir() and not item.name.startswith(('_', '.')):
                manifest_path = item / "manifest.py"
                if manifest_path.exists():
                    candidates.append(item)
                elif (item / "service.py").exists():
                    # Legacy feature without manifest
                    candidates.append(item)

        return candidates

    def _load_feature(self, path: Path, result: DiscoveryResult) -> Optional[LoadedFeature]:
        """Load a single feature from its directory.
        
        Args:
            path: Path to the feature directory
            result: DiscoveryResult to append errors/warnings to
            
        Returns:
            LoadedFeature if successful, None otherwise.
            
        Requirements: 2.1, 2.2, 2.3, 3.2
        """
        manifest_path = path / "manifest.py"

        # Check for legacy feature
        if not manifest_path.exists():
            return self._load_legacy_feature(path, result)

        try:
            # Dynamic import of manifest module
            spec = importlib.util.spec_from_file_location(
                f"contrib.{path.name}.manifest",
                manifest_path
            )
            if spec is None or spec.loader is None:
                result.errors.append(DiscoveryError(
                    feature_path=str(path),
                    error_type="import",
                    message="Failed to create module spec"
                ))
                return None
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Validate required exports
            if not hasattr(module, 'MANIFEST'):
                result.errors.append(DiscoveryError(
                    feature_path=str(path),
                    error_type="validation",
                    message="Missing MANIFEST constant"
                ))
                return None

            if not hasattr(module, 'run'):
                result.errors.append(DiscoveryError(
                    feature_path=str(path),
                    error_type="validation",
                    message="Missing run function"
                ))
                return None

            manifest = module.MANIFEST

            # Validate manifest fields
            validation_error = self._validate_manifest(manifest, path)
            if validation_error:
                result.errors.append(validation_error)
                return None

            return LoadedFeature(
                manifest=manifest,
                run=module.run,
                setup=getattr(module, 'setup', None),
                module_path=str(path)
            )

        except Exception as e:
            result.errors.append(DiscoveryError(
                feature_path=str(path),
                error_type="import",
                message=str(e)
            ))
            return None

    def _validate_manifest(self, manifest: FeatureManifest, path: Path) -> Optional[DiscoveryError]:
        """Validate manifest has all required fields with correct types.
        
        Args:
            manifest: The manifest to validate
            path: Path to the feature directory (for error reporting)
            
        Returns:
            DiscoveryError if validation fails, None otherwise.
            
        Requirements: 1.4, 9.2
        """
        required_fields = ['name', 'display_name', 'description', 'icon', 'color', 'category']

        for field_name in required_fields:
            value = getattr(manifest, field_name, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                return DiscoveryError(
                    feature_path=str(path),
                    error_type="validation",
                    message=f"Missing or empty required field: {field_name}"
                )

        # Validate category is valid enum
        if not isinstance(manifest.category, FeatureCategory):
            return DiscoveryError(
                feature_path=str(path),
                error_type="validation",
                message=f"Invalid category: {manifest.category}. Must be FeatureCategory enum."
            )

        return None

    def _load_legacy_feature(self, path: Path, result: DiscoveryResult) -> Optional[LoadedFeature]:
        """Attempt to load a feature using legacy service.py pattern.
        
        Args:
            path: Path to the feature directory
            result: DiscoveryResult to append warnings to
            
        Returns:
            LoadedFeature with default manifest if service.py exists, None otherwise.
            
        Requirements: 8.1, 8.2, 8.3, 8.4
        """
        service_path = path / "service.py"
        if not service_path.exists():
            return None
            
        result.warnings.append(
            f"Feature '{path.name}' uses legacy format. Consider adding manifest.py"
        )

        # Generate default manifest from folder name
        manifest = FeatureManifest(
            name=path.name,
            display_name=path.name.replace('_', ' ').title(),
            description=f"Legacy {path.name} feature",
            icon="📦",
            color="dim",
            category=FeatureCategory.UTILITY,
        )

        # Create a wrapper run function that delegates to service
        def legacy_run(ctx):
            return FeatureResult(
                success=False,
                message="Legacy feature - use service directly",
                error="No manifest.py run function"
            )

        return LoadedFeature(
            manifest=manifest,
            run=legacy_run,
            module_path=str(path)
        )

    def _resolve_dependencies(
        self,
        features: list[LoadedFeature],
        result: DiscoveryResult
    ) -> list[LoadedFeature]:
        """Sort features by dependencies using topological sort.
        
        Uses Kahn's algorithm to perform topological sorting.
        Detects and reports circular dependencies.
        
        Args:
            features: List of loaded features to sort
            result: DiscoveryResult to append errors to
            
        Returns:
            List of features sorted in dependency order.
            
        Requirements: 7.1, 7.2, 7.3, 7.4
        """
        # Build dependency graph
        by_name = {f.manifest.name: f for f in features}

        # Check for missing dependencies
        valid_features = []
        for feature in features:
            missing = [
                dep for dep in feature.manifest.dependencies
                if dep not in by_name
            ]
            if missing:
                result.errors.append(DiscoveryError(
                    feature_path=feature.module_path,
                    error_type="dependency",
                    message=f"Missing dependencies: {', '.join(missing)}"
                ))
            else:
                valid_features.append(feature)

        # If no features have dependencies, return as-is
        if not valid_features:
            return valid_features
            
        # Topological sort (Kahn's algorithm)
        in_degree = {f.manifest.name: 0 for f in valid_features}
        for feature in valid_features:
            for dep in feature.manifest.dependencies:
                if dep in in_degree:
                    in_degree[feature.manifest.name] += 1

        queue = [f for f in valid_features if in_degree[f.manifest.name] == 0]
        sorted_features = []

        while queue:
            feature = queue.pop(0)
            sorted_features.append(feature)

            for other in valid_features:
                if feature.manifest.name in other.manifest.dependencies:
                    in_degree[other.manifest.name] -= 1
                    if in_degree[other.manifest.name] == 0:
                        queue.append(other)

        # Check for circular dependencies
        if len(sorted_features) != len(valid_features):
            circular = [
                f.manifest.name for f in valid_features
                if f not in sorted_features
            ]
            result.errors.append(DiscoveryError(
                feature_path="",
                error_type="dependency",
                message=f"Circular dependency detected: {', '.join(circular)}"
            ))
            # Return only the non-circular features
            return sorted_features

        return sorted_features
