#!/usr/bin/env python3
"""A job that runs for a bit then crashes with a realistic traceback."""
import time
import sys
import random

random.seed()

print("Initializing simulation parameters...")
time.sleep(2)
print("Loading configuration from /etc/sim/config.yaml")
time.sleep(1)
print("Connecting to distributed cache at redis://cache-node:6379...")
time.sleep(1)
print("Connected.")
print()

iterations = random.randint(5, 15)
for i in range(iterations):
    print(f"Processing batch {i+1}/{iterations}... "
          f"throughput={random.uniform(100, 500):.1f} items/s", flush=True)
    if random.random() < 0.3:
        print(f"  WARN: Retry on batch {i+1}, transient error", file=sys.stderr, flush=True)
    time.sleep(2)

# Crash
print(f"Processing batch {iterations + 1}...", flush=True)
time.sleep(1)

crash_type = random.choice(["oom", "keyerror", "cuda", "timeout"])

if crash_type == "oom":
    print("Traceback (most recent call last):", file=sys.stderr)
    print('  File "/opt/sim/engine.py", line 342, in run_simulation', file=sys.stderr)
    print("    results = allocate_buffer(n_particles * dims)", file=sys.stderr)
    print('  File "/opt/sim/memory.py", line 89, in allocate_buffer', file=sys.stderr)
    print("    buf = np.zeros(shape, dtype=np.float64)", file=sys.stderr)
    print("numpy.core._exceptions.MemoryError: Unable to allocate 14.9 GiB for an array with shape (2000000000,) and data type float64", file=sys.stderr)
elif crash_type == "keyerror":
    print("Traceback (most recent call last):", file=sys.stderr)
    print('  File "/opt/sim/pipeline.py", line 156, in process_batch', file=sys.stderr)
    print("    features = record['embeddings']['layer_12']", file=sys.stderr)
    print("KeyError: 'layer_12'", file=sys.stderr)
    print("", file=sys.stderr)
    print("The above exception was the direct cause of the following exception:", file=sys.stderr)
    print("", file=sys.stderr)
    print("Traceback (most recent call last):", file=sys.stderr)
    print('  File "/opt/sim/main.py", line 45, in <module>', file=sys.stderr)
    print("    run_pipeline(config)", file=sys.stderr)
    print('  File "/opt/sim/pipeline.py", line 201, in run_pipeline', file=sys.stderr)
    print("    batch_results = process_batch(batch)", file=sys.stderr)
    print("RuntimeError: Failed to process batch 12: missing key 'layer_12' in embeddings dict", file=sys.stderr)
elif crash_type == "cuda":
    print("Traceback (most recent call last):", file=sys.stderr)
    print('  File "/opt/sim/trainer.py", line 267, in forward_pass', file=sys.stderr)
    print("    output = self.model(input_tensor.cuda())", file=sys.stderr)
    print('  File "/usr/lib/python3.11/site-packages/torch/nn/modules/module.py", line 1518, in _call_impl', file=sys.stderr)
    print("    return forward_call(*args, **kwargs)", file=sys.stderr)
    print("RuntimeError: CUDA error: device-side assert triggered", file=sys.stderr)
    print("CUDA kernel errors might be asynchronously reported at some other API call, so the stacktrace below might be incorrect.", file=sys.stderr)
else:
    print("Traceback (most recent call last):", file=sys.stderr)
    print('  File "/opt/sim/distributed.py", line 98, in gather_results', file=sys.stderr)
    print("    response = coordinator.collect(timeout=300)", file=sys.stderr)
    print('  File "/opt/sim/rpc.py", line 45, in collect', file=sys.stderr)
    print("    raise TimeoutError(f'Worker {self.rank} did not respond within {timeout}s')", file=sys.stderr)
    print("TimeoutError: Worker 3 did not respond within 300s", file=sys.stderr)

sys.exit(1)
