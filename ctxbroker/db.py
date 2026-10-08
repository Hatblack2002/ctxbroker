#!/usr/bin/env python3
"""Core DB module for ctxbroker."""

import os
import sqlite3
from pathlib import Path
from typing import Optional
class Database:
    """SQLite database manager for file index and search."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection, creating one if necessary."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            # Enable FTS5 and foreign keys
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.execute("PRAGMA journal_mode = WAL")
        return self._conn

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def create_schema(self):
        """Create the full database schema with FTS5 and triggers."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Files table - basic file metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                mtime INTEGER,
                size INTEGER
            )
        """)

        # Snippets table - actual file content
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                line INTEGER NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """)

        # FTS5 virtual table for full-text search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS snippets_fts USING fts5(
                content,
                content='snippets',
                content_rowid='id',
                tokenize='unicode61'
            )
        """)

        # Trigger para insertar en snippets_fts
        cursor.executescript("""
            CREATE TRIGGER IF NOT EXISTS snippets_ai AFTER INSERT ON snippets
            BEGIN
                INSERT INTO snippets_fts(rowid, content)
                VALUES (NEW.id, NEW.content);
            END;
        """)

        # Trigger para eliminar en snippets_fts
        cursor.executescript("""
            CREATE TRIGGER IF NOT EXISTS snippets_ad AFTER DELETE ON snippets
            BEGIN
                INSERT INTO snippets_fts(snippets_fts, rowid, content)
                VALUES ('delete', OLD.id, OLD.content);
            END;
        """)

        # Trigger para actualizar en snippets_fts
        cursor.executescript("""
            CREATE TRIGGER IF NOT EXISTS snippets_au AFTER UPDATE ON snippets
            BEGIN
                INSERT INTO snippets_fts(snippets_fts, rowid, content)
                VALUES ('delete', OLD.id, OLD.content);
                INSERT INTO snippets_fts(rowid, content)
                VALUES (NEW.id, NEW.content);
            END;
        """)

        conn.commit()

    def init_project(self, project_path: Path):
        """Initialize database for a specific project."""
        db_file = project_path / '.ctxbroker.db'
        db = Database(db_file)
        db.create_schema()
        db.close()
        return db

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
