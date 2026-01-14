"""Feature Contract types for the contrib discovery system.

This module defines the types and protocols that all contrib features must follow.
It lives in workbench to prevent modification by feature developers.

Requirements: 1.1, 1.2, 1.3, 1.5, 9.1
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Awaitable, Any, Optional, Union

from rich.console import Console


class FeatureCategory(Enum):
    """Standard categories for organizing features in the CLI menu.
    
    Requirements: 9.1
    """
    CORE = "core"           # Core prompt building features
    AI = "ai"               # AI-powered features (require API key)
    STORAGE = "storage"     # History, favorites, persistence
    EXPORT = "export"       # Export and sharing features
    UTILITY = "utility"     # Miscellaneous utilities


@dataclass
class FeatureManifest:
    """Metadata describing a contrib feature.
    
    Requirements: 1.1, 1.2
    
    Required fields:
        name: Unique identifier (e.g., "optimizer")
        display_name: Human-readable name (e.g., "Prompt Optimizer")
        description: Short description for menu
        icon: Emoji icon (e.g., "🔧")
        color: Rich color name (e.g., "cyan")
        category: Menu category from FeatureCategory enum
    
    Optional fields:
        version: Semantic version (default: "1.0.0")
        requires_api_key: Whether feature needs LLM API (default: False)
        dependencies: List of other feature names this depends on
        enabled: Whether feature is enabled (default: True)
        menu_key: Keyboard shortcut (e.g., "o")
    """
    # Required fields
    name: str
    display_name: str
    description: str
    icon: str
    color: str
    category: FeatureCategory

    # Optional fields with defaults
    version: str = "1.0.0"
    requires_api_key: bool = False
    dependencies: list[str] = field(default_factory=list)
    enabled: bool = True
    menu_key: Optional[str] = None


@dataclass
class FeatureContext:
    """Runtime context passed to feature run functions.
    
    Requirements: 6.2
    """
    console: Console                    # Rich console for output
    llm_client: Any                     # LLMClient instance (if available)
    history: Any                        # HistoryService instance
    config: Any                         # APIConfig instance
    analytics: Any                      # PromptAnalytics instance
    prompt_builder: Any                 # Core PromptBuilder instance


@dataclass
class FeatureResult:
    """Result returned from feature execution.
    
    Requirements: 1.3
    """
    success: bool
    message: str = ""
    data: Any = None
    error: Optional[str] = None


# Type alias for the run function signature
# Supports both sync and async run functions (Requirement 1.5)
FeatureRunner = Callable[[FeatureContext], Union[FeatureResult, Awaitable[FeatureResult]]]
