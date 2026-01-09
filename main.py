#!/usr/bin/env python3
"""
Prompt Builder - Create exceptional prompts using modern prompt engineering techniques.

Techniques included:
- Chain of Thought (CoT)
- Few-Shot Learning
- Role-Based Prompting
- Structured Output
- Self-Consistency
- Tree of Thoughts
- ReAct (Reasoning + Acting)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.syntax import Syntax
    from rich.text import Text
    from rich.markdown import Markdown
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from prompt_history import PromptHistory, SavedPrompt
from template_manager import TemplateManager, CustomTemplate, YAML_AVAILABLE
from clipboard_utils import copy_to_clipboard, is_clipboard_available
from token_counter import TokenCounter, is_tiktoken_available
from export_formats import PromptExporter, PromptMetadata, EXPORT_FORMATS, export_prompt
from api_config import APIConfig
from llm_client import LLMClient
from prompt_optimizer import PromptOptimizer
from prompt_testing import PromptTestSuite, TestCase
from prompt_chains import ChainExecutor, ChainStep, PromptChain, BUILTIN_CHAINS
from prompt_sharing import PromptSharing, SharedPrompt
from context_manager import ContextManager
from analytics import PromptAnalytics
from natural_language_gen import NaturalLanguageGenerator

console = Console() if RICH_AVAILABLE else None


class PromptType(Enum):
    CHAIN_OF_THOUGHT = "cot"
    FEW_SHOT = "few_shot"
    ROLE_BASED = "role"
    STRUCTURED = "structured"
    REACT = "react"
    TREE_OF_THOUGHTS = "tot"
    SELF_CONSISTENCY = "self_consistency"


@dataclass
class PromptConfig:
    task: str
    context: str = ""
    examples: list[dict] = field(default_factory=list)
    role: str = ""
    output_format: str = ""
    constraints: list[str] = field(default_factory=list)
    temperature_hint: str = "balanced"


class PromptBuilder:
    """Build prompts using various prompt engineering techniques."""

    def __init__(self):
        self.templates = {
            PromptType.CHAIN_OF_THOUGHT: self._build_cot,
            PromptType.FEW_SHOT: self._build_few_shot,
            PromptType.ROLE_BASED: self._build_role_based,
            PromptType.STRUCTURED: self._build_structured,
            PromptType.REACT: self._build_react,
            PromptType.TREE_OF_THOUGHTS: self._build_tot,
            PromptType.SELF_CONSISTENCY: self._build_self_consistency,
        }

    def build(self, prompt_type: PromptType, config: PromptConfig) -> str:
        """Build a prompt using the specified technique."""
        builder = self.templates.get(prompt_type)
        if not builder:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
        return builder(config)

    def _build_cot(self, config: PromptConfig) -> str:
        """Chain of Thought - encourages step-by-step reasoning."""
        prompt = []
        if config.context:
            prompt.append(f"Context: {config.context}\n")
        prompt.append(f"Task: {config.task}\n")
        prompt.append("Think through this step-by-step:")
        prompt.append("1. First, identify the key elements of the problem")
        prompt.append("2. Break down the problem into smaller parts")
        prompt.append("3. Solve each part systematically")
        prompt.append("4. Combine the solutions and verify the result")
        prompt.append("\nLet's work through this carefully:")
        if config.constraints:
            prompt.append("\nConstraints to consider:")
            for c in config.constraints:
                prompt.append(f"- {c}")
        return "\n".join(prompt)

    def _build_few_shot(self, config: PromptConfig) -> str:
        """Few-Shot Learning - provides examples to guide the model."""
        prompt = []
        if config.context:
            prompt.append(f"Context: {config.context}\n")
        prompt.append(f"Task: {config.task}\n")
        if config.examples:
            prompt.append("Here are some examples:\n")
            for i, ex in enumerate(config.examples, 1):
                prompt.append(f"Example {i}:")
                prompt.append(f"Input: {ex.get('input', '')}")
                prompt.append(f"Output: {ex.get('output', '')}\n")
        prompt.append("Now, apply the same pattern to solve the following:")
        return "\n".join(prompt)

    def _build_role_based(self, config: PromptConfig) -> str:
        """Role-Based - assigns a specific persona to the model."""
        prompt = []
        role = config.role or "expert assistant"
        prompt.append(f"You are a {role}.\n")
        if config.context:
            prompt.append(f"Background: {config.context}\n")
        prompt.append(f"Your task: {config.task}\n")
        prompt.append("Approach this with your expertise, providing:")
        prompt.append("- Professional insights")
        prompt.append("- Practical recommendations")
        prompt.append("- Clear explanations")
        if config.constraints:
            prompt.append("\nKeep in mind:")
            for c in config.constraints:
                prompt.append(f"- {c}")
        return "\n".join(prompt)

    def _build_structured(self, config: PromptConfig) -> str:
        """Structured Output - requests specific format."""
        prompt = []
        if config.context:
            prompt.append(f"Context: {config.context}\n")
        prompt.append(f"Task: {config.task}\n")
        output_format = config.output_format or "JSON"
        prompt.append(f"Provide your response in {output_format} format.\n")
        prompt.append("Structure your response with:")
        prompt.append("- Clear sections/fields")
        prompt.append("- Consistent formatting")
        prompt.append("- Complete information")
        if config.constraints:
            prompt.append("\nRequirements:")
            for c in config.constraints:
                prompt.append(f"- {c}")
        return "\n".join(prompt)

    def _build_react(self, config: PromptConfig) -> str:
        """ReAct - combines reasoning and acting."""
        prompt = []
        if config.context:
            prompt.append(f"Context: {config.context}\n")
        prompt.append(f"Task: {config.task}\n")
        prompt.append("Use the ReAct framework to solve this:\n")
        prompt.append("For each step, follow this pattern:")
        prompt.append("Thought: [Your reasoning about what to do next]")
        prompt.append("Action: [The action you decide to take]")
        prompt.append("Observation: [What you observe from the action]")
        prompt.append("... (repeat until solved)")
        prompt.append("Final Answer: [Your conclusion]\n")
        prompt.append("Begin your analysis:")
        return "\n".join(prompt)

    def _build_tot(self, config: PromptConfig) -> str:
        """Tree of Thoughts - explores multiple reasoning paths."""
        prompt = []
        if config.context:
            prompt.append(f"Context: {config.context}\n")
        prompt.append(f"Task: {config.task}\n")
        prompt.append("Explore this problem using Tree of Thoughts:\n")
        prompt.append("1. Generate 3 different initial approaches")
        prompt.append("2. For each approach, evaluate:")
        prompt.append("   - Feasibility (1-10)")
        prompt.append("   - Potential issues")
        prompt.append("   - Expected outcome")
        prompt.append("3. Select the most promising path")
        prompt.append("4. Develop it further, backtracking if needed")
        prompt.append("5. Present your final solution with reasoning\n")
        prompt.append("Start by listing your three approaches:")
        return "\n".join(prompt)

    def _build_self_consistency(self, config: PromptConfig) -> str:
        """Self-Consistency - generates multiple solutions and finds consensus."""
        prompt = []
        if config.context:
            prompt.append(f"Context: {config.context}\n")
        prompt.append(f"Task: {config.task}\n")
        prompt.append("Apply self-consistency checking:\n")
        prompt.append("1. Solve this problem 3 different ways")
        prompt.append("2. For each solution, show your work")
        prompt.append("3. Compare all solutions")
        prompt.append("4. Identify the most consistent/reliable answer")
        prompt.append("5. Explain why this answer is most trustworthy\n")
        prompt.append("Solution 1:")
        return "\n".join(prompt)


class InteractivePromptBuilder:
    """Interactive CLI for building prompts with rich formatting."""

    TECHNIQUES = [
        (PromptType.CHAIN_OF_THOUGHT, "Chain of Thought", "🧠", "cyan", 
         "Step-by-step reasoning for complex problems"),
        (PromptType.FEW_SHOT, "Few-Shot Learning", "📚", "green",
         "Learn patterns from examples you provide"),
        (PromptType.ROLE_BASED, "Role-Based", "🎭", "magenta",
         "Assign expert persona for domain-specific tasks"),
        (PromptType.STRUCTURED, "Structured Output", "📋", "yellow",
         "Get responses in specific formats (JSON, etc.)"),
        (PromptType.REACT, "ReAct", "⚡", "red",
         "Reasoning + Acting for multi-step problem solving"),
        (PromptType.TREE_OF_THOUGHTS, "Tree of Thoughts", "🌳", "blue",
         "Explore multiple solution paths systematically"),
        (PromptType.SELF_CONSISTENCY, "Self-Consistency", "🔄", "white",
         "Multiple solutions for verification & consensus"),
    ]

    def __init__(self):
        self.builder = PromptBuilder()
        self.history = PromptHistory()
        self.template_manager = TemplateManager()
        self.token_counter = TokenCounter()
        self.preview_mode = False
        
        # Advanced features
        self.api_config = APIConfig()
        self.llm_client = LLMClient(self.api_config)
        self.optimizer = PromptOptimizer(self.llm_client)
        self.test_suite = PromptTestSuite(self.llm_client)
        self.chain_executor = ChainExecutor(self.llm_client)
        self.sharing = PromptSharing()
        self.context_manager = ContextManager()
        self.analytics = PromptAnalytics()
        self.nl_generator = NaturalLanguageGenerator(self.llm_client)
        
        if not RICH_AVAILABLE:
            print("[yellow]Install 'rich' for the best experience: pip install rich[/]")

    def run(self):
        """Run the interactive prompt builder."""
        self._show_header()

        while True:
            action = self._show_main_menu()
            
            if action == "quit":
                self._show_goodbye()
                break
            elif action == "new":
                self._create_new_prompt()
            elif action == "combine":
                self._combine_techniques()
            elif action == "templates":
                self._use_custom_template()
            elif action == "history":
                self._browse_history()
            elif action == "favorites":
                self._browse_favorites()
            elif action == "search":
                self._search_prompts()
            elif action == "preview":
                self._toggle_preview_mode()
            elif action == "ai":
                self._ai_features_menu()
            elif action == "settings":
                self._settings_menu()

    def _use_custom_template(self):
        """Use a custom template to create a prompt."""
        templates = self.template_manager.list_templates()
        
        if not templates:
            if RICH_AVAILABLE:
                console.print(f"[dim]No custom templates found. Add templates to:[/]")
                console.print(f"[cyan]{self.template_manager.get_config_path()}[/]\n")
            else:
                print(f"No custom templates. Add them to: {self.template_manager.get_config_path()}\n")
            return
        
        # Display templates
        if RICH_AVAILABLE:
            console.print("[bold bright_white]Custom Templates:[/]\n")
            table = Table(box=box.ROUNDED, border_style="dim", show_header=False, padding=(0, 2))
            table.add_column("Key", style="bold bright_white", width=5)
            table.add_column("Template", width=22)
            table.add_column("Description", style="dim")
            
            template_keys = list(self.template_manager.templates.keys())
            for i, key in enumerate(template_keys, 1):
                t = self.template_manager.templates[key]
                table.add_row(f"[{t.color}]{i}[/]", f"{t.icon} [{t.color}]{t.name}[/]", t.description)
            table.add_row("[red]b[/]", "🔙 [red]Back[/]", "Return to main menu")
            console.print(table)
            console.print()
            choice = Prompt.ask("[bold]Select template[/]", default="b")
        else:
            print("\nCustom Templates:\n")
            template_keys = list(self.template_manager.templates.keys())
            for i, key in enumerate(template_keys, 1):
                t = self.template_manager.templates[key]
                print(f"  [{i}] {t.icon} {t.name:<20} - {t.description}")
            print("  [b] 🔙 Back")
            choice = input("\nSelect template: ").strip()
        
        if choice.lower() == 'b':
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(template_keys):
                key = template_keys[idx]
                self._fill_template(key)
        except ValueError:
            pass

    def _fill_template(self, template_key: str):
        """Fill in a template's variables and generate prompt."""
        template = self.template_manager.get_template(template_key)
        if not template:
            return
        
        if RICH_AVAILABLE:
            console.print(Panel(
                f"[bold]{template.name}[/]\n[dim]{template.description}[/]",
                border_style=template.color,
                box=box.ROUNDED
            ))
        
        # Gather variables
        variables = {}
        for var in template.variables:
            if RICH_AVAILABLE:
                value = Prompt.ask(f"[bold {template.color}]{var}[/]")
            else:
                value = input(f"{var}: ").strip()
            variables[var] = value
        
        # Build prompt
        result = self.template_manager.build_prompt(template_key, variables)
        
        self._display_result(result, template.color)
        
        # Save to history
        tags = self._ask_tags()
        prompt_id = self.history.save(
            technique=f"template:{template_key}",
            task=variables.get('task', template.name),
            prompt=result,
            tags=tags
        )
        
        if RICH_AVAILABLE:
            console.print(f"[dim]💾 Auto-saved to history (ID: {prompt_id})[/]")
        
        self._prompt_actions(prompt_id, result, template.color)

    def _show_main_menu(self) -> str:
        """Show main menu and return selected action."""
        has_ai = self.api_config.has_any_provider()
        ai_status = "[green]●[/]" if has_ai else "[red]○[/]"
        
        if RICH_AVAILABLE:
            console.print("[bold bright_white]Main Menu:[/]\n")
            table = Table(box=box.ROUNDED, border_style="dim", show_header=False, padding=(0, 2))
            table.add_column("Key", style="bold bright_white", width=5)
            table.add_column("Action", width=22)
            table.add_column("Description", style="dim")
            table.add_row("[cyan]n[/]", "✨ [cyan]New Prompt[/]", "Create a new prompt")
            table.add_row("[bright_cyan]m[/]", "🔗 [bright_cyan]Combine[/]", "Chain multiple techniques")
            table.add_row("[blue]t[/]", "📦 [blue]Templates[/]", "Use custom templates")
            table.add_row("[green]h[/]", "📜 [green]History[/]", "Browse recent prompts")
            table.add_row("[yellow]f[/]", "⭐ [yellow]Favorites[/]", "View favorite prompts")
            table.add_row("[magenta]s[/]", "🔍 [magenta]Search[/]", "Search saved prompts")
            table.add_row("[white]p[/]", "👁️  [white]Preview Mode[/]", f"{'ON' if self.preview_mode else 'OFF'} - Live prompt preview")
            table.add_row(f"[bright_magenta]a[/]", f"🤖 [bright_magenta]AI Features[/] {ai_status}", "Optimize, generate, test, chains")
            table.add_row("[dim]c[/]", "⚙️  [dim]Settings[/]", "API keys & configuration")
            table.add_row("[red]q[/]", "🚪 [red]Quit[/]", "Exit the builder")
            console.print(table)
            console.print()
            choice = Prompt.ask("[bold]Your choice[/]", default="n")
        else:
            ai_indicator = "●" if has_ai else "○"
            print("\nMain Menu:\n")
            print("  [n] ✨ New Prompt    - Create a new prompt")
            print("  [m] 🔗 Combine       - Chain multiple techniques")
            print("  [t] 📦 Templates     - Use custom templates")
            print("  [h] 📜 History       - Browse recent prompts")
            print("  [f] ⭐ Favorites     - View favorite prompts")
            print("  [s] 🔍 Search        - Search saved prompts")
            print(f"  [p] 👁️  Preview Mode  - {'ON' if self.preview_mode else 'OFF'} - Live prompt preview")
            print(f"  [a] 🤖 AI Features {ai_indicator} - Optimize, generate, test, chains")
            print("  [c] ⚙️  Settings      - API keys & configuration")
            print("  [q] 🚪 Quit          - Exit the builder")
            choice = input("\nYour choice: ").strip().lower()

        menu_map = {"n": "new", "m": "combine", "t": "templates", "h": "history", "f": "favorites", 
                    "s": "search", "p": "preview", "a": "ai", "c": "settings", "q": "quit"}
        return menu_map.get(choice.lower(), "new")

    def _create_new_prompt(self):
        """Create a new prompt flow."""
        prompt_type, color = self._select_prompt_type()
        if prompt_type is None:
            return

        config = self._gather_config(prompt_type, color)
        result = self.builder.build(prompt_type, config)

        self._display_result(result, color)
        
        # Auto-save to history
        tags = self._ask_tags()
        prompt_id = self.history.save(
            technique=prompt_type.value,
            task=config.task,
            prompt=result,
            tags=tags
        )
        
        if RICH_AVAILABLE:
            console.print(f"[dim]💾 Auto-saved to history (ID: {prompt_id})[/]")
        
        # Offer additional actions
        self._prompt_actions(prompt_id, result, color)

    def _combine_techniques(self):
        """Combine multiple techniques into a mega-prompt."""
        if RICH_AVAILABLE:
            console.print(Panel(
                "[bold]🔗 Prompt Combiner[/]\n[dim]Chain multiple techniques into one powerful prompt[/]",
                border_style="bright_cyan",
                box=box.ROUNDED
            ))
            console.print("[dim]Select techniques to combine (enter numbers separated by spaces)[/]\n")
        else:
            print("\n🔗 Prompt Combiner")
            print("Select techniques to combine (enter numbers separated by spaces)\n")
        
        # Show technique options
        if RICH_AVAILABLE:
            table = Table(box=box.ROUNDED, border_style="dim", show_header=False, padding=(0, 2))
            table.add_column("Key", style="bold bright_white", width=5)
            table.add_column("Technique", width=22)
            table.add_column("Adds", style="dim")
            
            combo_info = [
                ("Role-Based", "Expert persona context"),
                ("Chain of Thought", "Step-by-step reasoning"),
                ("Few-Shot", "Learning examples"),
                ("Structured", "Output format requirements"),
                ("ReAct", "Reasoning + action framework"),
                ("Tree of Thoughts", "Multi-path exploration"),
                ("Self-Consistency", "Verification approach"),
            ]
            for i, (ptype, name, icon, color, _) in enumerate(self.TECHNIQUES, 1):
                table.add_row(f"[{color}]{i}[/]", f"{icon} [{color}]{name}[/]", combo_info[i-1][1])
            console.print(table)
            console.print()
            choices = Prompt.ask("[bold]Techniques to combine[/] [dim](e.g., 3 1 4)[/]", default="3 1")
        else:
            for i, (_, name, icon, _, _) in enumerate(self.TECHNIQUES, 1):
                print(f"  [{i}] {icon} {name}")
            choices = input("\nTechniques to combine (e.g., 3 1 4): ").strip()
        
        # Parse selections
        try:
            indices = [int(x) - 1 for x in choices.split()]
            selected = [(self.TECHNIQUES[i][0], self.TECHNIQUES[i][1], self.TECHNIQUES[i][3]) 
                       for i in indices if 0 <= i < len(self.TECHNIQUES)]
        except (ValueError, IndexError):
            if RICH_AVAILABLE:
                console.print("[red]Invalid selection[/]")
            return
        
        if len(selected) < 2:
            if RICH_AVAILABLE:
                console.print("[yellow]Select at least 2 techniques to combine[/]")
            return
        
        # Get the task
        if RICH_AVAILABLE:
            selected_names = " + ".join([f"[{c}]{n}[/]" for _, n, c in selected])
            console.print(f"\n[bold]Combining:[/] {selected_names}\n")
            task = Prompt.ask("[bold cyan]📝 What is your task/question?[/]")
            context = Prompt.ask("[bold blue]📖 Context[/] [dim](optional)[/]", default="")
        else:
            print(f"\nCombining: {' + '.join([n for _, n, _ in selected])}\n")
            task = input("📝 What is your task/question?\n> ").strip()
            context = input("\n📖 Context (optional):\n> ").strip()
        
        # Build combined prompt
        combined_parts = []
        combined_parts.append("=" * 50)
        combined_parts.append("COMBINED PROMPT - Multiple Techniques")
        combined_parts.append("=" * 50)
        
        if context:
            combined_parts.append(f"\nContext: {context}")
        combined_parts.append(f"\nTask: {task}")
        combined_parts.append("\n" + "-" * 50)
        
        for ptype, name, _ in selected:
            config = PromptConfig(task=task, context=context)
            section = self.builder.build(ptype, config)
            combined_parts.append(f"\n## {name.upper()} APPROACH ##\n")
            combined_parts.append(section)
            combined_parts.append("\n" + "-" * 50)
        
        combined_parts.append("\nSynthesize insights from all approaches above to provide a comprehensive answer.")
        
        result = "\n".join(combined_parts)
        
        self._display_result(result, "bright_cyan")
        
        # Save to history
        tags = self._ask_tags()
        technique_names = "+".join([p.value for p, _, _ in selected])
        prompt_id = self.history.save(
            technique=f"combined:{technique_names}",
            task=task,
            prompt=result,
            tags=tags
        )
        
        if RICH_AVAILABLE:
            console.print(f"[dim]💾 Auto-saved to history (ID: {prompt_id})[/]")
        
        self._prompt_actions(prompt_id, result, "bright_cyan")

    def _ask_tags(self) -> list[str]:
        """Ask for optional tags."""
        if RICH_AVAILABLE:
            tags_input = Prompt.ask("\n[bold]🏷️  Tags[/] [dim](comma-separated, Enter to skip)[/]", default="")
        else:
            tags_input = input("\n🏷️  Tags (comma-separated, Enter to skip): ").strip()
        
        if tags_input:
            return [t.strip() for t in tags_input.split(",") if t.strip()]
        return []

    def _prompt_actions(self, prompt_id: int, prompt: str, color: str):
        """Offer actions after prompt creation."""
        # Auto-copy to clipboard
        if is_clipboard_available():
            if copy_to_clipboard(prompt):
                if RICH_AVAILABLE:
                    console.print("[green]📋 Copied to clipboard![/]")
                else:
                    print("📋 Copied to clipboard!")
        
        while True:
            if RICH_AVAILABLE:
                console.print("\n[bold]Actions:[/] [cyan]c[/]=copy [yellow]f[/]=favorite [green]s[/]=save file [dim]Enter[/]=continue")
                action = Prompt.ask("[bold]Action[/]", default="")
            else:
                print("\nActions: [c]=copy [f]=favorite [s]=save file [Enter]=continue")
                action = input("Action: ").strip().lower()

            if action == "c":
                if copy_to_clipboard(prompt):
                    if RICH_AVAILABLE:
                        console.print("[green]📋 Copied to clipboard![/]")
                    else:
                        print("📋 Copied to clipboard!")
                else:
                    if RICH_AVAILABLE:
                        console.print("[red]Could not copy to clipboard[/]")
            elif action == "f":
                is_fav = self.history.toggle_favorite(prompt_id)
                if RICH_AVAILABLE:
                    status = "[yellow]⭐ Added to favorites[/]" if is_fav else "[dim]Removed from favorites[/]"
                    console.print(status)
                else:
                    print("⭐ Toggled favorite status")
            elif action == "s":
                self._save_to_file(prompt)
            else:
                break

    def _browse_history(self):
        """Browse recent prompts."""
        prompts = self.history.list_recent(15)
        if not prompts:
            if RICH_AVAILABLE:
                console.print("[dim]No prompts in history yet.[/]\n")
            else:
                print("No prompts in history yet.\n")
            return
        
        self._display_prompt_list(prompts, "📜 Recent Prompts")
        self._select_from_list(prompts)

    def _browse_favorites(self):
        """Browse favorite prompts."""
        prompts = self.history.list_favorites()
        if not prompts:
            if RICH_AVAILABLE:
                console.print("[dim]No favorites yet. Create prompts and mark them as favorites![/]\n")
            else:
                print("No favorites yet.\n")
            return
        
        self._display_prompt_list(prompts, "⭐ Favorite Prompts")
        self._select_from_list(prompts)

    def _search_prompts(self):
        """Search saved prompts."""
        if RICH_AVAILABLE:
            query = Prompt.ask("[bold magenta]🔍 Search[/]")
        else:
            query = input("🔍 Search: ").strip()
        
        prompts = self.history.search(query)
        if not prompts:
            if RICH_AVAILABLE:
                console.print(f"[dim]No prompts found for '{query}'[/]\n")
            else:
                print(f"No prompts found for '{query}'\n")
            return
        
        self._display_prompt_list(prompts, f"🔍 Results for '{query}'")
        self._select_from_list(prompts)

    def _display_prompt_list(self, prompts: list[SavedPrompt], title: str):
        """Display a list of prompts."""
        if RICH_AVAILABLE:
            table = Table(title=title, box=box.ROUNDED, border_style="dim")
            table.add_column("#", style="bold", width=4)
            table.add_column("Technique", width=12)
            table.add_column("Task", width=35)
            table.add_column("Tags", style="dim", width=15)
            table.add_column("⭐", width=3)
            
            for i, p in enumerate(prompts, 1):
                fav = "⭐" if p.is_favorite else ""
                task_preview = p.task[:32] + "..." if len(p.task) > 35 else p.task
                tags = ", ".join(p.tags[:3]) if p.tags else ""
                table.add_row(str(i), p.technique, task_preview, tags, fav)
            
            console.print(table)
        else:
            print(f"\n{title}\n" + "-" * 50)
            for i, p in enumerate(prompts, 1):
                fav = "⭐" if p.is_favorite else "  "
                task_preview = p.task[:40] + "..." if len(p.task) > 40 else p.task
                print(f"{i}. {fav} [{p.technique}] {task_preview}")

    def _select_from_list(self, prompts: list[SavedPrompt]):
        """Let user select a prompt from the list."""
        if RICH_AVAILABLE:
            choice = Prompt.ask("\n[bold]Select #[/] [dim](or Enter to go back)[/]", default="")
        else:
            choice = input("\nSelect # (or Enter to go back): ").strip()
        
        if not choice:
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(prompts):
                self._view_prompt(prompts[idx])
        except ValueError:
            pass

    def _view_prompt(self, saved: SavedPrompt):
        """View a saved prompt with actions."""
        color = "cyan"
        for ptype, _, _, c, _ in self.TECHNIQUES:
            if ptype.value == saved.technique:
                color = c
                break
        
        if RICH_AVAILABLE:
            console.print(Panel(
                saved.prompt,
                title=f"[bold]{saved.technique.upper()}[/] - {saved.task[:40]}",
                subtitle=f"[dim]ID: {saved.id} | Created: {saved.created_at.strftime('%Y-%m-%d %H:%M')}[/]",
                border_style=color,
                box=box.DOUBLE,
                padding=(1, 2)
            ))
        else:
            print(f"\n{'=' * 50}")
            print(f"[{saved.technique}] {saved.task}")
            print(f"{'=' * 50}")
            print(saved.prompt)
            print(f"{'=' * 50}")
        
        # Actions
        while True:
            if RICH_AVAILABLE:
                console.print("\n[bold]Actions:[/] [cyan]c[/]=copy [yellow]f[/]=toggle favorite [green]s[/]=save file [red]d[/]=delete [dim]b[/]=back")
                action = Prompt.ask("[bold]Action[/]", default="b")
            else:
                print("\nActions: [c]=copy [f]=favorite [s]=save [d]=delete [b]=back")
                action = input("Action: ").strip().lower()

            if action == "c":
                if copy_to_clipboard(saved.prompt):
                    if RICH_AVAILABLE:
                        console.print("[green]📋 Copied to clipboard![/]")
                    else:
                        print("📋 Copied to clipboard!")
            elif action == "f":
                is_fav = self.history.toggle_favorite(saved.id)
                if RICH_AVAILABLE:
                    console.print("[yellow]⭐ Favorite toggled[/]" if is_fav else "[dim]Removed from favorites[/]")
            elif action == "s":
                self._save_to_file(saved.prompt)
            elif action == "d":
                if self._confirm("[red]Delete this prompt?[/]"):
                    self.history.delete(saved.id)
                    if RICH_AVAILABLE:
                        console.print("[red]🗑️  Deleted[/]")
                    break
            elif action == "b":
                break

    def _save_to_file(self, prompt: str, technique: str = "unknown", task: str = ""):
        """Save prompt to file with format selection."""
        # Show format options
        if RICH_AVAILABLE:
            console.print("\n[bold]Export Formats:[/]")
            table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            table.add_column("Key", style="cyan", width=4)
            table.add_column("Format", width=20)
            
            format_keys = list(EXPORT_FORMATS.keys())
            for i, key in enumerate(format_keys, 1):
                name, _, ext = EXPORT_FORMATS[key]
                table.add_row(str(i), f"{name} ({ext})")
            console.print(table)
            
            choice = Prompt.ask("[bold]Format[/]", default="1")
        else:
            print("\nExport Formats:")
            format_keys = list(EXPORT_FORMATS.keys())
            for i, key in enumerate(format_keys, 1):
                name, _, ext = EXPORT_FORMATS[key]
                print(f"  [{i}] {name} ({ext})")
            choice = input("Format (1): ").strip() or "1"
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(format_keys):
                format_key = format_keys[idx]
            else:
                format_key = "txt"
        except ValueError:
            format_key = "txt"
        
        # Create metadata
        metadata = PromptMetadata(
            technique=technique,
            task=task[:50] if task else "prompt",
            created_at=datetime.now().isoformat()
        )
        
        # Export
        content, extension = export_prompt(prompt, format_key, metadata)
        
        # Get filename
        default_name = f"prompt{extension}"
        if RICH_AVAILABLE:
            filename = Prompt.ask("[dim]Filename[/]", default=default_name)
        else:
            filename = input(f"Filename ({default_name}): ").strip() or default_name
        
        with open(filename, 'w') as f:
            f.write(content)
        
        if RICH_AVAILABLE:
            console.print(f"[bold green]✅ Exported to {filename}[/]")
        else:
            print(f"✅ Exported to {filename}")

    def _show_header(self):
        """Display the application header."""
        if RICH_AVAILABLE:
            header = Text()
            header.append("⚡ PROMPT BUILDER ⚡\n", style="bold bright_white")
            header.append("Modern Prompt Engineering Techniques", style="dim")
            console.print(Panel(header, border_style="bright_blue", box=box.DOUBLE))
            console.print()
        else:
            print("\n" + "=" * 50)
            print("⚡ PROMPT BUILDER - Prompt Engineering Techniques")
            print("=" * 50 + "\n")

    def _show_goodbye(self):
        """Display goodbye message."""
        if RICH_AVAILABLE:
            console.print(Panel(
                "[bold green]Happy prompting! 🎯[/]\n[dim]May your tokens be ever efficient.[/]",
                border_style="green",
                box=box.ROUNDED
            ))
        else:
            print("\nGoodbye! Happy prompting! 🎯")

    def _select_prompt_type(self) -> tuple[Optional[PromptType], str]:
        """Let user select a prompt engineering technique."""
        if RICH_AVAILABLE:
            console.print("[bold bright_white]Select a technique:[/]\n")
            
            table = Table(box=box.ROUNDED, border_style="dim", show_header=False, padding=(0, 2))
            table.add_column("Key", style="bold bright_white", width=5)
            table.add_column("Technique", width=22)
            table.add_column("Description", style="dim")

            for i, (_, name, icon, color, desc) in enumerate(self.TECHNIQUES, 1):
                table.add_row(
                    f"[{color}]{i}[/]",
                    f"{icon} [{color}]{name}[/]",
                    desc
                )
            table.add_row("[red]q[/]", "🚪 [red]Quit[/]", "Exit the builder")
            
            console.print(table)
            console.print()
            
            choice = Prompt.ask("[bold]Your choice[/]", default="1")
        else:
            print("Select a technique:\n")
            for i, (_, name, icon, _, desc) in enumerate(self.TECHNIQUES, 1):
                print(f"  [{i}] {icon} {name:<20} - {desc}")
            print("  [q] 🚪 Quit")
            choice = input("\nYour choice: ").strip()

        if choice.lower() == 'q':
            return None, ""

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self.TECHNIQUES):
                ptype, name, icon, color, _ = self.TECHNIQUES[idx]
                if RICH_AVAILABLE:
                    console.print(f"\n[{color}]✓ Selected: {icon} {name}[/]\n")
                return ptype, color
        except ValueError:
            pass

        if RICH_AVAILABLE:
            console.print("[red]Invalid choice, try again.[/]\n")
        else:
            print("Invalid choice, try again.\n")
        return self._select_prompt_type()

    def _gather_config(self, prompt_type: PromptType, color: str) -> PromptConfig:
        """Gather configuration based on prompt type with optional live preview."""
        if RICH_AVAILABLE:
            console.print(Panel(
                f"[bold]Configure your prompt[/]" + (" [dim](Preview Mode ON)[/]" if self.preview_mode else ""),
                border_style=color,
                box=box.ROUNDED
            ))
            task = Prompt.ask("\n[bold cyan]📝 What is your task/question?[/]")
            context = Prompt.ask("[bold blue]📖 Context[/] [dim](optional, Enter to skip)[/]", default="")
        else:
            print(f"\n--- Configure {prompt_type.name} ---\n")
            task = input("📝 What is your task/question?\n> ").strip()
            context = input("\n📖 Context (optional, Enter to skip):\n> ").strip()

        config = PromptConfig(task=task, context=context)
        
        # Show preview after basic config
        if self.preview_mode:
            self._show_live_preview(prompt_type, config, color)

        # Type-specific configuration
        if prompt_type == PromptType.FEW_SHOT:
            config.examples = self._gather_examples()
            if self.preview_mode:
                self._show_live_preview(prompt_type, config, color)
        elif prompt_type == PromptType.ROLE_BASED:
            config.role = self._ask("[bold magenta]🎭 Role/Persona[/]", 
                                    "e.g., 'senior Python developer'")
            if self.preview_mode:
                self._show_live_preview(prompt_type, config, color)
        elif prompt_type == PromptType.STRUCTURED:
            config.output_format = self._ask("[bold yellow]📋 Output format[/]",
                                             "e.g., JSON, Markdown, Table")
            if self.preview_mode:
                self._show_live_preview(prompt_type, config, color)

        # Optional constraints
        if self._confirm("[bold]Add constraints?[/]"):
            config.constraints = self._gather_constraints()
            if self.preview_mode:
                self._show_live_preview(prompt_type, config, color)

        return config

    def _show_live_preview(self, prompt_type: PromptType, config: PromptConfig, color: str):
        """Show a live preview of the prompt being built."""
        preview = self.builder.build(prompt_type, config)
        token_count = self.token_counter.count_tokens(preview)
        
        if RICH_AVAILABLE:
            # Truncate for preview
            preview_text = preview[:500] + "..." if len(preview) > 500 else preview
            console.print()
            console.print(Panel(
                f"[dim]{preview_text}[/]",
                title=f"[dim]👁️ Preview ({token_count} tokens)[/]",
                border_style="dim",
                box=box.ROUNDED,
                padding=(0, 1)
            ))
        else:
            preview_text = preview[:300] + "..." if len(preview) > 300 else preview
            print(f"\n--- Preview ({token_count} tokens) ---")
            print(preview_text)
            print("---")

    def _toggle_preview_mode(self):
        """Toggle live preview mode."""
        self.preview_mode = not self.preview_mode
        status = "ON" if self.preview_mode else "OFF"
        if RICH_AVAILABLE:
            console.print(f"[bold]👁️ Preview Mode: [{'green' if self.preview_mode else 'red'}]{status}[/]")
        else:
            print(f"👁️ Preview Mode: {status}")

    def _ask(self, label: str, hint: str = "") -> str:
        """Ask for input with rich formatting."""
        if RICH_AVAILABLE:
            hint_text = f" [dim]({hint})[/]" if hint else ""
            return Prompt.ask(f"{label}{hint_text}", default="")
        else:
            hint_text = f" ({hint})" if hint else ""
            return input(f"{label}{hint_text}: ").strip()

    def _confirm(self, message: str) -> bool:
        """Ask for confirmation."""
        if RICH_AVAILABLE:
            return Confirm.ask(message, default=False)
        else:
            return input(f"{message} (y/n): ").strip().lower() == 'y'

    def _gather_examples(self) -> list[dict]:
        """Gather few-shot examples from user."""
        examples = []
        if RICH_AVAILABLE:
            console.print("\n[bold green]📚 Provide examples[/] [dim](type 'done' when finished)[/]\n")
        else:
            print("\nProvide examples (type 'done' when finished):\n")

        while True:
            num = len(examples) + 1
            if RICH_AVAILABLE:
                console.print(f"[bold]Example {num}[/]")
                inp = Prompt.ask("  [cyan]Input[/] [dim](or 'done')[/]")
            else:
                inp = input(f"Example {num} - Input (or 'done'): ").strip()

            if inp.lower() == 'done':
                break

            if RICH_AVAILABLE:
                out = Prompt.ask("  [green]Output[/]")
            else:
                out = input(f"Example {num} - Output: ").strip()

            examples.append({"input": inp, "output": out})
            if RICH_AVAILABLE:
                console.print(f"  [dim]✓ Added[/]\n")

        return examples

    def _gather_constraints(self) -> list[str]:
        """Gather constraints from user."""
        constraints = []
        if RICH_AVAILABLE:
            console.print("\n[bold yellow]⚠️  Enter constraints[/] [dim](type 'done' when finished)[/]\n")
        else:
            print("\nEnter constraints (type 'done' when finished):\n")

        while True:
            num = len(constraints) + 1
            if RICH_AVAILABLE:
                c = Prompt.ask(f"  [yellow]Constraint {num}[/] [dim](or 'done')[/]")
            else:
                c = input(f"Constraint {num} (or 'done'): ").strip()

            if c.lower() == 'done':
                break
            constraints.append(c)

        return constraints

    def _display_result(self, prompt: str, color: str):
        """Display the generated prompt with token estimates."""
        if RICH_AVAILABLE:
            console.print()
            console.print(Panel(
                prompt,
                title="[bold bright_white]📝 Generated Prompt[/]",
                border_style=color,
                box=box.DOUBLE,
                padding=(1, 2)
            ))
            # Show token estimates
            self._show_token_estimates(prompt)
        else:
            print("\n" + "=" * 50)
            print("📝 GENERATED PROMPT:")
            print("=" * 50)
            print(prompt)
            print("=" * 50)
            self._show_token_estimates(prompt)

    def _show_token_estimates(self, prompt: str):
        """Display token count and cost estimates."""
        estimates = self.token_counter.estimate_all_models(prompt)
        
        if RICH_AVAILABLE:
            table = Table(box=box.SIMPLE, border_style="dim", show_header=True, padding=(0, 1))
            table.add_column("Model", style="cyan", width=18)
            table.add_column("Tokens", justify="right", width=8)
            table.add_column("Input Cost", justify="right", style="green", width=10)
            table.add_column("Output/1K", justify="right", style="dim", width=10)
            
            for est in estimates:
                table.add_row(
                    est.model,
                    str(est.token_count),
                    est.formatted_cost,
                    f"${est.output_cost_1k:.4f}"
                )
            
            console.print(Panel(table, title="[dim]💰 Token Estimates[/]", border_style="dim", box=box.ROUNDED))
        else:
            print("\n💰 Token Estimates:")
            for est in estimates:
                print(f"  {est.model:<18} {est.token_count:>6} tokens  Input: {est.formatted_cost}")

    def _continue_prompt(self) -> bool:
        """Ask if user wants to create another prompt."""
        if RICH_AVAILABLE:
            console.print()
        return self._confirm("[bold]Create another prompt?[/]")

    # ==================== AI FEATURES ====================

    def _ai_features_menu(self):
        """Show AI-powered features menu."""
        if not self.api_config.has_any_provider():
            if RICH_AVAILABLE:
                console.print(Panel(
                    "[yellow]No API keys configured![/]\n\n"
                    "AI features require at least one LLM provider.\n"
                    "Go to [bold]Settings[/] to add your API keys.",
                    title="[yellow]⚠️ API Keys Required[/]",
                    border_style="yellow"
                ))
            else:
                print("\n⚠️ No API keys configured! Go to Settings to add your keys.\n")
            return

        while True:
            if RICH_AVAILABLE:
                console.print("\n[bold bright_magenta]🤖 AI Features[/]\n")
                table = Table(box=box.ROUNDED, border_style="dim", show_header=False, padding=(0, 2))
                table.add_column("Key", width=5)
                table.add_column("Feature", width=25)
                table.add_column("Description", style="dim")
                table.add_row("[cyan]g[/]", "🪄 [cyan]Generate from Description[/]", "Describe task in plain English")
                table.add_row("[green]o[/]", "✨ [green]Optimize Prompt[/]", "AI-powered prompt improvement")
                table.add_row("[yellow]t[/]", "🧪 [yellow]Test Prompt[/]", "Test against multiple models")
                table.add_row("[magenta]c[/]", "⛓️  [magenta]Prompt Chains[/]", "Multi-step workflows")
                table.add_row("[blue]s[/]", "📤 [blue]Share & Import[/]", "Export/import prompt libraries")
                table.add_row("[white]a[/]", "📊 [white]Analytics[/]", "View usage statistics")
                table.add_row("[red]b[/]", "🔙 [red]Back[/]", "Return to main menu")
                console.print(table)
                choice = Prompt.ask("\n[bold]Select[/]", default="b")
            else:
                print("\n🤖 AI Features:\n")
                print("  [g] 🪄 Generate from Description")
                print("  [o] ✨ Optimize Prompt")
                print("  [t] 🧪 Test Prompt")
                print("  [c] ⛓️  Prompt Chains")
                print("  [s] 📤 Share & Import")
                print("  [a] 📊 Analytics")
                print("  [b] 🔙 Back")
                choice = input("\nSelect: ").strip().lower()

            if choice == "b":
                break
            elif choice == "g":
                self._generate_from_description()
            elif choice == "o":
                self._optimize_prompt()
            elif choice == "t":
                self._test_prompt()
            elif choice == "c":
                self._prompt_chains_menu()
            elif choice == "s":
                self._sharing_menu()
            elif choice == "a":
                self._show_analytics()

    def _generate_from_description(self):
        """Generate a prompt from natural language description."""
        import asyncio
        
        if RICH_AVAILABLE:
            console.print(Panel(
                "[bold]Describe what you want to accomplish[/]\n[dim]I'll generate the optimal prompt for you[/]",
                border_style="cyan"
            ))
            description = Prompt.ask("\n[bold cyan]📝 What do you want to do?[/]")
            context = Prompt.ask("[dim]Additional context (optional)[/]", default="")
        else:
            print("\n🪄 Generate from Description")
            description = input("What do you want to do?\n> ").strip()
            context = input("Additional context (optional): ").strip()

        if RICH_AVAILABLE:
            with console.status("[bold cyan]Generating prompt...[/]"):
                result = asyncio.run(self.nl_generator.generate(description, context))
        else:
            print("Generating...")
            result = asyncio.run(self.nl_generator.generate(description, context))

        if result.error:
            if RICH_AVAILABLE:
                console.print(f"[red]Error: {result.error}[/]")
            else:
                print(f"Error: {result.error}")
            return

        if RICH_AVAILABLE:
            console.print(f"\n[dim]Technique: [cyan]{result.technique}[/] (confidence: {result.confidence:.0%})[/]")
            console.print(f"[dim]{result.explanation}[/]\n")
        
        self._display_result(result.prompt, "cyan")
        
        # Save to history
        tags = self._ask_tags()
        prompt_id = self.history.save(
            technique=f"generated:{result.technique}",
            task=description,
            prompt=result.prompt,
            tags=tags
        )
        self._prompt_actions(prompt_id, result.prompt, "cyan")

    def _optimize_prompt(self):
        """Optimize an existing prompt using AI."""
        import asyncio
        
        if RICH_AVAILABLE:
            console.print(Panel(
                "[bold]Paste your prompt to optimize[/]",
                border_style="green"
            ))
            prompt = Prompt.ask("\n[bold green]📝 Your prompt[/]")
            context = Prompt.ask("[dim]What's this prompt for? (optional)[/]", default="")
        else:
            print("\n✨ Optimize Prompt")
            prompt = input("Your prompt:\n> ").strip()
            context = input("What's this for? (optional): ").strip()

        if RICH_AVAILABLE:
            with console.status("[bold green]Analyzing and optimizing...[/]"):
                result = asyncio.run(self.optimizer.optimize(prompt, context))
        else:
            print("Optimizing...")
            result = asyncio.run(self.optimizer.optimize(prompt, context))

        if result.error:
            if RICH_AVAILABLE:
                console.print(f"[red]Error: {result.error}[/]")
            else:
                print(f"Error: {result.error}")
            return

        # Show scores
        if RICH_AVAILABLE:
            console.print("\n[bold]📊 Analysis Scores:[/]")
            console.print(f"  Clarity:       [cyan]{'█' * result.clarity_score}{'░' * (10-result.clarity_score)}[/] {result.clarity_score}/10")
            console.print(f"  Specificity:   [green]{'█' * result.specificity_score}{'░' * (10-result.specificity_score)}[/] {result.specificity_score}/10")
            console.print(f"  Effectiveness: [yellow]{'█' * result.effectiveness_score}{'░' * (10-result.effectiveness_score)}[/] {result.effectiveness_score}/10")
            
            if result.suggestions:
                console.print("\n[bold]💡 Suggestions:[/]")
                for s in result.suggestions:
                    console.print(f"  • {s}")
            
            console.print(f"\n[dim]{result.explanation}[/]")
        else:
            print(f"\nScores: Clarity={result.clarity_score}/10, Specificity={result.specificity_score}/10, Effectiveness={result.effectiveness_score}/10")
            if result.suggestions:
                print("\nSuggestions:")
                for s in result.suggestions:
                    print(f"  • {s}")

        self._display_result(result.optimized_prompt, "green")
        
        tags = self._ask_tags()
        prompt_id = self.history.save(
            technique="optimized",
            task="Optimized prompt",
            prompt=result.optimized_prompt,
            tags=tags
        )
        self._prompt_actions(prompt_id, result.optimized_prompt, "green")

    def _test_prompt(self):
        """Test a prompt against multiple models."""
        import asyncio
        
        if RICH_AVAILABLE:
            console.print(Panel(
                "[bold]Test your prompt across different models[/]",
                border_style="yellow"
            ))
            prompt = Prompt.ask("\n[bold yellow]📝 Prompt to test[/]")
        else:
            print("\n🧪 Test Prompt")
            prompt = input("Prompt to test:\n> ").strip()

        # Get available models
        available = self.api_config.get_available_models()
        if not available:
            if RICH_AVAILABLE:
                console.print("[red]No models available[/]")
            return

        if RICH_AVAILABLE:
            console.print("\n[bold]Available models:[/]")
            for i, (provider, model) in enumerate(available[:6], 1):
                console.print(f"  [{i}] {provider}: {model}")
            
            with console.status("[bold yellow]Testing across models...[/]"):
                results = []
                for provider, model in available[:3]:  # Test first 3
                    response = asyncio.run(self.llm_client.complete(prompt, provider, model, max_tokens=500))
                    results.append((provider, model, response))
        else:
            print("\nTesting...")
            results = []
            for provider, model in available[:3]:
                response = asyncio.run(self.llm_client.complete(prompt, provider, model, max_tokens=500))
                results.append((provider, model, response))

        # Display results
        if RICH_AVAILABLE:
            console.print("\n[bold]📊 Results:[/]\n")
            for provider, model, response in results:
                if response.error:
                    console.print(f"[red]{provider}/{model}: Error - {response.error}[/]")
                else:
                    preview = response.content[:200] + "..." if len(response.content) > 200 else response.content
                    console.print(Panel(
                        preview,
                        title=f"[bold]{provider}/{model}[/]",
                        subtitle=f"[dim]{response.input_tokens + response.output_tokens} tokens[/]",
                        border_style="dim"
                    ))
        else:
            for provider, model, response in results:
                print(f"\n--- {provider}/{model} ---")
                if response.error:
                    print(f"Error: {response.error}")
                else:
                    print(response.content[:300])

    def _prompt_chains_menu(self):
        """Manage and execute prompt chains."""
        import asyncio
        
        while True:
            chains = list(self.chain_executor.chains.keys()) + list(BUILTIN_CHAINS.keys())
            
            if RICH_AVAILABLE:
                console.print("\n[bold magenta]⛓️ Prompt Chains[/]\n")
                table = Table(box=box.ROUNDED, border_style="dim", show_header=False)
                table.add_column("Key", width=5)
                table.add_column("Action", width=30)
                
                for i, name in enumerate(chains[:5], 1):
                    chain = self.chain_executor.get_chain(name) or BUILTIN_CHAINS.get(name)
                    desc = chain.description[:30] if chain else ""
                    table.add_row(f"[cyan]{i}[/]", f"▶️  {name} [dim]- {desc}[/]")
                
                table.add_row("[green]n[/]", "➕ [green]Create new chain[/]")
                table.add_row("[red]b[/]", "🔙 [red]Back[/]")
                console.print(table)
                choice = Prompt.ask("\n[bold]Select[/]", default="b")
            else:
                print("\n⛓️ Prompt Chains:\n")
                for i, name in enumerate(chains[:5], 1):
                    print(f"  [{i}] {name}")
                print("  [n] Create new chain")
                print("  [b] Back")
                choice = input("\nSelect: ").strip().lower()

            if choice == "b":
                break
            elif choice == "n":
                self._create_chain()
            else:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(chains):
                        self._execute_chain(chains[idx])
                except ValueError:
                    pass

    def _execute_chain(self, chain_name: str):
        """Execute a prompt chain."""
        import asyncio
        
        chain = self.chain_executor.get_chain(chain_name) or BUILTIN_CHAINS.get(chain_name)
        if not chain:
            return

        if RICH_AVAILABLE:
            console.print(Panel(
                f"[bold]{chain.name}[/]\n[dim]{chain.description}[/]\n\nSteps: {len(chain.steps)}",
                border_style="magenta"
            ))
        
        # Gather input context
        input_context = {}
        if RICH_AVAILABLE:
            console.print("\n[bold]Provide input values:[/]")
        
        # Find variables in first step
        first_step = chain.steps[0].prompt_template
        import re
        vars_found = set(re.findall(r'\{(\w+)\}', first_step))
        
        for var in vars_found:
            if RICH_AVAILABLE:
                input_context[var] = Prompt.ask(f"[cyan]{var}[/]")
            else:
                input_context[var] = input(f"{var}: ").strip()

        # Execute
        if RICH_AVAILABLE:
            with console.status("[bold magenta]Executing chain...[/]"):
                result = asyncio.run(self.chain_executor.execute(chain, input_context))
        else:
            print("Executing...")
            result = asyncio.run(self.chain_executor.execute(chain, input_context))

        # Show results
        if RICH_AVAILABLE:
            status = "[green]✓ Success[/]" if result.success else "[red]✗ Failed[/]"
            console.print(f"\n{status} - {result.steps_completed}/{result.total_steps} steps")
            console.print(f"[dim]Tokens: {result.total_tokens} | Latency: {result.total_latency_ms}ms[/]")
            
            if result.errors:
                for err in result.errors:
                    console.print(f"[red]  {err}[/]")
            
            if result.final_output:
                console.print(Panel(result.final_output, title="[bold]Final Output[/]", border_style="green"))
        else:
            print(f"\n{'Success' if result.success else 'Failed'} - {result.steps_completed}/{result.total_steps} steps")
            if result.final_output:
                print(f"\nOutput:\n{result.final_output}")

    def _create_chain(self):
        """Create a new prompt chain."""
        if RICH_AVAILABLE:
            name = Prompt.ask("[bold]Chain name[/]")
            description = Prompt.ask("[dim]Description[/]", default="")
        else:
            name = input("Chain name: ").strip()
            description = input("Description: ").strip()

        steps = []
        if RICH_AVAILABLE:
            console.print("\n[dim]Add steps (type 'done' when finished)[/]")
        
        while True:
            if RICH_AVAILABLE:
                step_name = Prompt.ask(f"\n[bold]Step {len(steps)+1} name[/] [dim](or 'done')[/]")
            else:
                step_name = input(f"\nStep {len(steps)+1} name (or 'done'): ").strip()
            
            if step_name.lower() == 'done':
                break
            
            if RICH_AVAILABLE:
                prompt_template = Prompt.ask("[cyan]Prompt template[/]")
                output_key = Prompt.ask("[dim]Output variable name[/]", default=f"step{len(steps)+1}_output")
            else:
                prompt_template = input("Prompt template: ").strip()
                output_key = input("Output variable name: ").strip() or f"step{len(steps)+1}_output"
            
            steps.append(ChainStep(
                name=step_name,
                prompt_template=prompt_template,
                output_key=output_key
            ))

        if steps:
            self.chain_executor.create_chain(name, description, steps)
            if RICH_AVAILABLE:
                console.print(f"[green]✓ Chain '{name}' created with {len(steps)} steps[/]")
            else:
                print(f"Chain '{name}' created!")

    def _sharing_menu(self):
        """Share and import prompt libraries."""
        while True:
            if RICH_AVAILABLE:
                console.print("\n[bold blue]📤 Share & Import[/]\n")
                table = Table(box=box.ROUNDED, border_style="dim", show_header=False)
                table.add_column("Key", width=5)
                table.add_column("Action", width=30)
                table.add_row("[cyan]e[/]", "📦 [cyan]Export library[/]")
                table.add_row("[green]i[/]", "📥 [green]Import from code[/]")
                table.add_row("[yellow]l[/]", "📚 [yellow]List libraries[/]")
                table.add_row("[red]b[/]", "🔙 [red]Back[/]")
                console.print(table)
                choice = Prompt.ask("\n[bold]Select[/]", default="b")
            else:
                print("\n📤 Share & Import:\n")
                print("  [e] Export library")
                print("  [i] Import from code")
                print("  [l] List libraries")
                print("  [b] Back")
                choice = input("\nSelect: ").strip().lower()

            if choice == "b":
                break
            elif choice == "e":
                self._export_library()
            elif choice == "i":
                self._import_library()
            elif choice == "l":
                self._list_libraries()

    def _export_library(self):
        """Export prompts to a shareable library."""
        prompts = self.history.list_recent(50)
        if not prompts:
            if RICH_AVAILABLE:
                console.print("[dim]No prompts to export[/]")
            return

        if RICH_AVAILABLE:
            name = Prompt.ask("[bold]Library name[/]")
            description = Prompt.ask("[dim]Description[/]", default="")
        else:
            name = input("Library name: ").strip()
            description = input("Description: ").strip()

        shared_prompts = [
            SharedPrompt(
                id="",
                name=p.task[:50],
                technique=p.technique,
                prompt=p.prompt,
                tags=p.tags
            )
            for p in prompts[:20]  # Export up to 20
        ]

        library = self.sharing.create_library(name, description, shared_prompts)
        path = self.sharing.export_library(library)
        share_code = self.sharing.generate_share_code(library)

        if RICH_AVAILABLE:
            console.print(f"\n[green]✓ Exported to {path}[/]")
            console.print(f"\n[bold]Share code:[/]\n[cyan]{share_code[:100]}...[/]")
        else:
            print(f"\nExported to {path}")
            print(f"Share code: {share_code[:80]}...")

    def _import_library(self):
        """Import a library from share code."""
        if RICH_AVAILABLE:
            code = Prompt.ask("[bold]Paste share code[/]")
        else:
            code = input("Paste share code: ").strip()

        try:
            library = self.sharing.import_from_share_code(code)
            self.sharing.export_library(library)
            if RICH_AVAILABLE:
                console.print(f"[green]✓ Imported '{library.name}' with {len(library.prompts)} prompts[/]")
            else:
                print(f"Imported '{library.name}' with {len(library.prompts)} prompts")
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]Error: {e}[/]")
            else:
                print(f"Error: {e}")

    def _list_libraries(self):
        """List local libraries."""
        libraries = self.sharing.list_local_libraries()
        if not libraries:
            if RICH_AVAILABLE:
                console.print("[dim]No libraries found[/]")
            return

        if RICH_AVAILABLE:
            table = Table(title="📚 Local Libraries", box=box.ROUNDED)
            table.add_column("Name")
            table.add_column("Prompts", justify="right")
            for name in libraries:
                lib = self.sharing.load_local_library(name)
                count = len(lib.prompts) if lib else 0
                table.add_row(name, str(count))
            console.print(table)
        else:
            print("\nLocal Libraries:")
            for name in libraries:
                print(f"  • {name}")

    def _show_analytics(self):
        """Show usage analytics."""
        summary = self.analytics.get_summary(30)
        
        if RICH_AVAILABLE:
            console.print("\n[bold white]📊 Analytics (Last 30 Days)[/]\n")
            
            # Stats
            table = Table(box=box.SIMPLE, show_header=False)
            table.add_column("Metric", style="dim")
            table.add_column("Value", style="bold")
            table.add_row("Total Prompts", str(summary.total_prompts))
            table.add_row("Total Tokens", f"{summary.total_tokens:,}")
            table.add_row("Total Cost", f"${summary.total_cost:.2f}")
            table.add_row("Avg Latency", f"{summary.avg_latency_ms:.0f}ms")
            table.add_row("Success Rate", f"{summary.success_rate:.1f}%")
            console.print(table)
            
            if summary.top_techniques:
                console.print("\n[bold]Top Techniques:[/]")
                for tech, count in summary.top_techniques[:5]:
                    console.print(f"  {tech}: [cyan]{count}[/]")
            
            if summary.cost_by_provider:
                console.print("\n[bold]Cost by Provider:[/]")
                for provider, cost in summary.cost_by_provider.items():
                    console.print(f"  {provider}: [green]${cost:.2f}[/]")
        else:
            print("\n📊 Analytics (Last 30 Days)")
            print(f"  Prompts: {summary.total_prompts}")
            print(f"  Tokens: {summary.total_tokens:,}")
            print(f"  Cost: ${summary.total_cost:.2f}")

    # ==================== SETTINGS ====================

    def _settings_menu(self):
        """Settings and configuration menu."""
        while True:
            providers = self.api_config.get_available_providers()
            
            if RICH_AVAILABLE:
                console.print("\n[bold dim]⚙️ Settings[/]\n")
                
                # Show current status
                console.print("[bold]API Keys Status:[/]")
                for name, provider in self.api_config.providers.items():
                    status = "[green]✓ Configured[/]" if provider.is_available else "[red]✗ Not set[/]"
                    console.print(f"  {name.capitalize()}: {status}")
                
                console.print()
                table = Table(box=box.ROUNDED, border_style="dim", show_header=False)
                table.add_column("Key", width=5)
                table.add_column("Action", width=30)
                table.add_row("[cyan]o[/]", "🔑 [cyan]Set OpenAI key[/]")
                table.add_row("[green]a[/]", "🔑 [green]Set Anthropic key[/]")
                table.add_row("[yellow]g[/]", "🔑 [yellow]Set Google key[/]")
                table.add_row("[red]b[/]", "🔙 [red]Back[/]")
                console.print(table)
                choice = Prompt.ask("\n[bold]Select[/]", default="b")
            else:
                print("\n⚙️ Settings\n")
                print("API Keys Status:")
                for name, provider in self.api_config.providers.items():
                    status = "✓" if provider.is_available else "✗"
                    print(f"  {name}: {status}")
                print("\n  [o] Set OpenAI key")
                print("  [a] Set Anthropic key")
                print("  [g] Set Google key")
                print("  [b] Back")
                choice = input("\nSelect: ").strip().lower()

            if choice == "b":
                break
            elif choice == "o":
                self._set_api_key("openai")
            elif choice == "a":
                self._set_api_key("anthropic")
            elif choice == "g":
                self._set_api_key("google")

    def _set_api_key(self, provider: str):
        """Set API key for a provider."""
        if RICH_AVAILABLE:
            key = Prompt.ask(f"[bold]Enter {provider.capitalize()} API key[/]", password=True)
        else:
            key = input(f"Enter {provider.capitalize()} API key: ").strip()
        
        if key:
            self.api_config.set_api_key(provider, key)
            # Reinitialize client
            self.llm_client = LLMClient(self.api_config)
            self.optimizer = PromptOptimizer(self.llm_client)
            self.nl_generator = NaturalLanguageGenerator(self.llm_client)
            
            if RICH_AVAILABLE:
                console.print(f"[green]✓ {provider.capitalize()} API key saved[/]")
            else:
                print(f"✓ {provider.capitalize()} API key saved")


def quick_build(
    technique: str,
    task: str,
    context: str = "",
    role: str = "",
    examples: list[dict] = None,
    output_format: str = "",
    constraints: list[str] = None
) -> str:
    """
    Quick function to build prompts programmatically.

    Args:
        technique: One of 'cot', 'few_shot', 'role', 'structured', 'react', 'tot', 'self_consistency'
        task: The main task or question
        context: Optional background context
        role: Role/persona (for role-based prompts)
        examples: List of {"input": ..., "output": ...} dicts (for few-shot)
        output_format: Desired format (for structured prompts)
        constraints: List of constraints to include

    Returns:
        Generated prompt string
    """
    builder = PromptBuilder()
    prompt_type = PromptType(technique)
    config = PromptConfig(
        task=task,
        context=context,
        role=role,
        examples=examples or [],
        output_format=output_format,
        constraints=constraints or []
    )
    return builder.build(prompt_type, config)


if __name__ == "__main__":
    if not RICH_AVAILABLE:
        print("💡 Tip: Install 'rich' for a better experience: pip install rich\n")
    app = InteractivePromptBuilder()
    app.run()
