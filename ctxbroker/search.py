#!/usr/bin/env python3
"""Search module for ctxbroker."""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any

class Searcher:
    """Handles searching through the database and formatting results."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def _normalize_score(self, raw_score: float, max_score: float) -> float:
        """Normalize a raw score to a 0-1 range."""
        if max_score == 0:
            return 0.0
        return min(1.0, max(0.0, raw_score / max_score))

    def search(self, query: str, limit: int = 10, context: int = 1) -> Dict[str, Any]:
        """Search for code snippets matching query.

        Args:
            query: Text to search for
            limit: Maximum number of results to return
            context: Number of lines of context to include

        Returns:
            Dict with search results in the required JSON format
        """
        conn = sqlite3.connect(str(self.db_path))

        try:
            # Execute FTS5 search with BM25 ranking
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    s.id, s.line, s.content,
                    f.path AS file_path,
                    bm25(snippets_fts) AS raw_score
                FROM snippets_fts
                JOIN snippets s ON s.id = snippets_fts.rowid
                JOIN files f ON f.id = s.file_id
                WHERE snippets_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))

            rows = cursor.fetchall()

            if not rows:
                return {
                    "query": query,
                    "results": []
                }

            # Get max score for normalization
            max_score = max(row[4] for row in rows)

            # Format results
            results = []
            for row in rows:
                snippet_id, line, content, file_path, raw_score = row

                # Get surrounding lines of context
                start_line = max(1, line - context)
                end_line = line + context

                # Get all lines from the file
                file_path = Path(file_path)
                try:
                    file_content = file_path.read_text(errors='ignore')
                    lines = file_content.splitlines()

                    # Get context lines
                    context_lines = {
                        "before": lines[start_line-1:line-1],
                        "after": lines[line:end_line]
                    }

                    # Format result
                    results.append({
                        "id": snippet_id,
                        "file": str(file_path.absolute()),
                        "line": line,
                        "snippet": content,
                        "context": context_lines,
                        "score": self._normalize_score(raw_score, max_score)
                    })
                except Exception as e:
                    print(f"Error reading file {file_path}: {str(e)}")
                    continue

            # Calculate total_matches
            total_matches = len(rows)

            # Calculate tokens_estimated
            tokens_estimated = sum(
                len(result['snippet']) +
                sum(len(line) for line in result['context']['before']) +
                sum(len(line) for line in result['context']['after'])
                for result in results
            ) // 4

            return {
                "query": query,
                "project": str(self.db_path.parent.absolute()),
                "total_matches": total_matches,
                "returned": len(results),
                "tokens_estimated": tokens_estimated,
                "results": results
            }
        except Exception as e:
            raise RuntimeError(f"Search failed: {str(e)}")
        finally:
            conn.close()