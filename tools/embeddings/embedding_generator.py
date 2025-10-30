"""
Embedding Generation Module

Generate vector embeddings for entities using OpenAI or other providers.
Automatically tracks model usage, versions embeddings, and updates quality scores.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import time

sys.path.append(str(Path(__file__).parent.parent))

from db_utils import (
    execute_query, execute_many, generate_uuid, update_quality_score
)


class EmbeddingGenerator:
    """Generate and manage vector embeddings for entities."""
    
    def __init__(self, provider: str = 'openai', model: str = 'text-embedding-3-small'):
        """
        Initialize embedding generator.
        
        Args:
            provider: 'openai' or other providers
            model: Model name (default: text-embedding-3-small, 1536 dimensions)
        """
        self.provider = provider
        self.model = model
        self.dimensions = 1536
        self.api_key = None
        self.client = None
        
        if provider == 'openai':
            self.api_key = os.environ.get('OPENAI_API_KEY')
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not set. Please set your API key.")
            
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("OpenAI package not installed. Run: uv add openai")
        
        # Register model in database
        self.model_id = self._register_model()
        
        self.stats = {
            'generated': 0,
            'updated': 0,
            'errors': [],
            'api_calls': 0,
            'tokens_used': 0
        }
    
    def _register_model(self) -> str:
        """Register embedding model in database."""
        query = """
            SELECT model_id FROM embedding_models
            WHERE provider = %s AND model_name = %s
        """
        result = execute_query(query, (self.provider, self.model))
        
        if result and len(result) > 0:
            return str(result[0]['model_id'])
        
        # Create new model registration
        model_id = generate_uuid()
        insert_query = """
            INSERT INTO embedding_models (
                model_id, provider, model_name, dimensions,
                cost_per_1k_tokens, max_input_tokens
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING model_id
        """
        
        # Default costs for common models
        cost_map = {
            'text-embedding-3-small': 0.00002,
            'text-embedding-3-large': 0.00013,
            'text-embedding-ada-002': 0.00010
        }
        cost = cost_map.get(self.model, 0.0001)
        
        result = execute_query(
            insert_query,
            (model_id, self.provider, self.model, self.dimensions, cost, 8191)
        )
        if result:
            return str(result[0]['model_id'])
        return model_id
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if self.provider == 'openai':
            response = self.client.embeddings.create(
                model=self.model,
                input=text.strip()
            )
            self.stats['api_calls'] += 1
            self.stats['tokens_used'] += response.usage.total_tokens
            
            return response.data[0].embedding
        else:
            raise ValueError(f"Provider {self.provider} not supported yet")
    
    def generate_entity_embedding(
        self,
        entity_id: str,
        text: str,
        invalidate_old: bool = True
    ) -> Dict[str, Any]:
        """
        Generate embedding for an entity and store in database.
        
        Args:
            entity_id: UUID of entity in standards_entities
            text: Text to generate embedding from
            invalidate_old: Set old embeddings to is_current=false
            
        Returns:
            Dict with embedding_id and success status
        """
        try:
            # Generate embedding
            embedding = self._generate_embedding(text)
            
            # Invalidate old embeddings if requested
            if invalidate_old:
                update_query = """
                    UPDATE entity_embeddings
                    SET is_current = false
                    WHERE entity_id = %s AND is_current = true
                """
                execute_query(update_query, (entity_id,), fetch=False)
            
            # Insert new embedding
            embedding_id = generate_uuid()
            insert_query = """
                INSERT INTO entity_embeddings (
                    embedding_id, entity_id, model_id, embedding,
                    is_current, embedding_version, quality_score
                ) VALUES (%s, %s, %s, %s, true, 1, 0.9)
                RETURNING embedding_id
            """
            
            result = execute_query(
                insert_query,
                (embedding_id, entity_id, self.model_id, embedding)
            )
            
            self.stats['generated'] += 1
            
            # Update entity quality score
            update_quality_score(entity_id, 10, 10)
            
            if result:
                return {'embedding_id': str(result[0]['embedding_id']), 'success': True}
            return {'embedding_id': embedding_id, 'success': True}
            
        except Exception as e:
            self.stats['errors'].append(f"Error for entity {entity_id}: {str(e)}")
            return {'embedding_id': None, 'success': False, 'error': str(e)}
    
    def generate_batch_embeddings(
        self,
        entity_ids: List[str],
        text_map: Dict[str, str],
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Generate embeddings for multiple entities in batches.
        
        Args:
            entity_ids: List of entity UUIDs
            text_map: Dict mapping entity_id to text
            batch_size: Number of entities to process at once
            
        Returns:
            Statistics dict
        """
        self.stats = {'generated': 0, 'updated': 0, 'errors': [], 'api_calls': 0, 'tokens_used': 0}
        
        for i in range(0, len(entity_ids), batch_size):
            batch = entity_ids[i:i + batch_size]
            print(f"Processing batch {i // batch_size + 1}/{(len(entity_ids) + batch_size - 1) // batch_size}")
            
            for entity_id in batch:
                text = text_map.get(entity_id, '')
                if text:
                    self.generate_entity_embedding(entity_id, text)
                else:
                    self.stats['errors'].append(f"No text for entity {entity_id}")
            
            # Rate limiting
            time.sleep(1)
        
        return self.stats
    
    def generate_for_table(
        self,
        table_name: str,
        text_columns: List[str],
        entity_id_column: str = 'entity_id',
        where_clause: str = ''
    ) -> Dict[str, Any]:
        """
        Generate embeddings for all entities in a table.
        
        Args:
            table_name: Name of table
            text_columns: List of columns to combine for embedding text
            entity_id_column: Name of entity_id column
            where_clause: Optional WHERE clause (e.g., "WHERE entity_id IS NOT NULL")
            
        Returns:
            Statistics dict
        """
        # Build query to get entities and text
        text_select = " || ' ' || ".join([f"COALESCE({col}::text, '')" for col in text_columns])
        query = f"""
            SELECT {entity_id_column} as entity_id,
                   {text_select} as text
            FROM {table_name}
            {where_clause}
        """
        
        results = execute_query(query)
        if not results:
            print(f"No entities found in {table_name}")
            return self.stats
        
        print(f"Found {len(results)} entities in {table_name}")
        
        # Build text map
        text_map = {row['entity_id']: row['text'] for row in results if row['entity_id']}
        entity_ids = list(text_map.keys())
        
        # Generate embeddings
        return self.generate_batch_embeddings(entity_ids, text_map)
    
    def refresh_embeddings(
        self,
        entity_ids: Optional[List[str]] = None,
        older_than_days: int = 30
    ) -> Dict[str, Any]:
        """
        Refresh embeddings that are old or missing.
        
        Args:
            entity_ids: Optional list of specific entity IDs to refresh
            older_than_days: Refresh embeddings older than this many days
            
        Returns:
            Statistics dict
        """
        if entity_ids:
            entity_list = ','.join([f"'{e}'" for e in entity_ids])
            where_clause = f"WHERE entity_id = ANY(ARRAY[{entity_list}]::uuid[])"
        else:
            where_clause = f"""
                WHERE entity_id NOT IN (
                    SELECT entity_id FROM entity_embeddings
                    WHERE is_current = true
                    AND created_at > CURRENT_TIMESTAMP - INTERVAL '{older_than_days} days'
                )
            """
        
        # Get entities needing refresh from standards_entities
        query = f"""
            SELECT entity_id, canonical_name, entity_type
            FROM standards_entities
            {where_clause}
        """
        
        results = execute_query(query)
        if not results:
            print("No entities need embedding refresh")
            return self.stats
        
        print(f"Refreshing embeddings for {len(results)} entities")
        
        # Build text map
        text_map = {row['entity_id']: f"{row['entity_type']}: {row['canonical_name']}" for row in results}
        entity_ids_to_refresh = list(text_map.keys())
        
        return self.generate_batch_embeddings(entity_ids_to_refresh, text_map)


if __name__ == '__main__':
    # Example usage
    print("Embedding Generator Example")
    print("=" * 50)
    
    # Check if API key is set
    if not os.environ.get('OPENAI_API_KEY'):
        print("ERROR: OPENAI_API_KEY not set")
        print("Please set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)
    
    # Initialize generator
    generator = EmbeddingGenerator(provider='openai', model='text-embedding-3-small')
    print(f"Using model: {generator.model} (ID: {generator.model_id})")
    print()
    
    # Example: Generate embeddings for layer standards
    print("Generating embeddings for layer_standards...")
    stats = generator.generate_for_table(
        table_name='layer_standards',
        text_columns=['name', 'description'],
        where_clause='WHERE entity_id IS NOT NULL LIMIT 10'
    )
    
    print()
    print("Results:")
    print(f"  Generated: {stats['generated']}")
    print(f"  API Calls: {stats['api_calls']}")
    print(f"  Tokens Used: {stats['tokens_used']}")
    print(f"  Errors: {len(stats['errors'])}")
    if stats['errors']:
        for error in stats['errors'][:5]:
            print(f"    - {error}")
