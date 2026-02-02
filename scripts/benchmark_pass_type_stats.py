import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from sqlalchemy import func
from app import create_app
from models import db, GoPass, PassType

def run_inefficient():
    # print("Running Inefficient N+1 Query Logic...")
    start_time = time.time()

    # The logic from the issue description
    pass_types = PassType.query.filter_by(is_active=True).all()
    pass_type_stats = []
    for pt in pass_types:
        # Task said status='active', but code uses 'valid' usually.
        # I'll use 'valid' as seeded.
        count = GoPass.query.filter_by(type_id=pt.id, status='valid').count()
        pass_type_stats.append({
            'name': pt.name,
            'count': count,
            'color': pt.color
        })

    end_time = time.time()
    return end_time - start_time, pass_type_stats

def run_optimized():
    # print("Running Optimized Aggregation Logic...")
    start_time = time.time()

    pass_type_counts = db.session.query(
        PassType,
        func.count(GoPass.id)
    ).outerjoin(
        GoPass,
        (GoPass.type_id == PassType.id) & (GoPass.status == 'valid')
    ).filter(
        PassType.is_active == True
    ).group_by(PassType.id).all()

    pass_type_stats = []
    for pt, count in pass_type_counts:
        pass_type_stats.append({
            'name': pt.name,
            'count': count,
            'color': pt.color
        })

    end_time = time.time()
    return end_time - start_time, pass_type_stats

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        print("Benchmarking...")
        # Warmup
        run_inefficient()
        run_optimized()

        iterations = 50

        # Benchmark Inefficient
        total_inefficient = 0
        for _ in range(iterations):
            dur, _ = run_inefficient()
            total_inefficient += dur
        avg_inefficient = total_inefficient / iterations

        # Benchmark Optimized
        total_optimized = 0
        for _ in range(iterations):
            dur, results = run_optimized()
            total_optimized += dur
        avg_optimized = total_optimized / iterations

        print(f"\nResults for {iterations} iterations:")
        print(f"Inefficient Average Time: {avg_inefficient:.6f}s")
        print(f"Optimized Average Time:   {avg_optimized:.6f}s")
        print(f"Speedup: {avg_inefficient / avg_optimized:.2f}x")

        # Verify Results
        _, res_inefficient = run_inefficient()
        _, res_optimized = run_optimized()

        # Sort by name to compare
        res_inefficient.sort(key=lambda x: x['name'])
        res_optimized.sort(key=lambda x: x['name'])

        if res_inefficient == res_optimized:
            print("\n✅ Verification Successful: Results match.")
        else:
            print("\n❌ Verification Failed: Results do not match.")
            print("Inefficient:", res_inefficient)
            print("Optimized:", res_optimized)
