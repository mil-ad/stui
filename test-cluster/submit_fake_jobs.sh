#!/bin/bash
# Submit a variety of fake jobs as different users
set -e

JOBS_DIR=/opt/fake_jobs

echo "Waiting for nodes to come online..."
for i in $(seq 1 30); do
    if sinfo -N -h 2>/dev/null | grep -q "idle"; then
        echo "Nodes ready."
        break
    fi
    sleep 2
done

echo ""
echo "Submitting jobs..."
echo ""

# --- alice: ML researcher ---
su - alice -s /bin/bash -c "sbatch --job-name=bert-finetune --partition=compute --cpus-per-task=2 --mem=2G --time=02:00:00 --wrap 'python3 $JOBS_DIR/model_training.py'"
su - alice -s /bin/bash -c "sbatch --job-name=vit-pretrain --partition=compute --cpus-per-task=4 --mem=3G --time=04:00:00 --wrap 'python3 $JOBS_DIR/model_training.py'"
su - alice -s /bin/bash -c "sbatch --job-name=gpt2-eval --partition=gpu --cpus-per-task=1 --mem=1G --time=00:30:00 --wrap 'python3 $JOBS_DIR/model_training.py'"

# --- bob: bioinformatics ---
su - bob -s /bin/bash -c "sbatch --job-name=genome-align-001 --partition=compute --cpus-per-task=2 --mem=3G --time=06:00:00 --wrap 'bash $JOBS_DIR/genome_align.sh'"
su - bob -s /bin/bash -c "sbatch --job-name=genome-align-002 --partition=compute --cpus-per-task=2 --mem=3G --time=06:00:00 --wrap 'bash $JOBS_DIR/genome_align.sh'"
su - bob -s /bin/bash -c "sbatch --job-name=variant-calling --partition=compute --cpus-per-task=1 --mem=2G --time=03:00:00 --wrap 'bash $JOBS_DIR/genome_align.sh'"

# --- carol: data engineer ---
su - carol -s /bin/bash -c "sbatch --job-name=etl-daily --partition=compute --cpus-per-task=1 --mem=2G --time=01:00:00 --wrap 'bash $JOBS_DIR/data_pipeline.sh'"
su - carol -s /bin/bash -c "sbatch --job-name=etl-weekly --partition=compute --cpus-per-task=2 --mem=3G --time=02:00:00 --wrap 'bash $JOBS_DIR/data_pipeline.sh'"
# Array job
su - carol -s /bin/bash -c "sbatch --job-name=batch-ingest --partition=compute --cpus-per-task=1 --mem=1G --time=00:30:00 --array=1-5 --wrap 'echo \"Array task \$SLURM_ARRAY_TASK_ID\"; bash $JOBS_DIR/data_pipeline.sh'"

# --- dave: HPC / physics ---
su - dave -s /bin/bash -c "sbatch --job-name=matrix-4k --partition=compute --cpus-per-task=2 --mem=2G --time=01:00:00 --wrap 'python3 $JOBS_DIR/matrix_multiply.py'"
su - dave -s /bin/bash -c "sbatch --job-name=matrix-16k --partition=gpu --cpus-per-task=4 --mem=3G --time=08:00:00 --wrap 'python3 $JOBS_DIR/matrix_multiply.py'"
# Jobs that will fail
su - dave -s /bin/bash -c "sbatch --job-name=sim-crash --partition=compute --cpus-per-task=1 --mem=1G --time=00:15:00 --wrap 'python3 $JOBS_DIR/failed_job.py'"
su - dave -s /bin/bash -c "sbatch --job-name=oom-test --partition=compute --cpus-per-task=1 --mem=1G --time=00:10:00 --wrap 'python3 $JOBS_DIR/failed_job.py'"

# A couple of short sleep jobs to quickly get COMPLETED status
su - alice -s /bin/bash -c "sbatch --job-name=quick-test --partition=compute --cpus-per-task=1 --mem=100M --time=00:01:00 --wrap 'echo Done; sleep 5'"
su - bob -s /bin/bash -c "sbatch --job-name=sanity-check --partition=compute --cpus-per-task=1 --mem=100M --time=00:01:00 --wrap 'echo All good; sleep 3'"

echo ""
echo "All jobs submitted. Run 'squeue' to see the queue."
squeue
