#!/usr/bin/env python3
"""
Phase 2: Background Embedding Worker

This worker processes the embedding_generation_queue table and generates
embeddings asynchronously. It runs continuously in the background.

Usage:
    python workers/embedding_worker.py [--batch-size 50] [--poll-interval 10]

Options:
    --batch-size N      Process N items per batch (default: 50)
    --poll-interval N   Check queue every N seconds (default: 10)
    --budget-cap X      Daily budget cap in dollars (default: 100.0)
"""

import sys
import os
import time
import signal
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from openai import OpenAI

# Load environment
load_dotenv()


class EmbeddingWorker:
    """Background worker for async embedding generation."""

    def __init__(self, batch_size=50, budget_cap=100.0):
        self.batch_size = batch_size
        self.budget_cap = budget_cap
        self.running = True

        # OpenAI client
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = 'text-embedding-3-small'
        self.dimensions = 1536
        self.cost_per_1k_tokens = 0.00002

        # Database connection
        self.conn = None
        self.model_id = None

        # Statistics
        self.stats = {
            'processed': 0,
            'succeeded': 0,
            'failed': 0,
            'total_cost': 0.0,
            'total_tokens': 0,
            'started_at': datetime.now()
        }

    def connect_db(self):
        """Connect to database."""
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(
                host=os.getenv('PGHOST') or os.getenv('DB_HOST'),
                port=int(os.getenv('PGPORT') or os.getenv('DB_PORT', 5432)),
                database=os.getenv('PGDATABASE') or os.getenv('DB_NAME'),
                user=os.getenv('PGUSER') or os.getenv('DB_USER'),
                password=os.getenv('PGPASSWORD') or os.getenv('DB_PASSWORD'),
                sslmode='require',
                cursor_factory=RealDictCursor
            )

    def register_model(self):
        """Register embedding model."""
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

        self.model_id = cursor.fetchone()['model_id']
        self.conn.commit()
        cursor.close()

    def check_budget(self):
        """Check if we're within budget for today."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT COALESCE(SUM(ee.tokens_used * em.cost_per_1k_tokens / 1000.0), 0) as today_cost
            FROM entity_embeddings ee
            JOIN embedding_models em ON ee.model_id = em.model_id
            WHERE ee.created_at >= CURRENT_DATE
        """)

        today_cost = cursor.fetchone()['today_cost']
        cursor.close()

        return today_cost < self.budget_cap

    def get_pending_batch(self):
        """Get a batch of pending items from queue."""
        cursor = self.conn.cursor()

        # Mark items as processing
        cursor.execute("""
            WITH pending AS (
                SELECT queue_id
                FROM embedding_generation_queue
                WHERE status = 'pending'
                ORDER BY
                    CASE priority
                        WHEN 'high' THEN 1
                        WHEN 'normal' THEN 2
                        WHEN 'low' THEN 3
                    END,
                    created_at ASC
                LIMIT %s
                FOR UPDATE SKIP LOCKED
            )
            UPDATE embedding_generation_queue
            SET status = 'processing'
            WHERE queue_id IN (SELECT queue_id FROM pending)
            RETURNING queue_id, entity_id, text_to_embed
        """, (self.batch_size,))

        items = cursor.fetchall()
        self.conn.commit()
        cursor.close()

        return items

    def generate_embedding(self, text):
        """Generate embedding via OpenAI API."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions
            )

            return {
                'embedding': response.data[0].embedding,
                'tokens': response.usage.total_tokens,
                'success': True
            }
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }

    def save_embedding(self, entity_id, embedding, text, tokens):
        """Save embedding to database."""
        cursor = self.conn.cursor()

        try:
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
            """, (entity_id, self.model_id, embedding, text, entity_id, tokens))

            self.conn.commit()
            cursor.close()
            return True

        except Exception as e:
            self.conn.rollback()
            cursor.close()
            raise e

    def mark_completed(self, queue_id):
        """Mark queue item as completed."""
        cursor = self.conn.cursor()

        cursor.execute("""
            UPDATE embedding_generation_queue
            SET status = 'completed',
                processed_at = CURRENT_TIMESTAMP
            WHERE queue_id = %s
        """, (queue_id,))

        self.conn.commit()
        cursor.close()

    def mark_failed(self, queue_id, error_msg):
        """Mark queue item as failed."""
        cursor = self.conn.cursor()

        cursor.execute("""
            UPDATE embedding_generation_queue
            SET status = 'failed',
                attempt_count = attempt_count + 1,
                error_message = %s,
                processed_at = CURRENT_TIMESTAMP
            WHERE queue_id = %s
        """, (error_msg, queue_id))

        self.conn.commit()
        cursor.close()

    def process_batch(self):
        """Process a batch of embeddings."""
        # Check budget
        if not self.check_budget():
            print(f'  ⚠️  Daily budget cap (${self.budget_cap}) reached. Pausing until tomorrow.')
            return 0

        # Get pending items
        items = self.get_pending_batch()

        if not items:
            return 0

        print(f'  Processing {len(items)} items...')

        # Process each item
        succeeded = 0
        failed = 0

        for item in items:
            queue_id = item['queue_id']
            entity_id = item['entity_id']
            text = item['text_to_embed']

            try:
                # Generate embedding
                result = self.generate_embedding(text)

                if result['success']:
                    # Save to database
                    self.save_embedding(
                        entity_id,
                        result['embedding'],
                        text,
                        result['tokens']
                    )

                    # Mark completed
                    self.mark_completed(queue_id)

                    # Update stats
                    succeeded += 1
                    self.stats['tokens'] += result['tokens']
                    self.stats['total_cost'] += (result['tokens'] / 1000.0) * self.cost_per_1k_tokens

                else:
                    # Mark failed
                    self.mark_failed(queue_id, result['error'])
                    failed += 1

            except Exception as e:
                # Mark failed
                self.mark_failed(queue_id, str(e))
                failed += 1
                print(f'    ✗ Error processing {entity_id}: {e}')

        # Update overall stats
        self.stats['processed'] += len(items)
        self.stats['succeeded'] += succeeded
        self.stats['failed'] += failed

        print(f'  ✓ Completed: {succeeded}, Failed: {failed}')

        return len(items)

    def print_stats(self):
        """Print worker statistics."""
        uptime = datetime.now() - self.stats['started_at']

        print()
        print('=' * 70)
        print('WORKER STATISTICS')
        print('=' * 70)
        print(f'  Uptime: {uptime}')
        print(f'  Processed: {self.stats["processed"]:,}')
        print(f'  Succeeded: {self.stats["succeeded"]:,}')
        print(f'  Failed: {self.stats["failed"]:,}')
        print(f'  Total tokens: {self.stats["total_tokens"]:,}')
        print(f'  Total cost: ${self.stats["total_cost"]:.4f}')
        print('=' * 70)
        print()

    def run(self, poll_interval=10):
        """Main worker loop."""
        print('=' * 70)
        print('EMBEDDING WORKER STARTED')
        print('=' * 70)
        print(f'  Model: {self.model}')
        print(f'  Batch size: {self.batch_size}')
        print(f'  Poll interval: {poll_interval}s')
        print(f'  Budget cap: ${self.budget_cap}/day')
        print()
        print('Press Ctrl+C to stop')
        print('=' * 70)
        print()

        # Connect and register model
        self.connect_db()
        self.register_model()

        last_stats_print = datetime.now()

        # Main loop
        while self.running:
            try:
                # Process batch
                processed = self.process_batch()

                # Print stats every 5 minutes
                if (datetime.now() - last_stats_print).total_seconds() > 300:
                    self.print_stats()
                    last_stats_print = datetime.now()

                # Sleep if no items processed
                if processed == 0:
                    time.sleep(poll_interval)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f'  ✗ Error in main loop: {e}')
                time.sleep(poll_interval)

        # Cleanup
        print()
        print('Shutting down...')
        self.print_stats()

        if self.conn:
            self.conn.close()

        print('Worker stopped.')


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    print('\nReceived shutdown signal...')
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description='Background embedding worker')
    parser.add_argument('--batch-size', type=int, default=50,
                        help='Items per batch (default: 50)')
    parser.add_argument('--poll-interval', type=int, default=10,
                        help='Poll interval in seconds (default: 10)')
    parser.add_argument('--budget-cap', type=float, default=100.0,
                        help='Daily budget cap in dollars (default: 100.0)')

    args = parser.parse_args()

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run worker
    try:
        worker = EmbeddingWorker(
            batch_size=args.batch_size,
            budget_cap=args.budget_cap
        )
        worker.run(poll_interval=args.poll_interval)
    except Exception as e:
        print(f'\nFatal error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
