#!/usr/bin/env python3
"""Fake distributed matrix computation with periodic status output."""
import time
import random
import sys

random.seed()

N = random.choice([2048, 4096, 8192, 16384])
block_size = random.choice([256, 512])
total_blocks = (N // block_size) ** 2

print(f"Matrix multiplication: ({N} x {N}) @ ({N} x {N})")
print(f"Block size: {block_size}, Total blocks: {total_blocks}")
print(f"Precision: float64, Algorithm: Cannon's")
print(f"Allocated {N * N * 8 * 2 / 1e9:.2f} GB")
print()

completed = 0
start = time.time()

while completed < total_blocks:
    batch = random.randint(1, max(1, total_blocks // 15))
    completed = min(completed + batch, total_blocks)
    elapsed = time.time() - start
    rate = completed / max(elapsed, 0.1)
    eta = (total_blocks - completed) / max(rate, 0.1)

    print(f"  Block {completed:>6}/{total_blocks}  "
          f"[{'#' * (completed * 30 // total_blocks):<30}]  "
          f"{completed * 100 / total_blocks:5.1f}%  "
          f"ETA: {eta:.0f}s  GFLOPS: {random.uniform(50, 200):.1f}", flush=True)

    if random.random() < 0.05:
        print(f"  INFO: cache miss rate {random.uniform(0.01, 0.15):.3f} at block {completed}",
              file=sys.stderr, flush=True)

    time.sleep(random.uniform(1, 3))

elapsed = time.time() - start
print()
print(f"Computation complete in {elapsed:.1f}s")
print(f"Result norm: {random.uniform(1e3, 1e6):.6e}")
print(f"Max element: {random.uniform(1e2, 1e5):.4f}")
print(f"Checksum: {random.getrandbits(64):016x}")
