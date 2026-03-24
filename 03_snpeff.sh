#!/bin/bash

SAMPLENAMES=$1
INPUTPATH=$2
OUTPUTPATH=$3
GNOMADPATH=$4
CLINVARPATH=$5

# RAM requirement: 8 GB

PARENTPATH="$(cd "$(dirname "$(realpath "$0")")" && pwd)"
# Get the system's-specific package path
OS="$(uname -s)"
ARCH="$(uname -m)"
if [[ "$OS" == "Darwin" && "$ARCH" == "arm64" ]]; then
  BINDIR="$PARENTPATH/apps/macos_arm64"
elif [[ "$OS" == "Linux" && "$ARCH" == "x86_64" ]]; then
  BINDIR="$PARENTPATH/apps/linux_x86_64"
fi
# Get packages
SNPEFF="${PARENTPATH}/apps/snpeff/snpEff"
SNPSIFT="${PARENTPATH}/apps/snpeff/SnpSift"
JAVA_PATH="${BINDIR}/java/bin/java"

READFROM="${INPUTPATH}"
WRITETO="${OUTPUTPATH}/annotated_vcf/"

mkdir -p ${WRITETO}

for SAMPLENAME in ${SAMPLENAMES[*]} ; do
    INPUTFILE=${READFROM}/${SAMPLENAME}.vcf
    OUTPUTFILE=${WRITETO}/${SAMPLENAME}

    # annotate with SNPeff, SNPSIFT (gnomad) and SNPSIFT (clinvar)
    # if also intergenic variants shall be annotated or canonical variants shall be preferred: add -no-intergenic or -canon
    "${JAVA_PATH}" -Xmx8g -jar "${SNPEFF}.jar" -noStats -v GRCh38.99 "${INPUTFILE}" \
    | "${JAVA_PATH}" -Xmx8g -jar "${SNPSIFT}.jar" annotate "${GNOMADPATH}" \
    | "${JAVA_PATH}" -Xmx8g -jar "${SNPSIFT}.jar" annotate "${CLINVARPATH}" \
    > "${OUTPUTFILE}.annotated.vcf"

done
