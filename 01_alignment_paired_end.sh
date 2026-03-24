#!/bin/bash

REFGENOME=$4
TARGETS=$5

SAMPLENAMES=$1
INPUTPATH=$2
OUTPUTPATH=$3

READFROM="${INPUTPATH}/"
WRITETO="${OUTPUTPATH}/bam/"
TEMP="${OUTPUTPATH}/tempAlignment/"
QC="${OUTPUTPATH}/QC/"

# Get Parentpath
PARENTPATH="$(cd "$(dirname "$(realpath "$0")")" && pwd)"

# Get the system's-specific package path
OS="$(uname -s)"
ARCH="$(uname -m)"
if [[ "$OS" == "Darwin" && "$ARCH" == "arm64" ]]; then
  BINDIR="$PARENTPATH/apps/macos_arm64"
elif [[ "$OS" == "Linux" && "$ARCH" == "x86_64" ]]; then
  BINDIR="$PARENTPATH/apps/linux_x86_64"
fi

TRIMMOMATIC="${PARENTPATH}/apps/trimmomatic"
TRIMMOMATIC_ADAPTERS="${PARENTPATH}/apps/TruSeq3-PE"
PICARD="${PARENTPATH}/apps/picard"
SAMTOOLS="${BINDIR}/samtools"
BEDTOOLS="${BINDIR}/bedtools"
BWA="${BINDIR}/bwa"
JAVA_PATH="${BINDIR}/java/bin/java"

THREADS=8

PICARDOUT=${QC}picard

mkdir -p ${TEMP} ${QC} ${PICARDOUT} ${WRITETO}/log

for SAMPLENAME in ${SAMPLENAMES[*]} ; do

    for TAG in _c _f _m ; do

        SAMPLE=${SAMPLENAME}${TAG}

        PICARDOUT_PREFIX=${QC}picard/${SAMPLE}
        LOG_ALN=${WRITETO}log/${SAMPLE}_log_bwamem.txt
        LOG_PICARD_1=${WRITETO}log/${SAMPLE}_log_Picard_SortSam.txt
        LOG_PICARD_2=${WRITETO}log/${SAMPLE}_log_Picard_MarkDuplicates.txt

        # trim paired-end reads with Trimmomatic
        "${JAVA_PATH}" -jar ${TRIMMOMATIC}.jar PE -phred33 \
          ${READFROM}${SAMPLE}_1.fastq.gz ${READFROM}${SAMPLE}_2.fastq.gz \
          ${TEMP}${SAMPLE}_1_trimmed_paired.fastq.gz ${TEMP}${SAMPLE}_1_trimmed_unpaired.fastq.gz \
          ${TEMP}${SAMPLE}_2_trimmed_paired.fastq.gz ${TEMP}${SAMPLE}_2_trimmed_unpaired.fastq.gz \
          ILLUMINACLIP:${TRIMMOMATIC_ADAPTERS}.fa:2:30:10 LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:36

        # align trimmed paired reads only (use paired files)
        "${BWA}" mem -t ${THREADS} -R "@RG\tID:${SAMPLE}\tSM:${SAMPLE}\tPL:ILLUMINA\tPI:330" ${REFGENOME} \
          ${TEMP}${SAMPLE}_1_trimmed_paired.fastq.gz ${TEMP}${SAMPLE}_2_trimmed_paired.fastq.gz > ${TEMP}${SAMPLE}.sam 2> ${LOG_ALN}

        # sort SAM -> BAM
        "${JAVA_PATH}" -Xmx16g -jar "${PICARD}.jar" SortSam INPUT=${TEMP}${SAMPLE}.sam OUTPUT=${TEMP}${SAMPLE}.bam SORT_ORDER=coordinate CREATE_INDEX=true \
            VALIDATION_STRINGENCY=LENIENT 2> ${LOG_PICARD_1}

        rm ${TEMP}${SAMPLE}.sam

        # mark duplicates
        "${JAVA_PATH}" -Xmx16g -jar "${PICARD}.jar" MarkDuplicates INPUT=${TEMP}${SAMPLE}.bam OUTPUT=${TEMP}${SAMPLE}_picard.bam REMOVE_DUPLICATES=true \
            METRICS_FILE=${PICARDOUT_PREFIX}_duplicate_metrics.txt CREATE_INDEX=true \
            VALIDATION_STRINGENCY=LENIENT MAX_RECORDS_IN_RAM=5000000 2> ${LOG_PICARD_2}

        # filter to targets with bedtools
        "${BEDTOOLS}" intersect -a ${TEMP}${SAMPLE}_picard.bam -b ${TARGETS} -wa > ${WRITETO}${SAMPLE}.bam
        "${SAMTOOLS}" index ${WRITETO}${SAMPLE}.bam

        # cleanup temp BAMs
        rm ${TEMP}${SAMPLE}_picard.bam
        rm ${TEMP}${SAMPLE}.bam

        # Optionally cleanup trimmed unpaired files if not needed:
        rm ${TEMP}${SAMPLE}_1_trimmed_unpaired.fastq.gz ${TEMP}${SAMPLE}_2_trimmed_unpaired.fastq.gz
    done

done
