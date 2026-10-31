"""Search history manager"""

import json
import os
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
from loguru import logger


class HistoryManager:
    """Manages search history storage and retrieval"""

    def __init__(self, history_file: str = "data/search_history.json"):
        """Initialize history manager

        Args:
            history_file: Path to history JSON file
        """
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing history
        self.history = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load history from file

        Returns:
            List of history entries
        """
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("history file does not contain a list")
                return data
            except Exception as e:
                backup = self.history_file.with_name(self.history_file.stem + '.corrupt.json')
                try:
                    os.replace(str(self.history_file), str(backup))
                    logger.error(f"Failed to load history ({e}); moved the unreadable file to {backup}")
                except OSError:
                    logger.error(f"Failed to load history ({e})")
                return []
        return []

    def _save_history(self):
        """Save history to file (atomic write via temp file)"""
        import os
        try:
            tmp = self.history_file.with_suffix('.tmp')
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
            os.replace(str(tmp), str(self.history_file))
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def add_search(self, query: str, result: Dict[str, Any], sources: List[str]):
        """Add a search to history

        Args:
            query: Search query
            result: Research result
            sources: Data sources used
        """
        max_id = max((e.get('id', 0) for e in self.history), default=0)
        entry = {
            'id': max_id + 1,
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'sources': sources,
            'papers_found': result.get('papers_found', 0),
            'papers_analyzed': result.get('papers_analyzed', 0),
            'confidence': result.get('metadata', {}).get('average_confidence', 0),
            'literature_review_preview': result.get('literature_review', '')[:200] + '...'
        }

        self.history.append(entry)
        self._save_history()
        logger.info(f"Added search to history: {query}")

    def get_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get search history

        Args:
            limit: Optional limit on number of entries

        Returns:
            List of history entries (most recent first)
        """
        history = sorted(self.history, key=lambda x: x.get('timestamp', ''), reverse=True)
        if limit:
            return history[:limit]
        return history

    def get_search_by_id(self, search_id: int) -> Dict[str, Any]:
        """Get a specific search by ID

        Args:
            search_id: Search ID

        Returns:
            Search entry or None
        """
        for entry in self.history:
            if entry.get('id') == search_id:
                return entry
        return None

    def delete_search(self, search_id: int) -> bool:
        """Delete a search from history

        Args:
            search_id: Search ID

        Returns:
            True if deleted, False otherwise
        """
        original_len = len(self.history)
        self.history = [e for e in self.history if e.get('id') != search_id]

        if len(self.history) < original_len:
            self._save_history()
            logger.info(f"Deleted search {search_id} from history")
            return True

        return False

    def clear_history(self):
        """Clear all history"""
        self.history = []
        self._save_history()
        logger.info("Cleared all search history")

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about search history

        Returns:
            Dictionary of statistics
        """
        if not self.history:
            return {
                'total_searches': 0,
                'total_papers_found': 0,
                'total_papers_analyzed': 0,
                'average_confidence': 0,
                'most_used_sources': [],
                'recent_queries': []
            }

        total_papers_found = sum(e.get('papers_found', 0) for e in self.history)
        total_papers_analyzed = sum(e.get('papers_analyzed', 0) for e in self.history)
        avg_confidence = sum(e.get('confidence', 0) for e in self.history) / len(self.history)

        # Count source usage
        source_counts = {}
        for entry in self.history:
            for source in entry.get('sources', []):
                source_counts[source] = source_counts.get(source, 0) + 1

        # Sort by usage
        most_used = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Recent queries
        recent = [e.get('query') for e in sorted(
            self.history,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )[:10]]

        return {
            'total_searches': len(self.history),
            'total_papers_found': total_papers_found,
            'total_papers_analyzed': total_papers_analyzed,
            'average_confidence': round(avg_confidence, 2),
            'most_used_sources': [{'source': s, 'count': c} for s, c in most_used],
            'recent_queries': recent
        }
