"""
Context Window Manager - Handle long contexts intelligently.
Feature #7: Context Window Manager
"""

from dataclasses import dataclass
from typing import Optional
import re

from token_counter import TokenCounter


@dataclass
class ContextChunk:
    content: str
    tokens: int
    index: int
    is_summary: bool = False


@dataclass
class ManagedContext:
    chunks: list[ContextChunk]
    total_tokens: int
    original_tokens: int
    was_truncated: bool
    summary: Optional[str] = None


# Model context limits (conservative estimates leaving room for output)
MODEL_LIMITS = {
    "gpt-4o": 120000,
    "gpt-4o-mini": 120000,
    "gpt-4-turbo": 120000,
    "gpt-4": 8000,
    "gpt-3.5-turbo": 14000,
    "claude-3-5-sonnet-20241022": 190000,
    "claude-3-opus-20240229": 190000,
    "claude-3-haiku-20240307": 190000,
    "gemini-1.5-pro": 1000000,
    "gemini-1.5-flash": 1000000,
    "gemini-pro": 30000,
}

DEFAULT_LIMIT = 8000


class ContextManager:
    """Manage context windows for LLM interactions."""

    def __init__(self, token_counter: TokenCounter = None):
        self.counter = token_counter or TokenCounter()

    def get_limit(self, model: str, reserve_output: int = 4096) -> int:
        """Get context limit for a model, reserving space for output."""
        limit = MODEL_LIMITS.get(model, DEFAULT_LIMIT)
        return max(limit - reserve_output, 1000)

    def check_context(
        self,
        content: str,
        model: str = "gpt-4o"
    ) -> tuple[bool, int, int]:
        """
        Check if content fits in context window.
        Returns: (fits, token_count, limit)
        """
        tokens = self.counter.count_tokens(content, model)
        limit = self.get_limit(model)
        return tokens <= limit, tokens, limit

    def chunk_content(
        self,
        content: str,
        chunk_size: int = 2000,
        overlap: int = 200,
        model: str = "gpt-4o"
    ) -> list[ContextChunk]:
        """Split content into overlapping chunks."""
        chunks = []
        
        # Split by paragraphs first
        paragraphs = content.split("\n\n")
        current_chunk = ""
        current_tokens = 0
        chunk_index = 0
        
        for para in paragraphs:
            para_tokens = self.counter.count_tokens(para, model)
            
            if current_tokens + para_tokens > chunk_size and current_chunk:
                # Save current chunk
                chunks.append(ContextChunk(
                    content=current_chunk.strip(),
                    tokens=current_tokens,
                    index=chunk_index
                ))
                chunk_index += 1
                
                # Start new chunk with overlap
                if overlap > 0:
                    # Take last part of previous chunk
                    words = current_chunk.split()
                    overlap_words = words[-overlap:] if len(words) > overlap else words
                    current_chunk = " ".join(overlap_words) + "\n\n" + para
                else:
                    current_chunk = para
                current_tokens = self.counter.count_tokens(current_chunk, model)
            else:
                current_chunk += "\n\n" + para if current_chunk else para
                current_tokens += para_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append(ContextChunk(
                content=current_chunk.strip(),
                tokens=current_tokens,
                index=chunk_index
            ))
        
        return chunks

    def truncate_to_fit(
        self,
        content: str,
        model: str = "gpt-4o",
        strategy: str = "end"  # "end", "start", "middle"
    ) -> ManagedContext:
        """Truncate content to fit in context window."""
        limit = self.get_limit(model)
        original_tokens = self.counter.count_tokens(content, model)
        
        if original_tokens <= limit:
            return ManagedContext(
                chunks=[ContextChunk(content=content, tokens=original_tokens, index=0)],
                total_tokens=original_tokens,
                original_tokens=original_tokens,
                was_truncated=False
            )
        
        # Need to truncate
        words = content.split()
        
        if strategy == "end":
            # Keep beginning
            truncated = ""
            for i, word in enumerate(words):
                test = truncated + " " + word if truncated else word
                if self.counter.count_tokens(test, model) > limit - 50:  # Leave buffer
                    truncated += "\n\n[... content truncated ...]"
                    break
                truncated = test
        
        elif strategy == "start":
            # Keep end
            truncated = ""
            for word in reversed(words):
                test = word + " " + truncated if truncated else word
                if self.counter.count_tokens(test, model) > limit - 50:
                    truncated = "[... content truncated ...]\n\n" + truncated
                    break
                truncated = test
        
        else:  # middle
            # Keep beginning and end
            half_limit = (limit - 100) // 2
            beginning = ""
            for word in words:
                test = beginning + " " + word if beginning else word
                if self.counter.count_tokens(test, model) > half_limit:
                    break
                beginning = test
            
            ending = ""
            for word in reversed(words):
                test = word + " " + ending if ending else word
                if self.counter.count_tokens(test, model) > half_limit:
                    break
                ending = test
            
            truncated = beginning + "\n\n[... content truncated ...]\n\n" + ending
        
        final_tokens = self.counter.count_tokens(truncated, model)
        
        return ManagedContext(
            chunks=[ContextChunk(content=truncated, tokens=final_tokens, index=0)],
            total_tokens=final_tokens,
            original_tokens=original_tokens,
            was_truncated=True
        )

    def summarize_for_context(
        self,
        content: str,
        target_tokens: int = 1000,
        model: str = "gpt-4o"
    ) -> str:
        """
        Create a summary prompt for content that's too long.
        Returns a prompt that asks the LLM to summarize.
        """
        return f"""Please summarize the following content in approximately {target_tokens} tokens, 
preserving the key information and main points:

{content}

Summary:"""

    def create_conversation_context(
        self,
        messages: list[dict],
        model: str = "gpt-4o",
        max_messages: int = None
    ) -> list[dict]:
        """
        Manage conversation history to fit in context.
        Keeps most recent messages, summarizes older ones if needed.
        """
        limit = self.get_limit(model)
        
        # Calculate tokens for all messages
        total_tokens = 0
        message_tokens = []
        for msg in messages:
            tokens = self.counter.count_tokens(msg.get("content", ""), model)
            message_tokens.append(tokens)
            total_tokens += tokens
        
        if total_tokens <= limit:
            return messages if not max_messages else messages[-max_messages:]
        
        # Need to trim - keep system message and recent messages
        result = []
        current_tokens = 0
        
        # Always keep system message if present
        if messages and messages[0].get("role") == "system":
            result.append(messages[0])
            current_tokens += message_tokens[0]
            messages = messages[1:]
            message_tokens = message_tokens[1:]
        
        # Add messages from most recent, going backwards
        for msg, tokens in zip(reversed(messages), reversed(message_tokens)):
            if current_tokens + tokens > limit:
                # Add truncation notice
                result.insert(1 if result and result[0].get("role") == "system" else 0, {
                    "role": "system",
                    "content": "[Earlier conversation history truncated due to length]"
                })
                break
            result.insert(1 if result and result[0].get("role") == "system" else 0, msg)
            current_tokens += tokens
        
        return result

    def estimate_response_tokens(
        self,
        prompt: str,
        model: str = "gpt-4o"
    ) -> dict:
        """Estimate token usage for a prompt."""
        prompt_tokens = self.counter.count_tokens(prompt, model)
        limit = self.get_limit(model)
        available = limit - prompt_tokens
        
        return {
            "prompt_tokens": prompt_tokens,
            "context_limit": limit,
            "available_for_response": max(available, 0),
            "fits": prompt_tokens < limit,
            "utilization": round(prompt_tokens / limit * 100, 1)
        }
