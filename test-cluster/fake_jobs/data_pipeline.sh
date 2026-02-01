#!/bin/bash
# Fake data ETL pipeline with progress bars and warnings

echo "=========================================="
echo "  Data Pipeline v3.2.1"
echo "  $(date)"
echo "=========================================="
echo ""

STAGES=("Extracting raw data" "Decompressing archives" "Parsing CSV records" "Validating schema" "Deduplicating entries" "Transforming features" "Computing aggregations" "Writing parquet output")
TOTAL_RECORDS=$((RANDOM % 5000000 + 1000000))

echo "Processing $TOTAL_RECORDS records across ${#STAGES[@]} stages"
echo ""

for i in "${!STAGES[@]}"; do
    stage="${STAGES[$i]}"
    echo "[$((i+1))/${#STAGES[@]}] $stage..."

    steps=20
    for ((s=1; s<=steps; s++)); do
        pct=$((s * 100 / steps))
        bar=$(printf '#%.0s' $(seq 1 $((s * 2))))
        printf "\r  [%-40s] %3d%%" "$bar" "$pct"

        # Random warnings to stderr
        if [ $((RANDOM % 15)) -eq 0 ]; then
            echo "" >&2
            case $((RANDOM % 4)) in
                0) echo "  WARN: Null value in column 'user_id' at row $((RANDOM % TOTAL_RECORDS))" >&2 ;;
                1) echo "  WARN: Timestamp out of range: 2087-13-42T99:99:99Z, row $((RANDOM % TOTAL_RECORDS))" >&2 ;;
                2) echo "  WARN: Duplicate key detected, keeping latest entry" >&2 ;;
                3) echo "  WARN: Memory usage at $((60 + RANDOM % 35))%, consider increasing --mem" >&2 ;;
            esac
        fi

        sleep 1
    done
    echo ""

    processed=$((TOTAL_RECORDS * (i + 1) / ${#STAGES[@]}))
    echo "  Done. $processed/$TOTAL_RECORDS records processed."
    echo ""
done

echo "=========================================="
echo "  Pipeline complete"
echo "  Total records: $TOTAL_RECORDS"
echo "  Output: /data/output/result_$(date +%Y%m%d).parquet"
echo "  Duration: ${SECONDS}s"
echo "=========================================="
