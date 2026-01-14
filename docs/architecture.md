# Architecture Documentation

## Overview

Prompt Builder is a command-line tool for creating exceptional prompts using modern prompt engineering techniques. The codebase follows a VS Code-inspired plugin architecture with clear separation between workbench infrastructure and feature contributions.

## Project Structure

```
prompt-builder/
├── main.py                    # CLI entry point and interactive interface
├── src/                       # Source code root
│   ├── core/                  # Core prompt building logic
│   ├── platform/              # Platform abstractions (OS, clipboard, storage)
│   ├── services/              # Shared services (tokens, export, LLM)
│   └── workbench/             # Plugin infrastructure and feature discovery
│       ├── contract.py        # Feature contracts and protocols
│       ├── discovery.py       # Dynamic feature discovery engine
│       ├── registry.py        # Feature registry with query methods
│       ├── integration.py     # CLI integration for feature execution
│       └── contrib/           # Feature contributions (modular features)
├── tests/                     # Test suite
├── docs/                      # Documentation
└── files/                     # Example files and outputs
```

## Architecture Layers

### 1. Core Layer (`src/core/`)

The foundation of the prompt building system. Contains the essential business logic for creating prompts using various techniques.

**Files:**

- `types.py` - Core type definitions and enums (PromptType, etc.)
- `config.py` - Configuration classes for prompt building
- `builder.py` - Main PromptBuilder class that orchestrates prompt generation
- `__init__.py` - Public API exports

**Responsibilities:**

- Define prompt engineering techniques (Chain of Thought, Few-Shot, Role-Based, etc.)
- Implement prompt generation algorithms
- Provide the core API for building prompts

**Dependencies:** None (self-contained)

### 2. Platform Layer (`src/platform/`)

Abstracts platform-specific functionality to ensure cross-platform compatibility.

**Files:**

- `clipboard.py` - Clipboard operations (copy/paste)
- `environment.py` - Environment variable handling
- `storage.py` - File system and data persistence abstractions

**Responsibilities:**

- Handle OS-specific operations
- Provide unified interfaces for platform features
- Manage file I/O and storage paths

**Dependencies:** Standard library only

### 3. Services Layer (`src/services/`)

Shared services that provide functionality across multiple features.

**Files:**

- `token_counter.py` - Token counting and cost estimation for LLM models
- `export.py` - Export prompts to various formats (JSON, Markdown, LangChain, etc.)
- `context.py` - Context window management for LLMs
- `llm/` - LLM provider integration
  - `config.py` - API key and provider configuration
  - `client.py` - Unified client for OpenAI, Anthropic, Google

**Responsibilities:**

- Token counting and cost calculation
- Format conversion and export
- LLM API communication
- Context management

**Dependencies:** Core layer, external libraries (tiktoken, openai, anthropic, google-genai)

### 4. Workbench Layer (`src/workbench/`)

The plugin infrastructure inspired by VS Code's architecture. Provides dynamic feature discovery, registration, and execution.

**Files:**

- `contract.py` - Feature contracts, protocols, and type definitions
- `discovery.py` - Discovery engine that scans for feature manifests
- `registry.py` - Feature registry with query methods (by name, category, etc.)
- `integration.py` - CLI integration for menu rendering and feature execution
- `__init__.py` - Public API exports

**Key Components:**

#### Feature Contract (`contract.py`)

Defines the interface all features must implement:

```python
@dataclass
class FeatureManifest:
    name: str                    # Unique identifier
    display_name: str            # Human-readable name
    description: str             # Short description
    category: FeatureCategory    # AI, UTILITY, STORAGE
    icon: str                    # Emoji icon
    requires_api_key: bool       # Whether LLM access is needed
    dependencies: list[str]      # Other features this depends on
    enabled: bool                # Whether feature is active
    menu_key: Optional[str]      # Keyboard shortcut
```

#### Discovery Engine (`discovery.py`)

Automatically discovers features by scanning for `manifest.py` files:

```python
engine = DiscoveryEngine()
result = engine.discover()  # Returns DiscoveryResult with features, errors, warnings
```

Features:

- Scans `src/workbench/contrib/*/manifest.py`
- Validates manifests against contracts
- Resolves dependencies with topological sort
- Detects circular dependencies
- Collects errors and warnings without crashing

#### Feature Registry (`registry.py`)

Provides query methods for accessing discovered features:

```python
registry = get_registry()
feature = registry.get("optimizer")           # Get by name
ai_features = registry.list_by_category(FeatureCategory.AI)
api_features = registry.list_requiring_api()
all_features = registry.list_all()
```

#### CLI Integration (`integration.py`)

Bridges features with the CLI interface:

```python
cli = CLIIntegration(console, llm_client, history, config, analytics, builder, registry)
cli.render_feature_menu(title="AI Features", category=FeatureCategory.AI)
result = cli.execute_feature_sync(feature)
```

### 5. Contrib Layer (`src/workbench/contrib/`)

Modular feature contributions. Each feature is self-contained with a standardized manifest.

**Structure Pattern:**

```
contrib/<feature>/
├── __init__.py      # Public exports
├── common.py        # Types, dataclasses, constants
├── service.py       # Business logic and implementation
└── manifest.py      # Feature manifest and run() function
```

**Manifest Pattern:**

```python
# manifest.py
from src.workbench.contract import FeatureManifest, FeatureCategory, FeatureContext, FeatureResult

MANIFEST = FeatureManifest(
    name="optimizer",
    display_name="Optimize Prompt",
    description="AI-powered prompt improvement",
    category=FeatureCategory.AI,
    icon="✨",
    requires_api_key=True,
    dependencies=[],
    enabled=True,
    menu_key="o",
)

def run(ctx: FeatureContext) -> FeatureResult:
    """Entry point called by CLIIntegration."""
    # Lazy imports to avoid circular dependencies
    from .service import OptimizerService
    # ... implementation
    return FeatureResult(success=True, data=result)
```

**Current Features (8 total):**

| Feature     | Category | Description                         | Requires API |
| ----------- | -------- | ----------------------------------- | ------------ |
| `history`   | STORAGE  | Browse and manage saved prompts     | No           |
| `templates` | UTILITY  | Custom YAML template system         | No           |
| `variables` | UTILITY  | Variable interpolation in prompts   | No           |
| `analytics` | UTILITY  | Usage statistics and cost tracking  | No           |
| `optimizer` | AI       | AI-powered prompt improvement       | Yes          |
| `nlgen`     | AI       | Generate prompts from descriptions  | Yes          |
| `testing`   | AI       | Test prompts across multiple models | Yes          |
| `chains`    | AI       | Multi-step prompt workflows         | Yes          |

**Design Principles:**

- Each feature is independently testable
- Minimal coupling between features
- Lazy imports inside `run()` to avoid circular dependencies
- Clear service boundaries
- Shared types in `common.py`, logic in `service.py`

### 6. Tests Layer (`tests/`)

Comprehensive test coverage including property-based tests.

```
tests/
├── test_core/              # Core layer tests
│   └── test_builder.py
├── test_services/          # Services layer tests
│   ├── test_export.py
│   └── test_token_counter.py
└── test_workbench/         # Workbench layer tests
    ├── test_contract.py         # Contract property tests
    ├── test_discovery.py        # Discovery engine tests
    ├── test_registry.py         # Registry query tests
    ├── test_integration.py      # CLI integration tests
    ├── test_manifest_contract.py # Manifest validation tests
    ├── test_error_collection.py # Error handling tests
    └── test_full_discovery_flow.py # End-to-end flow tests
```

**Testing Strategy:**

- Property-based tests (Hypothesis) for contracts and discovery
- Unit tests for core logic
- Integration tests for full discovery flow
- 115 tests total with comprehensive coverage

## Data Flow

### Feature Discovery Flow

```
Application Startup
    ↓
DiscoveryEngine.discover()
    ↓
Scan contrib/*/manifest.py
    ↓
Validate manifests against contracts
    ↓
Resolve dependencies (topological sort)
    ↓
Register in FeatureRegistry
    ↓
CLIIntegration ready for use
```

### Feature Execution Flow

```
User selects feature (main.py)
    ↓
CLIIntegration.execute_feature_sync(feature)
    ↓
Build FeatureContext (console, llm_client, history, etc.)
    ↓
Call feature's run(ctx) function
    ↓
Feature executes with lazy-loaded services
    ↓
Return FeatureResult
    ↓
Display result to user
```

### Prompt Creation Flow

```
User Input (main.py)
    ↓
Core Builder (src/core/builder.py)
    ↓
Prompt Generation
    ↓
Services (token counting, export)
    ↓
History Service (auto-save)
    ↓
Output (clipboard, file, display)
```

## Key Design Patterns

### 1. Plugin Architecture (VS Code-inspired)

Features are discovered dynamically via manifests, allowing:

- Independent feature development
- Easy addition/removal of features
- Clear contracts between infrastructure and features

### 2. Dependency Injection

Services and context passed to features:

```python
ctx = FeatureContext(
    console=console,
    llm_client=llm_client,
    history=history,
    # ...
)
result = feature.run(ctx)
```

### 3. Lazy Loading

Features use lazy imports to avoid loading all dependencies at startup:

```python
def run(ctx: FeatureContext) -> FeatureResult:
    from .service import MyService  # Loaded only when feature runs
    # ...
```

### 4. Error Collection

Discovery collects errors without crashing:

```python
result = engine.discover()
if result.errors:
    for error in result.errors:
        print(f"Error in {error.feature}: {error.message}")
# Application continues with valid features
```

### 5. Type Safety

Strong typing throughout with:

- Dataclasses for structured data (`FeatureManifest`, `FeatureResult`)
- Enums for categories (`FeatureCategory`)
- Type hints for all public APIs
- Protocol classes for contracts

## Extension Points

### Adding a New Feature

1. Create `src/workbench/contrib/<feature>/` directory
2. Add `common.py` with types and dataclasses
3. Add `service.py` with business logic
4. Add `manifest.py` with `MANIFEST` constant and `run()` function
5. Feature is automatically discovered on next startup

### Adding a New Prompt Technique

1. Add enum to `src/core/types.py`
2. Implement builder method in `src/core/builder.py`
3. Add UI option in `main.py`

### Adding a New Export Format

1. Add format handler in `src/services/export.py`
2. Register in `FORMAT_INFO` dictionary
3. Update UI in `main.py`

## Configuration Management

### Environment Variables

- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `GOOGLE_API_KEY` - Google AI API key

### Configuration Files

- `.env` - Environment variables (not committed)
- `~/.promptbuilder/templates.yaml` - Custom templates
- `~/.promptbuilder/prompts.db` - SQLite history database
- `~/.promptbuilder/analytics.db` - SQLite analytics database

## Dependencies

### Core Dependencies (Required)

- `rich` - Terminal UI and formatting
- `pyyaml` - Template parsing
- `python-dotenv` - Environment variable loading
- `simple-term-menu` - Interactive arrow-key menus
- `tiktoken` - Token counting

### Optional Dependencies

- `pyperclip` - Clipboard support
- `openai` - OpenAI API client
- `anthropic` - Anthropic API client
- `google-genai` - Google AI client

### Development Dependencies

- `pytest` - Testing framework
- `hypothesis` - Property-based testing

## Performance Considerations

- **Lazy Loading**: Features only loaded when executed
- **Discovery Caching**: Registry loaded once at startup
- **Token Caching**: Token counts cached per model
- **Database Indexing**: History/analytics use indexed queries
- **Discovery Performance**: <500ms for 20+ features

## Security Considerations

- API keys stored in environment variables or `.env` (gitignored)
- No sensitive data in prompt history by default
- User confirmation for destructive operations
- Input sanitization for file operations
- Dynamic code loading limited to trusted `contrib/` directory

## Conclusion

The Prompt Builder architecture prioritizes:

- **Modularity**: Clear separation via workbench/contrib pattern
- **Extensibility**: Plugin architecture for easy feature addition
- **Testability**: 115 tests with property-based testing
- **Maintainability**: Consistent patterns and contracts
- **User Experience**: Rich CLI with interactive menus
