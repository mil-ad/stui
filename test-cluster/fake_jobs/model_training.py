#!/usr/bin/env python3
"""Fake ML model training — prints realistic training logs."""
import sys
import time
import random
import math

random.seed(42)

model_name = random.choice(["ResNet-50", "BERT-base", "GPT-2-small", "ViT-L/16", "Llama-7B-LoRA"])
dataset = random.choice(["ImageNet-1k", "CIFAR-100", "WikiText-103", "OpenWebText", "CC-3M"])
lr = random.choice([1e-3, 3e-4, 5e-5, 2e-4])
batch_size = random.choice([16, 32, 64, 128])
total_epochs = random.randint(5, 20)

print(f"{'='*60}")
print(f"  Training: {model_name}")
print(f"  Dataset:  {dataset}")
print(f"  LR: {lr}, Batch Size: {batch_size}, Epochs: {total_epochs}")
print(f"{'='*60}")
print(f"Loading dataset...", flush=True)
time.sleep(2)
print(f"Loaded {random.randint(50000, 1200000)} samples", flush=True)
print(f"Model parameters: {random.uniform(10, 7000):.1f}M", flush=True)
print()

loss = random.uniform(3.0, 6.0)

for epoch in range(1, total_epochs + 1):
    steps = random.randint(200, 800)
    for step in range(0, steps + 1, 50):
        decay = math.exp(-0.003 * ((epoch - 1) * steps + step))
        noise = random.gauss(0, 0.05)
        current_loss = loss * decay + noise + 0.3
        acc = min(99.5, 100 * (1 - decay) + random.gauss(0, 1.5))

        if step % 200 == 0:
            print(f"[Epoch {epoch:>2}/{total_epochs}] Step {step:>4}/{steps}  "
                  f"loss={current_loss:.4f}  acc={acc:.2f}%  "
                  f"lr={lr * min(1.0, step / max(1, 100)):.2e}", flush=True)

        if random.random() < 0.02:
            print(f"  WARNING: gradient norm {random.uniform(5, 50):.1f} exceeds threshold, clipping",
                  file=sys.stderr, flush=True)

        time.sleep(0.5)

    val_loss = loss * math.exp(-0.003 * epoch * steps) + random.gauss(0, 0.03) + 0.35
    val_acc = min(99.0, 100 * (1 - math.exp(-0.003 * epoch * steps)) + random.gauss(0, 1.0))
    print(f"  --> Validation: loss={val_loss:.4f}, acc={val_acc:.2f}%", flush=True)
    print(f"  --> Checkpoint saved: ckpt_epoch{epoch}.pt", flush=True)
    print()

print(f"Training complete. Best val_acc: {val_acc:.2f}%")
