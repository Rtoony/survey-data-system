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
    
    def __init__(
        self, 
        provider: str = 'openai', 
        model: str = 'text-embedding-3-small',
        budget_cap: float = 100.0,
        dry_run: bool = False
    ):
        """
        Initialize embedding generator.
        
        Args:
            provider: 'openai' or other providers
            model: Model name (default: text-embedding-3-small, 1536 dimensions)
            budget_cap: Maximum total cost in USD (default: $100)
            dry_run: If True, preview costs without generating embeddings
        """
        self.provider = provider
        self.model = model
        self.dimensions = 1536
        self.api_key = None
        self.client = None
        self.budget_cap = budget_cap
        self.dry_run = dry_run
        
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
        
        # Get current cumulative cost from database
        self.cumulative_cost = self._get_cumulative_cost()
        
        self.stats = {
            'generated': 0,
            'updated': 0,
            'errors': [],
            'api_calls': 0,
            'tokens_used': 0,
            'estimated_cost': 0.0,
            'cumulative_cost': self.cumulative_cost,
            'budget_remaining': self.budget_cap - self.cumulative_cost
        }
        
        # Check if already over budget
        if self.cumulative_cost >= self.budget_cap:
            raise ValueError(
                f"Budget cap already exceeded! "
                f"Cumulative cost: ${self.cumulative_cost:.2f}, "
                f"Budget cap: ${self.budget_cap:.2f}. "
                f"Increase budget_cap or reset costs in database."
            )
    
    def _get_cumulative_cost(self) -> float:
        """Get total cumulative cost from database."""
        query = """
            SELECT COALESCE(SUM(
                (usage_stats->>'tokens_used')::integer * 
                cost_per_1k_tokens / 1000
            ), 0.0) AS total_cost
            FROM embedding_models
            WHERE provider = %s AND model_name = %s
        """
        result = execute_query(query, (self.provider, self.model))
        if result and len(result) > 0:
            return float(result[0]['total_cost'])
        return 0.0
    
    def _check_budget(self, estimated_tokens: int) -> None:
        """
        Check if operation would exceed budget.
        
        Raises:
            ValueError: If operation would exceed budget cap
        """
        # Get cost per 1k tokens
        query = """
            SELECT cost_per_1k_tokens FROM embedding_models
            WHERE model_id = %s::uuid
        """
        result = execute_query(query, (self.model_id,))
        cost_per_1k = float(result[0]['cost_per_1k_tokens']) if result else 0.00002
        
        # Calculate estimated cost for this operation
        operation_cost = (estimated_tokens / 1000) * cost_per_1k
        projected_total = self.stats['cumulative_cost'] + operation_cost
        
        # Check thresholds
        if projected_total >= self.budget_cap:
            raise ValueError(
                f"🛑 BUDGET CAP REACHED!\n"
                f"   Current: ${self.stats['cumulative_cost']:.2f}\n"
                f"   This operation: ${operation_cost:.2f}\n"
                f"   Projected total: ${projected_total:.2f}\n"
                f"   Budget cap: ${self.budget_cap:.2f}\n"
                f"   Would exceed budget by: ${projected_total - self.budget_cap:.2f}"
            )
        
        # Warnings at $50, $75, $90
        if projected_total >= 90 and self.stats['cumulative_cost'] < 90:
            print(f"⚠️  WARNING: Approaching budget cap! ${projected_total:.2f} / ${self.budget_cap:.2f}")
        elif projected_total >= 75 and self.stats['cumulative_cost'] < 75:
            print(f"⚠️  WARNING: 75% of budget used. ${projected_total:.2f} / ${self.budget_cap:.2f}")
        elif projected_total >= 50 and self.stats['cumulative_cost'] < 50:
            print(f"ℹ️  INFO: 50% of budget used. ${projected_total:.2f} / ${self.budget_cap:.2f}")
    
    def _update_cost_tracking(self, tokens_used: int) -> None:
        """Update cost tracking in database and stats."""
        # Get cost per 1k tokens
        query = """
            SELECT cost_per_1k_tokens FROM embedding_models
            WHERE model_id = %s::uuid
        """
        result = execute_query(query, (self.model_id,))
        cost_per_1k = float(result[0]['cost_per_1k_tokens']) if result else 0.00002
        
        operation_cost = (tokens_used / 1000) * cost_per_1k
        
        # Update database
        update_query = """
            UPDATE embedding_models
            SET usage_stats = COALESCE(usage_stats, '{}'::jsonb) || 
                jsonb_build_object(
                    'tokens_used', 
                    COALESCE((usage_stats->>'tokens_used')::integer, 0) + %s,
                    'last_updated',
                    CURRENT_TIMESTAMP::text
                )
            WHERE model_id = %s::uuid
        """
        execute_query(update_query, (tokens_used, self.model_id))
        
        # Update stats
        self.stats['estimated_cost'] += operation_cost
        self.stats['cumulative_cost'] += operation_cost
        self.stats['budget_remaining'] = self.budget_cap - self.stats['cumulative_cost']
    
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
        # Reset stats but preserve cumulative cost
        cumulative = self.stats['cumulative_cost']
        budget_remaining = self.stats['budget_remaining']
        self.stats = {
            'generated': 0, 
            'updated': 0, 
            'errors': [], 
            'api_calls': 0, 
            'tokens_used': 0,
            'estimated_cost': 0.0,
            'cumulative_cost': cumulative,
            'budget_remaining': budget_remaining
        }
        
        # Estimate tokens for budget check
        total_text_length = sum(len(text_map.get(eid, '')) for eid in entity_ids)
        estimated_tokens = int(total_text_length * 0.4)  # Rough estimate: 1 token ~= 2.5 chars
        
        # DRY RUN MODE
        if self.dry_run:
            query = """
                SELECT cost_per_1k_tokens FROM embedding_models
                WHERE model_id = %s::uuid
            """
            result = execute_query(query, (self.model_id,))
            cost_per_1k = float(result[0]['cost_per_1k_tokens']) if result else 0.00002
            estimated_cost = (estimated_tokens / 1000) * cost_per_1k
            
            print(f"\n{'='*60}")
            print(f"🔍 DRY RUN MODE - No embeddings will be generated")
            print(f"{'='*60}")
            print(f"Entities to process: {len(entity_ids)}")
            print(f"Estimated tokens: {estimated_tokens:,}")
            print(f"Estimated cost: ${estimated_cost:.4f}")
            print(f"Current cumulative: ${cumulative:.2f}")
            print(f"Projected total: ${cumulative + estimated_cost:.2f}")
            print(f"Budget cap: ${self.budget_cap:.2f}")
            print(f"Budget remaining after: ${self.budget_cap - (cumulative + estimated_cost):.2f}")
            print(f"{'='*60}\n")
            
            self.stats['estimated_cost'] = estimated_cost
            return self.stats
        
        # BUDGET CHECK
        try:
            self._check_budget(estimated_tokens)
        except ValueError as e:
            print(str(e))
            raise
        
        print(f"\n{'='*60}")
        print(f"Starting embedding generation:")
        print(f"  Entities: {len(entity_ids)}")
        print(f"  Estimated tokens: {estimated_tokens:,}")
        print(f"  Current budget: ${self.stats['cumulative_cost']:.2f} / ${self.budget_cap:.2f}")
        print(f"  Budget remaining: ${self.stats['budget_remaining']:.2f}")
        print(f"{'='*60}\n")
        
        for i in range(0, len(entity_ids), batch_size):
            batch = entity_ids[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(entity_ids) + batch_size - 1) // batch_size
            
            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} entities)")
            
            for entity_id in batch:
                text = text_map.get(entity_id, '')
                if text:
                    self.generate_entity_embedding(entity_id, text)
                else:
                    self.stats['errors'].append(f"No text for entity {entity_id}")
            
            # Update cost tracking after each batch
            if self.stats['tokens_used'] > 0:
                self._update_cost_tracking(self.stats['tokens_used'])
                self.stats['tokens_used'] = 0  # Reset for next batch
            
            print(f"  Progress: {self.stats['generated']} generated, "
                  f"${self.stats['cumulative_cost']:.2f} spent, "
                  f"${self.stats['budget_remaining']:.2f} remaining")
            
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
    
    def reset_cost_tracking(self) -> None:
        """
        Reset cost tracking in database to zero.
        
        WARNING: This resets the cumulative cost counter. Use only when starting
        a new budget period or after billing reconciliation.
        """
        update_query = """
            UPDATE embedding_models
            SET usage_stats = jsonb_build_object(
                'tokens_used', 0,
                'last_reset', CURRENT_TIMESTAMP::text,
                'reset_by', CURRENT_USER
            )
            WHERE model_id = %s::uuid
        """
        execute_query(update_query, (self.model_id,), fetch=False)
        
        self.cumulative_cost = 0.0
        self.stats['cumulative_cost'] = 0.0
        self.stats['budget_remaining'] = self.budget_cap
        
        print(f"✓ Cost tracking reset to $0.00 for model {self.model}")
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get current cost and budget summary."""
        return {
            'cumulative_cost': self.stats['cumulative_cost'],
            'budget_cap': self.budget_cap,
            'budget_remaining': self.stats['budget_remaining'],
            'budget_used_percent': (self.stats['cumulative_cost'] / self.budget_cap) * 100,
            'estimated_cost_this_session': self.stats.get('estimated_cost', 0.0),
            'model': self.model,
            'dry_run_mode': self.dry_run
        }


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
