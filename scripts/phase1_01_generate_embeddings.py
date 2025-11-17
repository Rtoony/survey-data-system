#!/usr/bin/env python3
"""
Phase 1 - Task 1: Generate Embeddings for Layer Standards

This script generates vector embeddings for layer standards using OpenAI's API.
It includes cost estimation, budget caps, and progress tracking.

Usage:
    python scripts/phase1_01_generate_embeddings.py [--limit N] [--dry-run]

Options:
    --limit N     Generate embeddings for first N layers (default: 100)
    --dry-run     Estimate cost without making API calls
"""

import sys
import os
from pathlib import Path
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import psycopg2
from openai import OpenAI

# Load environment variables
load_dotenv()


class EmbeddingGenerator:
    """Generate embeddings for layer standards with cost tracking."""

    def __init__(self, dry_run=False, budget_cap=10.0):
        self.dry_run = dry_run
        self.budget_cap = budget_cap
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = 'text-embedding-3-small'
        self.dimensions = 1536
        self.cost_per_1k_tokens = 0.00002  # $0.02 per 1M tokens

        # Connect to database
        self.conn = psycopg2.connect(
            host=os.getenv('PGHOST') or os.getenv('DB_HOST'),
            port=int(os.getenv('PGPORT') or os.getenv('DB_PORT', 5432)),
            database=os.getenv('PGDATABASE') or os.getenv('DB_NAME'),
            user=os.getenv('PGUSER') or os.getenv('DB_USER'),
            password=os.getenv('PGPASSWORD') or os.getenv('DB_PASSWORD'),
            sslmode='require'
        )

        # Register model
        self.model_id = self._register_model()

    def _register_model(self):
        """Register the embedding model in the database."""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO embedding_models (
                model_name, provider, dimensions,
                cost_per_1k_tokens, max_input_tokens, is_active
            ) VALUES (
                %s, 'openai', %s, %s, 8191, TRUE
            )
            ON CONFLICT (model_name, provider)
            DO UPDATE SET is_active = TRUE
            RETURNING model_id
        """, (self.model, self.dimensions, self.cost_per_1k_tokens))

        model_id = cursor.fetchone()[0]
        self.conn.commit()
        cursor.close()

        return model_id

    def get_layers_to_embed(self, limit=100):
        """Get layers that need embeddings."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                ls.layer_id,
                ls.entity_id,
                ls.name,
                ls.description,
                ls.category
            FROM layer_standards ls
            WHERE ls.entity_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM entity_embeddings ee
                  WHERE ee.entity_id = ls.entity_id
                    AND ee.is_current = TRUE
              )
            ORDER BY ls.usage_frequency DESC NULLS LAST, ls.name
            LIMIT %s
        """, (limit,))

        layers = cursor.fetchall()
        cursor.close()

        return layers

    def estimate_cost(self, layers):
        """Estimate the cost of embedding generation."""
        # Average tokens per layer: name (10) + description (50) + category (5) = ~65 tokens
        avg_tokens = 65
        total_tokens = len(layers) * avg_tokens
        estimated_cost = (total_tokens / 1000.0) * self.cost_per_1k_tokens

        return {
            'layer_count': len(layers),
            'estimated_tokens': total_tokens,
            'estimated_cost': estimated_cost
        }

    def generate_embedding(self, text):
        """Generate a single embedding using OpenAI API."""
        if self.dry_run:
            # Return fake embedding for dry run
            return [0.0] * self.dimensions, 65  # Fake embedding, estimated tokens

        response = self.client.embeddings.create(
            model=self.model,
            input=text,
            dimensions=self.dimensions
        )

        embedding = response.data[0].embedding
        tokens_used = response.usage.total_tokens

        return embedding, tokens_used

    def save_embedding(self, entity_id, embedding, embedding_text, tokens_used):
        """Save embedding to database."""
        if self.dry_run:
            return

        cursor = self.conn.cursor()

        # Mark old embeddings as not current
        cursor.execute("""
            UPDATE entity_embeddings
            SET is_current = FALSE
            WHERE entity_id = %s
        """, (entity_id,))

        # Insert new embedding
        cursor.execute("""
            INSERT INTO entity_embeddings (
                entity_id,
                model_id,
                embedding,
                embedding_text,
                is_current,
                version,
                tokens_used
            ) VALUES (
                %s, %s, %s, %s, TRUE,
                COALESCE((
                    SELECT MAX(version) + 1
                    FROM entity_embeddings
                    WHERE entity_id = %s
                ), 1),
                %s
            )
        """, (entity_id, self.model_id, embedding, embedding_text, entity_id, tokens_used))

        self.conn.commit()
        cursor.close()

    def run(self, limit=100):
        """Generate embeddings for layers."""
        print('=' * 70)
        print('PHASE 1 - TASK 1: GENERATE EMBEDDINGS')
        print('=' * 70)
        print()

        # Get layers
        print(f'Fetching layers to embed (limit: {limit})...')
        layers = self.get_layers_to_embed(limit)
        print(f'✓ Found {len(layers)} layers without embeddings')
        print()

        if len(layers) == 0:
            print('No layers need embeddings. All done!')
            return

        # Estimate cost
        estimate = self.estimate_cost(layers)
        print('Cost Estimate:')
        print(f'  Layers: {estimate["layer_count"]:,}')
        print(f'  Estimated tokens: {estimate["estimated_tokens"]:,}')
        print(f'  Estimated cost: ${estimate["estimated_cost"]:.4f}')
        print(f'  Budget cap: ${self.budget_cap:.2f}')
        print()

        if estimate['estimated_cost'] > self.budget_cap:
            print(f'⚠️  Warning: Estimated cost exceeds budget cap!')
            print(f'  Reduce --limit or increase budget cap')
            return

        if self.dry_run:
            print('✓ DRY RUN MODE - No API calls will be made')
            print('  Run without --dry-run to generate actual embeddings')
            return

        # Confirm
        response = input(f'Proceed with embedding generation? (yes/no): ')
        if response.lower() != 'yes':
            print('Cancelled.')
            return

        print()
        print('Generating embeddings...')
        print('-' * 70)

        # Generate embeddings
        total_tokens = 0
        total_cost = 0.0
        generated = 0
        failed = 0

        for i, (layer_id, entity_id, name, description, category) in enumerate(layers, 1):
            # Create embedding text
            text_parts = [name]
            if description:
                text_parts.append(description)
            if category:
                text_parts.append(f'Category: {category}')

            embedding_text = ' | '.join(text_parts)

            try:
                # Generate embedding
                embedding, tokens = self.generate_embedding(embedding_text)

                # Save to database
                self.save_embedding(entity_id, embedding, embedding_text, tokens)

                total_tokens += tokens
                total_cost += (tokens / 1000.0) * self.cost_per_1k_tokens
                generated += 1

                # Progress update every 10 layers
                if i % 10 == 0:
                    print(f'  [{i}/{len(layers)}] {name[:50]}... ({tokens} tokens)')

            except Exception as e:
                print(f'  ✗ Failed: {name} - {e}')
                failed += 1

        print()
        print('=' * 70)
        print('RESULTS:')
        print('=' * 70)
        print(f'  ✓ Generated: {generated}')
        print(f'  ✗ Failed: {failed}')
        print(f'  Total tokens: {total_tokens:,}')
        print(f'  Total cost: ${total_cost:.4f}')
        print()
        print('✓ Phase 1 - Task 1 Complete!')
        print()
        print('Next steps:')
        print('  - Run: python scripts/phase1_02_build_relationships.py')
        print('  - Or verify: python scripts/phase1_03_verify.py')


def main():
    parser = argparse.ArgumentParser(description='Generate embeddings for layer standards')
    parser.add_argument('--limit', type=int, default=100, help='Number of layers to process')
    parser.add_argument('--dry-run', action='store_true', help='Estimate cost without API calls')
    parser.add_argument('--budget-cap', type=float, default=10.0, help='Budget cap in dollars')

    args = parser.parse_args()

    try:
        generator = EmbeddingGenerator(dry_run=args.dry_run, budget_cap=args.budget_cap)
        generator.run(limit=args.limit)
    except KeyboardInterrupt:
        print('\n\nCancelled by user.')
        sys.exit(1)
    except Exception as e:
        print(f'\n✗ Error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
