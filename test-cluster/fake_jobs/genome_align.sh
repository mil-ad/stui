#!/bin/bash
# Fake genome alignment / bioinformatics pipeline

SAMPLE_ID="SAMPLE_$(printf '%04d' $((RANDOM % 9999)))"
READS=$((RANDOM % 50000000 + 10000000))

echo "================================================================"
echo "  Genome Alignment Pipeline"
echo "  Sample: $SAMPLE_ID"
echo "  Reference: GRCh38.p14"
echo "  Reads: $READS paired-end (150bp)"
echo "================================================================"
echo ""

echo "[$(date +%H:%M:%S)] Loading reference index..."
sleep 3
echo "[$(date +%H:%M:%S)] Index loaded (3.2 GB)"
echo ""

# Alignment phase
echo "[$(date +%H:%M:%S)] Starting alignment with BWA-MEM2..."
aligned=0
chunk=$((READS / 20))
while [ $aligned -lt $READS ]; do
    aligned=$((aligned + chunk + RANDOM % 1000))
    if [ $aligned -gt $READS ]; then aligned=$READS; fi
    pct=$((aligned * 100 / READS))
    rate=$((RANDOM % 5000 + 8000))
    echo "[$(date +%H:%M:%S)] Aligned: $aligned/$READS ($pct%) — ${rate} reads/sec"

    # stderr warnings
    if [ $((RANDOM % 5)) -eq 0 ]; then
        echo "[$(date +%H:%M:%S)] WARNING: Low mapping quality (MAPQ<10) for $((RANDOM % 500 + 100)) reads in chr$((RANDOM % 22 + 1))" >&2
    fi
    if [ $((RANDOM % 10)) -eq 0 ]; then
        echo "[$(date +%H:%M:%S)] WARNING: Chimeric alignment detected at chr$((RANDOM % 22 + 1)):$((RANDOM % 100000000))" >&2
    fi

    sleep 2
done
echo ""

# Stats
mapped=$((READS * (95 + RANDOM % 4) / 100))
duplicates=$((mapped * (5 + RANDOM % 10) / 100))
echo "[$(date +%H:%M:%S)] Sorting BAM..."
sleep 2
echo "[$(date +%H:%M:%S)] Marking duplicates..."
sleep 2
echo ""
echo "================================================================"
echo "  Alignment Summary — $SAMPLE_ID"
echo "  Total reads:     $READS"
echo "  Mapped:          $mapped ($(( mapped * 100 / READS ))%)"
echo "  Duplicates:      $duplicates ($(( duplicates * 100 / mapped ))%)"
echo "  Mean coverage:   ${RANDOM:0:2}.${RANDOM:0:1}x"
echo "  Output:          /data/aligned/${SAMPLE_ID}.sorted.dedup.bam"
echo "================================================================"
