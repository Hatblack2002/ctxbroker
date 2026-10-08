#!/usr/bin/env python3
"""Command-line interface for ctxbroker."""

import argparse
import json
from pathlib import Path
from typing import List

from .db import Database
from .indexer import Indexer
from .search import Searcher

DEFAULT_EXTENSIONS = ['.ts', '.js', '.tsx', '.jsx', '.py', '.go', '.rs']

class CtxBrokerCLI:
    """Main CLI class for ctxbroker."""

    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Lightweight code search for Termux")
        self._setup_parser()

    def _setup_parser(self):
        subparsers = self.parser.add_subparsers(dest='command', required=True, help="Command to execute")

        # Query command
        query_parser = subparsers.add_parser('query', help="Search for code snippets")
        query_parser.add_argument('query', help="Text to search for")
        query_parser.add_argument('--project', required=True, help="Path to project directory")
        query_parser.add_argument('--limit', type=int, default=10, help="Maximum number of results (default: 10)")
        query_parser.add_argument('--context', type=int, default=1, help="Number of context lines (default: 1)")
        query_parser.add_argument('--pretty', action='store_true', help="Output pretty JSON with indentation")

        # Init command
        init_parser = subparsers.add_parser('init', help="Initialize database for a project")
        init_parser.add_argument('--project', required=True, help="Path to project directory")

        # Index command
        index_parser = subparsers.add_parser('index', help="Index a project")
        index_parser.add_argument('--project', required=True, help="Path to project directory")
        index_parser.add_argument('--ext', nargs='+', default=DEFAULT_EXTENSIONS,
                                 help=f"File extensions to index (default: {' '.join(DEFAULT_EXTENSIONS)})")

        # Rebuild command
        rebuild_parser = subparsers.add_parser('rebuild', help="Rebuild index for a project")
        rebuild_parser.add_argument('--project', required=True, help="Path to project directory")
        rebuild_parser.add_argument('--ext', nargs='+', default=DEFAULT_EXTENSIONS,
                                 help=f"File extensions to index (default: {' '.join(DEFAULT_EXTENSIONS)})")

    def _validate_project_path(self, project_path: str) -> Path:
        """Validate and return the project path."""
        path = Path(project_path).resolve()
        if not path.exists():
            raise ValueError(f"Project path does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"Project path is not a directory: {path}")
        return path

    def _get_db_path(self, project_path: Path) -> Path:
        """Get the database path for a project."""
        return project_path / ".ctxbroker" / "index.db"

    def run(self):
        """Run the CLI."""
        args = self.parser.parse_args()

        try:
            if args.command == 'init':
                project_path = self._validate_project_path(args.project)
                db_path = self._get_db_path(project_path)
                with Database(db_path) as db:
                    db.create_schema()
                print(f"Initialized database at {db_path}")

            elif args.command == 'index':
                project_path = self._validate_project_path(args.project)
                db_path = self._get_db_path(project_path)
                indexer = Indexer(db_path)
                indexer.index_project(project_path, args.ext)
                print(f"Indexed {project_path} with extensions: {', '.join(args.ext)}")

            elif args.command == 'rebuild':
                project_path = self._validate_project_path(args.project)
                db_path = self._get_db_path(project_path)
                indexer = Indexer(db_path)
                indexer.rebuild_project(project_path, args.ext)
                print(f"Rebuilt index for {project_path} with extensions: {', '.join(args.ext)}")

            elif args.command == 'query':
                project_path = self._validate_project_path(args.project)
                db_path = self._get_db_path(project_path)
                try:
                    searcher = Searcher(db_path)
                    results = searcher.search(args.query, args.limit, args.context)
                    if not results.get('results', []):
                        if not list(Path(db_path.parent).glob('index.db')):
                            print("Error: no index found for this project.")
                            print("Run: ctxbroker index --project <path> --ext <exts>")
                            exit(1)
                    indent = 2 if args.pretty else None
                    print(json.dumps(results, indent=indent))
                except sqlite3.OperationalError as e:
                    if "no such table" in str(e):
                        print("Error: no index found for this project.")
                        print("Run: ctxbroker index --project <path> --ext <exts>")
                        exit(1)
                    raise

        except Exception as e:
            print(f"Error: {str(e)}")
            exit(1)

def main():
    """Main CLI entry point."""
    cli = CtxBrokerCLI()
    cli.run()

if __name__ == '__main__':
    main()