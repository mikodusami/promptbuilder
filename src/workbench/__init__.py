"""Contrib discovery and registration infrastructure.

This module provides the contracts, discovery engine, registry, and CLI
integration for the dynamic contrib feature system.

Public Exports:
    - FeatureCategory: Enum of standard feature categories
    - FeatureManifest: Dataclass for feature metadata
    - FeatureContext: Runtime context passed to features
    - FeatureResult: Result returned from feature execution
    - FeatureRunner: Type alias for run function signature
    - get_registry: Get the global feature registry
    - reset_registry: Reset the global registry (for testing)
    - FeatureRegistry: The registry class itself
    - CLIIntegration: Bridge between registry and CLI menu
"""

from src.workbench.contract import (
    FeatureCategory,
    FeatureManifest,
    FeatureContext,
    FeatureResult,
    FeatureRunner,
)

from src.workbench.registry import (
    FeatureRegistry,
    get_registry,
    reset_registry,
)

from src.workbench.integration import CLIIntegration

__all__ = [
    # Contract types
    "FeatureCategory",
    "FeatureManifest",
    "FeatureContext",
    "FeatureResult",
    "FeatureRunner",
    # Registry
    "FeatureRegistry",
    "get_registry",
    "reset_registry",
    # CLI Integration
    "CLIIntegration",
]
