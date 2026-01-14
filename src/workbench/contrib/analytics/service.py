"""
Prompt Analytics Dashboard - Track usage patterns and insights.
Feature #8: Prompt Analytics Dashboard
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import json

from src.platform.environment import get_config_dir


@dataclass
class UsageRecord:
    id: int
    timestamp: str
    technique: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: int
    success: bool
    tags: list[str]


@dataclass
class AnalyticsSummary:
    total_prompts: int
    total_tokens: int
    total_cost: float
    avg_latency_ms: float
    success_rate: float
    top_techniques: list[tuple[str, int]]
    top_models: list[tuple[str, int]]
    daily_usage: list[tuple[str, int]]
    cost_by_provider: dict[str, float]


class PromptAnalytics:
    """Track and analyze prompt usage."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(get_config_dir() / "analytics.db")
        
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize analytics database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    technique TEXT,
                    provider TEXT,
                    model TEXT,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    cost REAL DEFAULT 0,
                    latency_ms INTEGER DEFAULT 0,
                    success INTEGER DEFAULT 1,
                    tags TEXT DEFAULT ''
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON usage(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_technique ON usage(technique)")
            conn.commit()

    def record_usage(
        self,
        technique: str,
        provider: str = "",
        model: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0,
        latency_ms: int = 0,
        success: bool = True,
        tags: list[str] = None
    ) -> int:
        """Record a prompt usage event."""
        tags_str = ",".join(tags) if tags else ""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO usage (technique, provider, model, input_tokens, output_tokens, 
                                   cost, latency_ms, success, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (technique, provider, model, input_tokens, output_tokens, 
                  cost, latency_ms, 1 if success else 0, tags_str))
            conn.commit()
            return cursor.lastrowid

    def get_summary(self, days: int = 30) -> AnalyticsSummary:
        """Get analytics summary for the specified period."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Total stats
            row = conn.execute("""
                SELECT COUNT(*), SUM(input_tokens + output_tokens), SUM(cost),
                       AVG(latency_ms), AVG(success)
                FROM usage WHERE timestamp >= ?
            """, (since,)).fetchone()
            
            total_prompts = row[0] or 0
            total_tokens = row[1] or 0
            total_cost = row[2] or 0
            avg_latency = row[3] or 0
            success_rate = (row[4] or 0) * 100
            
            # Top techniques
            top_techniques = conn.execute("""
                SELECT technique, COUNT(*) as cnt
                FROM usage WHERE timestamp >= ?
                GROUP BY technique ORDER BY cnt DESC LIMIT 5
            """, (since,)).fetchall()
            
            # Top models
            top_models = conn.execute("""
                SELECT model, COUNT(*) as cnt
                FROM usage WHERE timestamp >= ? AND model != ''
                GROUP BY model ORDER BY cnt DESC LIMIT 5
            """, (since,)).fetchall()
            
            # Daily usage
            daily_usage = conn.execute("""
                SELECT DATE(timestamp) as day, COUNT(*)
                FROM usage WHERE timestamp >= ?
                GROUP BY day ORDER BY day DESC LIMIT 30
            """, (since,)).fetchall()
            
            # Cost by provider
            cost_rows = conn.execute("""
                SELECT provider, SUM(cost)
                FROM usage WHERE timestamp >= ? AND provider != ''
                GROUP BY provider
            """, (since,)).fetchall()
            cost_by_provider = {row[0]: row[1] for row in cost_rows}
        
        return AnalyticsSummary(
            total_prompts=total_prompts,
            total_tokens=total_tokens,
            total_cost=total_cost,
            avg_latency_ms=avg_latency,
            success_rate=success_rate,
            top_techniques=top_techniques,
            top_models=top_models,
            daily_usage=daily_usage,
            cost_by_provider=cost_by_provider
        )

    def get_technique_stats(self, technique: str, days: int = 30) -> dict:
        """Get detailed stats for a specific technique."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT COUNT(*), AVG(input_tokens + output_tokens), AVG(cost),
                       AVG(latency_ms), AVG(success)
                FROM usage WHERE technique = ? AND timestamp >= ?
            """, (technique, since)).fetchone()
            
            return {
                "technique": technique,
                "usage_count": row[0] or 0,
                "avg_tokens": row[1] or 0,
                "avg_cost": row[2] or 0,
                "avg_latency_ms": row[3] or 0,
                "success_rate": (row[4] or 0) * 100
            }

    def get_cost_breakdown(self, days: int = 30) -> dict:
        """Get detailed cost breakdown."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # By provider
            by_provider = conn.execute("""
                SELECT provider, SUM(cost), COUNT(*)
                FROM usage WHERE timestamp >= ? AND provider != ''
                GROUP BY provider
            """, (since,)).fetchall()
            
            # By model
            by_model = conn.execute("""
                SELECT model, SUM(cost), COUNT(*)
                FROM usage WHERE timestamp >= ? AND model != ''
                GROUP BY model
            """, (since,)).fetchall()
            
            # By day
            by_day = conn.execute("""
                SELECT DATE(timestamp), SUM(cost)
                FROM usage WHERE timestamp >= ?
                GROUP BY DATE(timestamp) ORDER BY DATE(timestamp)
            """, (since,)).fetchall()
        
        return {
            "by_provider": {row[0]: {"cost": row[1], "count": row[2]} for row in by_provider},
            "by_model": {row[0]: {"cost": row[1], "count": row[2]} for row in by_model},
            "by_day": {row[0]: row[1] for row in by_day}
        }

    def get_recent_usage(self, limit: int = 20) -> list[UsageRecord]:
        """Get recent usage records."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT id, timestamp, technique, provider, model, input_tokens,
                       output_tokens, cost, latency_ms, success, tags
                FROM usage ORDER BY timestamp DESC LIMIT ?
            """, (limit,)).fetchall()
        
        return [
            UsageRecord(
                id=row[0],
                timestamp=row[1],
                technique=row[2],
                provider=row[3],
                model=row[4],
                input_tokens=row[5],
                output_tokens=row[6],
                cost=row[7],
                latency_ms=row[8],
                success=bool(row[9]),
                tags=row[10].split(",") if row[10] else []
            )
            for row in rows
        ]

    def export_data(self, days: int = None) -> str:
        """Export analytics data as JSON."""
        query = "SELECT * FROM usage"
        params = ()
        
        if days:
            since = (datetime.now() - timedelta(days=days)).isoformat()
            query += " WHERE timestamp >= ?"
            params = (since,)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
        
        data = [dict(row) for row in rows]
        return json.dumps(data, indent=2)

    def clear_old_data(self, days: int = 90) -> int:
        """Clear data older than specified days."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM usage WHERE timestamp < ?", (since,))
            conn.commit()
            return cursor.rowcount
