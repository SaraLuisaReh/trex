#!/bin/bash

REFGENOME=$4
SAMPLENAMES=$1
INPUTPATH=$2
OUTPUTPATH=$3
BEDFILE=$5

# RAM requirements: 16 GB; threads: 8

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

# Get the package paths
BCFTOOLS="${BINDIR}/bcftools"
GATK="${PARENTPATH}/apps/gatk"
JAVA_PATH="${BINDIR}/java/bin/java"

# Input BAM files and outputfolder
READFROM="${INPUTPATH}/"
OUTPUT_VCF="${OUTPUTPATH}/gatk/"

mkdir -p ${OUTPUT_VCF}

for SAMPLENAME in ${SAMPLENAMES[*]} ; do

    BAM_F=${READFROM}/${SAMPLENAME}_f.bam
    BAM_M=${READFROM}/${SAMPLENAME}_m.bam
    BAM_C=${READFROM}/${SAMPLENAME}_c.bam
    GATK_VCF=${OUTPUT_VCF}/${SAMPLENAME}.vcf

    #Create GVCF files using GATK HaplotypeCaller
    "${JAVA_PATH}" "-Xmx16g" -jar "$GATK.jar" HaplotypeCaller \
    -R ${REFGENOME} \
    -I "${BAM_C}" \
    -O ${OUTPUT_VCF}/${SAMPLENAME}_c.vcf.gz \
    -L ${BEDFILE} \
    --native-pair-hmm-threads 8

    "${JAVA_PATH}" "-Xmx16g" -jar "$GATK.jar" HaplotypeCaller \
    -R ${REFGENOME} \
    -I "${BAM_F}" \
    -O ${OUTPUT_VCF}/${SAMPLENAME}_f.vcf.gz \
    -L ${BEDFILE} \
    --native-pair-hmm-threads 8

    "${JAVA_PATH}" "-Xmx16g" -jar "$GATK.jar" HaplotypeCaller \
    -R ${REFGENOME} \
    -I "${BAM_M}" \
    -O ${OUTPUT_VCF}/${SAMPLENAME}_m.vcf.gz \
    -L ${BEDFILE} \
    --native-pair-hmm-threads 8

    "$BCFTOOLS" merge -m none ${OUTPUT_VCF}/${SAMPLENAME}_f.vcf.gz ${OUTPUT_VCF}/${SAMPLENAME}_m.vcf.gz ${OUTPUT_VCF}/${SAMPLENAME}_c.vcf.gz -O v -o ${OUTPUT_VCF}/${SAMPLENAME}.vcf


done
