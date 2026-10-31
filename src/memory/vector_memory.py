"""Vector memory system using ChromaDB"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from loguru import logger

from src.utils.config import settings


class VectorMemory:
    """Vector-based memory system for semantic search"""

    def __init__(self, collection_name: str = None, persist_directory: str = None):
        """Initialize vector memory

        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist the database
        """
        if collection_name is None:
            collection_name = settings.get('memory.vector_db.collection_name', 'research_papers')

        if persist_directory is None:
            persist_directory = settings.get('memory.vector_db.path', './data/chroma_db')

        # Create directory if it doesn't exist
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client (new API)
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Research papers and analyses"}
            )
            logger.info(f"Created new collection: {collection_name}")

        self.collection_name = collection_name

    def store(
        self,
        id: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store content with semantic embedding

        Args:
            id: Unique identifier
            content: Content to store (will be converted to string)
            metadata: Optional metadata dictionary
        """
        # Convert content to string if needed
        if isinstance(content, dict):
            text = json.dumps(content, indent=2)
            if metadata is None:
                metadata = {}
            metadata['type'] = 'dict'
        elif isinstance(content, (list, tuple)):
            text = json.dumps(content, indent=2)
            if metadata is None:
                metadata = {}
            metadata['type'] = 'list'
        else:
            text = str(content)

        if not text.strip():
            logger.warning(f"Empty content for id: {id}")
            return

        try:
            self.collection.upsert(
                ids=[id],
                documents=[text],
                metadatas=[metadata] if metadata else None
            )
            logger.debug(f"Stored in memory: {id}")
        except Exception as e:
            logger.error(f"Error storing in memory: {e}")

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar content

        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of results with content and metadata
        """
        if not query.strip():
            logger.warning("Empty search query")
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=filters
            )

            # Format results
            formatted_results = []
            if results and results['ids']:
                for i, doc_id in enumerate(results['ids'][0]):
                    result = {
                        'id': doc_id,
                        'content': results['documents'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None,
                        'metadata': results['metadatas'][0][i] if results.get('metadatas') else {}
                    }

                    # Try to parse JSON content back to dict
                    if result['metadata'].get('type') in ['dict', 'list']:
                        try:
                            result['content'] = json.loads(result['content'])
                        except:
                            pass

                    formatted_results.append(result)

            logger.debug(f"Found {len(formatted_results)} results for query: {query[:50]}...")
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching memory: {e}")
            return []

    def get(self, id: str) -> Optional[Dict[str, Any]]:
        """Get content by ID

        Args:
            id: Content identifier

        Returns:
            Content dictionary or None
        """
        try:
            result = self.collection.get(ids=[id])

            if result and result['ids']:
                content = result['documents'][0]
                metadata = result['metadatas'][0] if result.get('metadatas') else {}

                # Try to parse JSON content
                if metadata.get('type') in ['dict', 'list']:
                    try:
                        content = json.loads(content)
                    except:
                        pass

                return {
                    'id': id,
                    'content': content,
                    'metadata': metadata
                }

        except Exception as e:
            logger.error(f"Error getting from memory: {e}")

        return None

    def delete(self, id: str) -> None:
        """Delete content by ID

        Args:
            id: Content identifier
        """
        try:
            self.collection.delete(ids=[id])
            logger.debug(f"Deleted from memory: {id}")
        except Exception as e:
            logger.error(f"Error deleting from memory: {e}")

    def clear(self) -> None:
        """Clear all content from collection"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Research papers and analyses"}
            )
            logger.info(f"Cleared collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")

    def count(self) -> int:
        """Get number of items in collection

        Returns:
            Number of items
        """
        try:
            return self.collection.count()
        except:
            return 0

    def persist(self) -> None:
        """Persist the database to disk"""
        try:
            self.client.persist()
            logger.debug("Memory persisted to disk")
        except Exception as e:
            logger.error(f"Error persisting memory: {e}")
