"""
Collaboration & Sharing - Export/import prompt libraries.
Feature #6: Collaboration & Sharing
"""

import json
import base64
import gzip
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
import hashlib


@dataclass
class SharedPrompt:
    id: str
    name: str
    technique: str
    prompt: str
    description: str = ""
    tags: list[str] = None
    author: str = ""
    created_at: str = ""
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.id:
            self.id = hashlib.md5(f"{self.name}{self.prompt}".encode()).hexdigest()[:12]


@dataclass
class PromptLibrary:
    name: str
    description: str
    version: str
    author: str
    prompts: list[SharedPrompt]
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class PromptSharing:
    """Handle prompt library export/import and sharing."""

    LIBRARY_PATH = Path.home() / ".promptbuilder" / "libraries"

    def __init__(self):
        self.LIBRARY_PATH.mkdir(parents=True, exist_ok=True)

    def create_library(
        self,
        name: str,
        description: str,
        prompts: list[SharedPrompt],
        author: str = "",
        version: str = "1.0.0"
    ) -> PromptLibrary:
        """Create a new prompt library."""
        return PromptLibrary(
            name=name,
            description=description,
            version=version,
            author=author,
            prompts=prompts
        )

    def export_library(self, library: PromptLibrary, path: str = None) -> str:
        """Export library to JSON file."""
        if path is None:
            path = self.LIBRARY_PATH / f"{library.name.lower().replace(' ', '_')}.json"
        
        data = {
            "name": library.name,
            "description": library.description,
            "version": library.version,
            "author": library.author,
            "created_at": library.created_at,
            "prompts": [asdict(p) for p in library.prompts]
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return str(path)

    def import_library(self, path: str) -> PromptLibrary:
        """Import library from JSON file."""
        with open(path) as f:
            data = json.load(f)
        
        prompts = [SharedPrompt(**p) for p in data.get("prompts", [])]
        
        return PromptLibrary(
            name=data.get("name", "Imported Library"),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            author=data.get("author", ""),
            prompts=prompts,
            created_at=data.get("created_at", "")
        )

    def generate_share_code(self, library: PromptLibrary) -> str:
        """Generate a shareable code string for a library."""
        data = {
            "name": library.name,
            "description": library.description,
            "version": library.version,
            "author": library.author,
            "prompts": [asdict(p) for p in library.prompts]
        }
        
        # Compress and encode
        json_str = json.dumps(data, separators=(',', ':'))
        compressed = gzip.compress(json_str.encode('utf-8'))
        encoded = base64.urlsafe_b64encode(compressed).decode('ascii')
        
        return f"pb://{encoded}"

    def import_from_share_code(self, code: str) -> PromptLibrary:
        """Import library from share code."""
        if not code.startswith("pb://"):
            raise ValueError("Invalid share code format")
        
        encoded = code[5:]  # Remove "pb://" prefix
        
        # Decode and decompress
        compressed = base64.urlsafe_b64decode(encoded)
        json_str = gzip.decompress(compressed).decode('utf-8')
        data = json.loads(json_str)
        
        prompts = [SharedPrompt(**p) for p in data.get("prompts", [])]
        
        return PromptLibrary(
            name=data.get("name", "Shared Library"),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            author=data.get("author", ""),
            prompts=prompts
        )

    def list_local_libraries(self) -> list[str]:
        """List all locally saved libraries."""
        return [f.stem for f in self.LIBRARY_PATH.glob("*.json")]

    def load_local_library(self, name: str) -> Optional[PromptLibrary]:
        """Load a library by name from local storage."""
        path = self.LIBRARY_PATH / f"{name}.json"
        if path.exists():
            return self.import_library(str(path))
        return None

    def delete_local_library(self, name: str) -> bool:
        """Delete a local library."""
        path = self.LIBRARY_PATH / f"{name}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def merge_libraries(
        self,
        libraries: list[PromptLibrary],
        name: str = "Merged Library"
    ) -> PromptLibrary:
        """Merge multiple libraries into one."""
        all_prompts = []
        seen_ids = set()
        
        for lib in libraries:
            for prompt in lib.prompts:
                if prompt.id not in seen_ids:
                    all_prompts.append(prompt)
                    seen_ids.add(prompt.id)
        
        return PromptLibrary(
            name=name,
            description=f"Merged from: {', '.join(lib.name for lib in libraries)}",
            version="1.0.0",
            author="",
            prompts=all_prompts
        )

    def export_single_prompt(self, prompt: SharedPrompt) -> str:
        """Generate a share code for a single prompt."""
        lib = PromptLibrary(
            name="Single Prompt",
            description="",
            version="1.0.0",
            author="",
            prompts=[prompt]
        )
        return self.generate_share_code(lib)

    def search_library(
        self,
        library: PromptLibrary,
        query: str,
        tags: list[str] = None
    ) -> list[SharedPrompt]:
        """Search prompts in a library."""
        results = []
        query_lower = query.lower()
        
        for prompt in library.prompts:
            # Check name and description
            if query_lower in prompt.name.lower() or query_lower in prompt.description.lower():
                results.append(prompt)
                continue
            
            # Check tags
            if tags:
                if any(t in prompt.tags for t in tags):
                    results.append(prompt)
                    continue
            
            # Check prompt content
            if query_lower in prompt.prompt.lower():
                results.append(prompt)
        
        return results
