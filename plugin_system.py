"""
Plugin System - Extensible architecture for community plugins.
Feature #10: Plugin System
"""

import importlib
import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional
from abc import ABC, abstractmethod
import json


@dataclass
class PluginMetadata:
    name: str
    version: str
    description: str
    author: str
    plugin_type: str  # "technique", "exporter", "processor", "integration"
    dependencies: list[str] = field(default_factory=list)
    config_schema: dict = field(default_factory=dict)


class PluginBase(ABC):
    """Base class for all plugins."""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass
    
    def initialize(self, config: dict = None):
        """Initialize the plugin with optional config."""
        pass
    
    def cleanup(self):
        """Cleanup when plugin is unloaded."""
        pass


class TechniquePlugin(PluginBase):
    """Plugin that adds a new prompt engineering technique."""
    
    @abstractmethod
    def build_prompt(self, task: str, context: str = "", **kwargs) -> str:
        """Build a prompt using this technique."""
        pass
    
    @property
    def technique_name(self) -> str:
        """Display name for the technique."""
        return self.metadata.name
    
    @property
    def technique_icon(self) -> str:
        """Icon for the technique."""
        return "🔌"
    
    @property
    def technique_color(self) -> str:
        """Color for the technique."""
        return "white"


class ExporterPlugin(PluginBase):
    """Plugin that adds a new export format."""
    
    @abstractmethod
    def export(self, prompt: str, metadata: dict = None) -> str:
        """Export prompt in this format."""
        pass
    
    @property
    def file_extension(self) -> str:
        """File extension for this format."""
        return ".txt"


class ProcessorPlugin(PluginBase):
    """Plugin that processes prompts or outputs."""
    
    @abstractmethod
    def process(self, content: str, **kwargs) -> str:
        """Process the content."""
        pass


class IntegrationPlugin(PluginBase):
    """Plugin that integrates with external services."""
    
    @abstractmethod
    async def execute(self, action: str, **kwargs) -> Any:
        """Execute an integration action."""
        pass
    
    @property
    def available_actions(self) -> list[str]:
        """List of available actions."""
        return []


class PluginManager:
    """Manage plugin discovery, loading, and execution."""

    PLUGIN_DIR = Path.home() / ".promptbuilder" / "plugins"

    def __init__(self):
        self.plugins: dict[str, PluginBase] = {}
        self.techniques: dict[str, TechniquePlugin] = {}
        self.exporters: dict[str, ExporterPlugin] = {}
        self.processors: dict[str, ProcessorPlugin] = {}
        self.integrations: dict[str, IntegrationPlugin] = {}
        
        self.PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
        self._load_builtin_plugins()

    def _load_builtin_plugins(self):
        """Load built-in example plugins."""
        # These would be actual plugin implementations
        pass

    def discover_plugins(self) -> list[str]:
        """Discover available plugins in the plugin directory."""
        plugins = []
        
        for path in self.PLUGIN_DIR.glob("*.py"):
            if not path.name.startswith("_"):
                plugins.append(path.stem)
        
        # Also check for plugin packages
        for path in self.PLUGIN_DIR.iterdir():
            if path.is_dir() and (path / "__init__.py").exists():
                plugins.append(path.name)
        
        return plugins

    def load_plugin(self, name: str, config: dict = None) -> bool:
        """Load a plugin by name."""
        try:
            # Try loading from plugin directory
            plugin_path = self.PLUGIN_DIR / f"{name}.py"
            
            if plugin_path.exists():
                spec = importlib.util.spec_from_file_location(name, plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                # Try loading as a package
                package_path = self.PLUGIN_DIR / name / "__init__.py"
                if package_path.exists():
                    spec = importlib.util.spec_from_file_location(name, package_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                else:
                    return False
            
            # Find plugin class
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, PluginBase) and 
                    attr is not PluginBase and
                    not attr.__name__.endswith("Plugin")):
                    plugin_class = attr
                    break
            
            if not plugin_class:
                return False
            
            # Instantiate and register
            plugin = plugin_class()
            plugin.initialize(config)
            
            self.plugins[name] = plugin
            
            # Register by type
            if isinstance(plugin, TechniquePlugin):
                self.techniques[name] = plugin
            elif isinstance(plugin, ExporterPlugin):
                self.exporters[name] = plugin
            elif isinstance(plugin, ProcessorPlugin):
                self.processors[name] = plugin
            elif isinstance(plugin, IntegrationPlugin):
                self.integrations[name] = plugin
            
            return True
            
        except Exception as e:
            print(f"Error loading plugin {name}: {e}")
            return False

    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin."""
        if name not in self.plugins:
            return False
        
        plugin = self.plugins[name]
        plugin.cleanup()
        
        del self.plugins[name]
        
        # Remove from type-specific registries
        self.techniques.pop(name, None)
        self.exporters.pop(name, None)
        self.processors.pop(name, None)
        self.integrations.pop(name, None)
        
        return True

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Get a loaded plugin by name."""
        return self.plugins.get(name)

    def list_loaded_plugins(self) -> list[PluginMetadata]:
        """List all loaded plugins."""
        return [p.metadata for p in self.plugins.values()]

    def get_technique_plugins(self) -> dict[str, TechniquePlugin]:
        """Get all loaded technique plugins."""
        return self.techniques.copy()

    def get_exporter_plugins(self) -> dict[str, ExporterPlugin]:
        """Get all loaded exporter plugins."""
        return self.exporters.copy()

    def create_plugin_template(self, name: str, plugin_type: str) -> str:
        """Create a template for a new plugin."""
        templates = {
            "technique": '''"""
{name} - Custom prompt engineering technique.
"""

from plugin_system import TechniquePlugin, PluginMetadata


class {class_name}(TechniquePlugin):
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="{name}",
            version="1.0.0",
            description="Description of your technique",
            author="Your Name",
            plugin_type="technique"
        )
    
    @property
    def technique_icon(self) -> str:
        return "🔌"
    
    @property
    def technique_color(self) -> str:
        return "cyan"
    
    def build_prompt(self, task: str, context: str = "", **kwargs) -> str:
        prompt = []
        if context:
            prompt.append(f"Context: {{context}}")
        prompt.append(f"Task: {{task}}")
        prompt.append("\\nYour custom technique instructions here...")
        return "\\n".join(prompt)
''',
            "exporter": '''"""
{name} - Custom export format.
"""

from plugin_system import ExporterPlugin, PluginMetadata


class {class_name}(ExporterPlugin):
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="{name}",
            version="1.0.0",
            description="Description of your export format",
            author="Your Name",
            plugin_type="exporter"
        )
    
    @property
    def file_extension(self) -> str:
        return ".custom"
    
    def export(self, prompt: str, metadata: dict = None) -> str:
        # Transform prompt to your format
        return prompt
''',
            "processor": '''"""
{name} - Custom prompt/output processor.
"""

from plugin_system import ProcessorPlugin, PluginMetadata


class {class_name}(ProcessorPlugin):
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="{name}",
            version="1.0.0",
            description="Description of your processor",
            author="Your Name",
            plugin_type="processor"
        )
    
    def process(self, content: str, **kwargs) -> str:
        # Process and return modified content
        return content
'''
        }
        
        template = templates.get(plugin_type, templates["technique"])
        class_name = "".join(word.capitalize() for word in name.split("_"))
        
        return template.format(name=name, class_name=class_name)

    def save_plugin_template(self, name: str, plugin_type: str) -> str:
        """Create and save a plugin template file."""
        content = self.create_plugin_template(name, plugin_type)
        path = self.PLUGIN_DIR / f"{name}.py"
        
        with open(path, 'w') as f:
            f.write(content)
        
        return str(path)
