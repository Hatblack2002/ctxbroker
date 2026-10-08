#!/usr/bin/env python3
"""Indexer module for ctxbroker."""

import re
import subprocess
import sqlite3
import os
from pathlib import Path
from typing import List, Tuple
from .db import Database

class Indexer:
    """Handles indexing of code files using ripgrep and SQLite."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_rigrep_output(self, project_path: Path, file_exts: List[str]) -> List[Tuple[str, int, str]]:
        """Get file content from ripgrep output.

        Args:
            project_path: Path to the project directory
            file_exts: List of file extensions to index (e.g., ['.ts', '.js'])

        Returns:
            List of tuples (file_path, line_number, line_content)
        """
        # Build ripgrep command to get file paths
        cmd = ['rg', '--files', '--sort', 'path']
        for ext in file_exts:
            cmd.extend(['--glob', f'*{ext}'])
        cmd.append(str(project_path))

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode not in (0, 1):
            raise RuntimeError(f"ripgrep failed: {result.stderr}")

        # Parse ripgrep output to get file paths
        file_paths = [path for path in result.stdout.strip().split('\n') if path]

        parsed_lines = []
        for file_path in file_paths:
            file_path = Path(file_path)
            if not file_path.is_file():
                continue

            try:
                content = file_path.read_text(errors='ignore')
                for line_number, line in enumerate(content.splitlines(), start=1):
                    parsed_lines.append((str(file_path.absolute()), line_number, line))
            except Exception as e:
                print(f"Error reading file {file_path}: {str(e)}")
                continue

        return parsed_lines

    def index_project(self, project_path: Path, file_exts: List[str]):
        """Index a project directory.

        Args:
            project_path: Path to the project directory
            file_exts: List of file extensions to index
        """
        with Database(self.db_path) as db:
            db.create_schema()
            conn = db.get_connection()
            cursor = conn.cursor()

            try:
                # Delete existing data for this project
                cursor.execute(
                    "DELETE FROM files WHERE path GLOB ?",
                    (f"{str(project_path.absolute())}/*",)
                )

                # Get file content from ripgrep
                file_data = self._get_rigrep_output(project_path, file_exts)

                # Insert files
                for file_path, _, _ in file_data:
                    file_path = str(Path(file_path).absolute())
                    mtime = int(os.path.getmtime(file_path))
                    size = os.path.getsize(file_path)
                    cursor.execute(
                        "INSERT OR REPLACE INTO files (path, mtime, size) VALUES (?, ?, ?)",
                        (file_path, mtime, size)
                    )

                # Insert snippets
                for file_path, line_number, content in file_data:
                    file_path = str(Path(file_path).absolute())
                    cursor.execute(
                        "SELECT id FROM files WHERE path = ?",
                        (file_path,)
                    )
                    file_id = cursor.fetchone()[0]

                    cursor.execute(
                        "INSERT INTO snippets (file_id, line, content) VALUES (?, ?, ?)",
                        (file_id, line_number, content)
                    )

                conn.commit()
            except Exception as e:
                conn.rollback()
                raise RuntimeError(f"Indexing failed: {str(e)}")

    def rebuild_project(self, project_path: Path, file_exts: List[str]):
        """Rebuild the index for a project.

        Args:
            project_path: Path to the project directory
            file_exts: List of file extensions to index
        """
        with Database(self.db_path) as db:
            conn = db.get_connection()
            cursor = conn.cursor()

            try:
                # Drop tables
                cursor.execute("DROP TABLE IF EXISTS snippets")
                cursor.execute("DROP TABLE IF EXISTS files")

                # Rebuild index
                self.index_project(project_path, file_exts)
            except Exception as e:
                conn.rollback()
                raise RuntimeError(f"Rebuild failed: {str(e)}")