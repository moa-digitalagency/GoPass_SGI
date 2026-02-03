"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for benchmark_dashboard_query.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

import sys
import os
import time
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, GoPass
from sqlalchemy.orm import joinedload

# Query counter
query_count = 0

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    global query_count
    query_count += 1

def benchmark_lazy(app):
    global query_count
    query_count = 0
    with app.app_context():
        print("Benchmarking Lazy Loading...")
        start_time = time.time()

        # Simulate query without eager loading
        passes = GoPass.query.order_by(GoPass.issue_date.desc()).limit(5).all()

        # Iterate and access relationships
        for p in passes:
            _ = p.pass_number
            if p.holder:
                _ = p.holder.first_name
            if p.pass_type:
                _ = p.pass_type.name

        end_time = time.time()
        print(f"Lazy Loading: {query_count} queries executed in {end_time - start_time:.4f}s")
        return query_count

def benchmark_eager(app):
    global query_count
    query_count = 0
    with app.app_context():
        print("Benchmarking Eager Loading...")
        start_time = time.time()

        # Optimized query
        passes = GoPass.query.options(
            joinedload(GoPass.holder),
            joinedload(GoPass.pass_type)
        ).order_by(GoPass.issue_date.desc()).limit(5).all()

        # Iterate and access relationships
        for p in passes:
            _ = p.pass_number
            if p.holder:
                _ = p.holder.first_name
            if p.pass_type:
                _ = p.pass_type.name

        end_time = time.time()
        print(f"Eager Loading: {query_count} queries executed in {end_time - start_time:.4f}s")
        return query_count

if __name__ == '__main__':
    app = create_app()
    lazy_count = benchmark_lazy(app)
    eager_count = benchmark_eager(app)

    print(f"\nImprovement: {lazy_count} queries -> {eager_count} queries")
