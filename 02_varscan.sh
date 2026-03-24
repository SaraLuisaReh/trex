#!/bin/bash

REFGENOME=$4
SAMPLENAMES=$1
INPUTPATH=$2
OUTPUTPATH=$3

# RAM requirement: 4 GB

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
SAMTOOLS="${BINDIR}/samtools"
VARSCAN_JAR="${PARENTPATH}/apps/varscan"
BAM_READCOUNT="${BINDIR}/bam-readcount"
JAVA_PATH="${BINDIR}/java/bin/java"

READFROM="${INPUTPATH}/"
WRITETO="${OUTPUTPATH}/varscan/"
TEMP="${OUTPUTPATH}/tempVariantsVarscan/"

mkdir -p ${WRITETO}/log ${TEMP}


for SAMPLENAME in ${SAMPLENAMES[*]} ; do

    LOG_MPILEUP=${WRITETO}/log/${SAMPLENAME}_log_mpileup.txt
    LOG_BAM_READCOUNT=${WRITETO}/log/${SAMPLENAME}_log_bam_readcount.txt
    LOG_VARSCAN=${WRITETO}/log/${SAMPLENAME}_log_VarScan.txt
    LOG_VARSCAN_FPFILTER=${WRITETO}/log/${SAMPLENAME}_log_VarScan_fpfilter.txt

    BAM_F=${READFROM}/${SAMPLENAME}_f.bam
    BAM_M=${READFROM}/${SAMPLENAME}_m.bam
    BAM_C=${READFROM}/${SAMPLENAME}_c.bam

    "${SAMTOOLS}" mpileup -B -q 1 -f ${REFGENOME} ${BAM_F} ${BAM_M} ${BAM_C} \
        > ${TEMP}${SAMPLENAME}.mpileup 2> ${LOG_MPILEUP}

    echo ${TEMP}${SAMPLENAME}.mpileup
    echo ${WRITETO}/${SAMPLENAME}

    "${JAVA_PATH}" -Xmx4g -jar "${VARSCAN_JAR}.jar" trio ${TEMP}${SAMPLENAME}.mpileup ${WRITETO}/${SAMPLENAME} \
        --min-coverage 10 --min-var-freq 0.20 --p-value 0.05 -adj-var-freq 0.05 -adj-p-value 0.05 \
        2> ${LOG_VARSCAN_FPFILTER}

    for TYPE in snp indel; do

        if [ ${TYPE} = snp ]
        then
            grep -v "#" ${WRITETO}/${SAMPLENAME}.${TYPE}.vcf | awk '{OFS="\t"; print $1,$2,$2}' > ${TEMP}${SAMPLENAME}.${TYPE}.tab
        else
            grep -v "#" ${WRITETO}/${SAMPLENAME}.${TYPE}.vcf | awk '{OFS="\t"; print $1,$2-10,$2+10}' > ${TEMP}${SAMPLENAME}.${TYPE}.tab
        fi

    "${BAM_READCOUNT}" --min-mapping-quality 1 --min-base-quality 20 --reference-fasta ${REFGENOME} \
        --site-list ${TEMP}${SAMPLENAME}.${TYPE}.tab --max-warnings 20 ${BAM_C} \
        > ${TEMP}${SAMPLENAME}.${TYPE}.bam.readcount 2>> ${LOG_BAM_READCOUNT}

    "${JAVA_PATH}" -Xmx4g -jar "${VARSCAN_JAR}.jar" fpfilter ${WRITETO}/${SAMPLENAME}.${TYPE}.vcf ${TEMP}${SAMPLENAME}.${TYPE}.bam.readcount \
        --output-file ${WRITETO}/${SAMPLENAME}.${TYPE}.pass.vcf \
        --filtered-file ${WRITETO}/${SAMPLENAME}.${TYPE}.filtered.vcf \
        2> ${LOG_VARSCAN_FPFILTER}_${TYPE}.txt

    done

    rm ${TEMP}${SAMPLENAME}.mpileup

done


