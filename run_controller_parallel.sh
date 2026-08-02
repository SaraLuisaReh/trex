#!/bin/bash

# Usage: ./run_controller_parallel.sh inputfolder outputfolder
# Start and end of the analysis could also be modified by changing --start or --end in line 35 of this script.
# (Possibilities for start and end include "fastq", "bam", "vcf" and "tsv".)

INPUTFOLDER="$1"
OUTPUTFOLDER="$2"

# Check if arguments are provided
if [[ -z "$INPUTFOLDER" || -z "$OUTPUTFOLDER" ]]; then
    echo "Usage: $0 inputfolder outputfolder"
    exit 1
fi

# Get unique sample names by stripping after the second underscore
# Example: TRIO-DD_039_f_2.fastq.gz → TRIO-DD_039
SAMPLES=$(find "$INPUTFOLDER" -type f -name "*.fastq.gz" | \
    sed -E 's|.*/||' | \
    sed -E 's/_[a-z]+(_[12])?\.fastq\.gz$//' | \
    sort -u)

# Number of parallel jobs to run
MAX_JOBS=4

# Counter for background jobs
JOB_COUNT=0

# Export environment so subshells can use these
export INPUTFOLDER OUTPUTFOLDER

for SAMPLE in $SAMPLES; do
    (
        echo "Starting analysis for $SAMPLE..."
        time python3 -u controller.py "$INPUTFOLDER" "$OUTPUTFOLDER" --samples "$SAMPLE" --start "fastq" --end "tsv"
        echo "Finished analysis for $SAMPLE"
    ) &

    ((JOB_COUNT++))

    # If max jobs are running, wait for them to finish
    if (( JOB_COUNT % MAX_JOBS == 0 )); then
        wait
    fi
done

# Wait for any remaining background jobs to finish
wait

echo "All analyses completed."
