"""Feature Registry for the contrib discovery system.

This module provides the central registry for all discovered contrib features.
It stores features indexed by name and provides query methods for filtering.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
"""

from typing import Optional
import logging

from .contract import FeatureCategory
from .discovery import LoadedFeature, DiscoveryEngine, DiscoveryResult


logger = logging.getLogger(__name__)


class FeatureRegistry:
    """Central registry for all discovered contrib features.
    
    The registry stores features indexed by unique name and provides
    methods to query features by category, API key requirement, etc.
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """

    def __init__(self):
        """Initialize an empty registry."""
        self._features: dict[str, LoadedFeature] = {}
        self._by_category: dict[FeatureCategory, list[LoadedFeature]] = {
            cat: [] for cat in FeatureCategory
        }
        self._discovery_result: Optional[DiscoveryResult] = None

    def load(self, engine: Optional[DiscoveryEngine] = None) -> DiscoveryResult:
        """Discover and load all features.
        
        Args:
            engine: Optional DiscoveryEngine instance. If not provided,
                   a default engine will be created.
        
        Returns:
            DiscoveryResult containing loaded features, errors, and warnings.
            
        Requirements: 4.1
        """
        engine = engine or DiscoveryEngine()
        result = engine.discover()
        self._discovery_result = result

        # Register valid features
        for feature in result.features:
            self._register(feature)

        # Log summary
        logger.info(
            f"Loaded {len(result.features)} features, "
            f"{len(result.errors)} errors, "
            f"{len(result.warnings)} warnings"
        )

        return result


    def _register(self, feature: LoadedFeature) -> bool:
        """Register a single feature.
        
        Args:
            feature: The loaded feature to register.
            
        Returns:
            True if registration succeeded, False if duplicate name.
            
        Requirements: 4.5
        """
        name = feature.manifest.name

        if name in self._features:
            logger.warning(f"Duplicate feature name: {name}. Keeping first.")
            return False

        self._features[name] = feature
        self._by_category[feature.manifest.category].append(feature)
        return True

    def get(self, name: str) -> Optional[LoadedFeature]:
        """Get a feature by name.
        
        Args:
            name: The unique feature name to look up.
            
        Returns:
            The LoadedFeature if found, None otherwise.
            
        Requirements: 4.4
        """
        return self._features.get(name)

    def list_all(self) -> list[LoadedFeature]:
        """List all registered features.
        
        Returns:
            List of all registered features.
            
        Requirements: 4.1
        """
        return list(self._features.values())

    def list_by_category(self, category: FeatureCategory) -> list[LoadedFeature]:
        """List features in a specific category.
        
        Args:
            category: The FeatureCategory to filter by.
            
        Returns:
            List of features in the specified category.
            
        Requirements: 4.2
        """
        return self._by_category.get(category, [])

    def list_enabled(self) -> list[LoadedFeature]:
        """List only enabled features.
        
        Returns:
            List of features where manifest.enabled is True.
        """
        return [f for f in self._features.values() if f.manifest.enabled]

    def list_requiring_api(self) -> list[LoadedFeature]:
        """List features that require an API key.
        
        Returns:
            List of features where manifest.requires_api_key is True.
            
        Requirements: 4.3
        """
        return [f for f in self._features.values() if f.manifest.requires_api_key]

    def get_categories_with_features(self) -> list[tuple[FeatureCategory, list[LoadedFeature]]]:
        """Get categories that have at least one feature, in display order.
        
        Returns:
            List of (category, features) tuples for non-empty categories,
            ordered by standard display order.
        """
        order = [
            FeatureCategory.CORE,
            FeatureCategory.AI,
            FeatureCategory.STORAGE,
            FeatureCategory.EXPORT,
            FeatureCategory.UTILITY,
        ]
        return [
            (cat, self._by_category[cat])
            for cat in order
            if self._by_category[cat]
        ]

    def has_errors(self) -> bool:
        """Check if discovery had any errors.
        
        Returns:
            True if there were discovery errors, False otherwise.
        """
        return bool(self._discovery_result and self._discovery_result.errors)

    def get_errors(self) -> list:
        """Get discovery errors.
        
        Returns:
            List of DiscoveryError objects from the last discovery.
        """
        return self._discovery_result.errors if self._discovery_result else []

    def get_warnings(self) -> list[str]:
        """Get discovery warnings.
        
        Returns:
            List of warning messages from the last discovery.
        """
        return self._discovery_result.warnings if self._discovery_result else []


# Global registry instance
_registry: Optional[FeatureRegistry] = None


def get_registry() -> FeatureRegistry:
    """Get or create the global feature registry.
    
    This function provides singleton access to the feature registry.
    On first access, it creates the registry and triggers discovery.
    
    Returns:
        The global FeatureRegistry instance.
        
    Requirements: 4.1
    """
    global _registry
    if _registry is None:
        _registry = FeatureRegistry()
        _registry.load()
    return _registry


def reset_registry() -> None:
    """Reset the global registry (primarily for testing).
    
    This clears the global registry instance, allowing a fresh
    registry to be created on the next get_registry() call.
    """
    global _registry
    _registry = None
