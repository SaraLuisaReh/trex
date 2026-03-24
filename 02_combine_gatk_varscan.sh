#!/bin/bash

PRIOR_OUTPUT_PATH=$1
SAMPLENAMES=$2

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
BGZIP="${BINDIR}/bgzip"

VARSCAN_PATH="${PRIOR_OUTPUT_PATH}/varscan/"
GATK_PATH="${PRIOR_OUTPUT_PATH}/gatk/"
COMBINED_PATH="${PRIOR_OUTPUT_PATH}/gatk_and_varscan/"
INTERSECTED_FOLDER="${PRIOR_OUTPUT_PATH}/vcf"

mkdir -p ${COMBINED_PATH} ${INTERSECTED_FOLDER}

for SAMPLENAME in ${SAMPLENAMES[*]} ; do

    VCF_VARSCAN_INDEL=${VARSCAN_PATH}/${SAMPLENAME}.indel.pass.vcf
    VCF_VARSCAN_SNP=${VARSCAN_PATH}/${SAMPLENAME}.snp.pass.vcf
    VCF_GATK=${GATK_PATH}/${SAMPLENAME}.vcf

    # Define output names
    VCF_VARSCAN=${VARSCAN_PATH}/${SAMPLENAME}.vcf
    VCF_COMBINED_FOLDER=${COMBINED_PATH}/${SAMPLENAME}

    # bgzip VCF output
    if [ ! -f ${VCF_VARSCAN_INDEL}.gz ];
    then "$BGZIP" ${VCF_VARSCAN_INDEL}
    fi
    if [ ! -f ${VCF_VARSCAN_SNP}.gz ];
    then "$BGZIP" ${VCF_VARSCAN_SNP}
    fi
    if [ ! -f ${VCF_GATK}.gz ];
    then "$BGZIP" ${VCF_GATK}
    fi
    "$BCFTOOLS" index -f ${VCF_GATK}.gz

    # sort and index indels and snps of varscan
    "$BCFTOOLS" sort ${VCF_VARSCAN_INDEL}.gz -Oz -o ${VCF_VARSCAN_INDEL}.sorted.gz
    mv ${VCF_VARSCAN_INDEL}.sorted.gz ${VCF_VARSCAN_INDEL}.gz
    "$BCFTOOLS" index -f ${VCF_VARSCAN_INDEL}.gz
    "$BCFTOOLS" sort ${VCF_VARSCAN_SNP}.gz -Oz -o ${VCF_VARSCAN_SNP}.sorted.gz
    mv ${VCF_VARSCAN_SNP}.sorted.gz ${VCF_VARSCAN_SNP}.gz
    "$BCFTOOLS" index -f ${VCF_VARSCAN_SNP}.gz
    # concat indels and snps of varscan
    "$BCFTOOLS" concat -a \
    ${VCF_VARSCAN_INDEL}.gz \
    ${VCF_VARSCAN_SNP}.gz \
    -Oz -o ${VCF_VARSCAN}.gz
    "$BCFTOOLS" sort -Oz -o "${VCF_VARSCAN}.gz" "${VCF_VARSCAN}.gz"
    "$BCFTOOLS" index -f ${VCF_VARSCAN}.gz

    # use bcftools isec to find the intersection between GATK and VarScan VCFs
    "$BCFTOOLS" isec -c all ${VCF_GATK}.gz ${VCF_VARSCAN}.gz -p ${VCF_COMBINED_FOLDER}

    # move the intersection to the "INTERSECTION" folder
    if [[ -f "${VCF_COMBINED_FOLDER}/0003.vcf" ]]; then
      mv "${VCF_COMBINED_FOLDER}/0003.vcf" "${INTERSECTED_FOLDER}/${SAMPLENAME}.vcf"
    elif [[ -f "${VCF_COMBINED_FOLDER}/0003.vcf.gz" ]]; then
        mv "${VCF_COMBINED_FOLDER}/0003.vcf.gz" "${INTERSECTED_FOLDER}/${SAMPLENAME}.vcf.gz"
    else
        echo "Warning: no intersection VCF found for ${SAMPLENAME}"
    fi

done
