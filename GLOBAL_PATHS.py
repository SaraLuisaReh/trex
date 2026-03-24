import os
import platform
import sys

#CURRENT_PATH = os.getcwd()
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    CURRENT_PATH = sys._MEIPASS
else:
    # Running as normal Python script
    CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
BEDFILE_PATH= os.path.join(CURRENT_PATH, "ref_data", "target.bed")
REF_GENOME_PATH=os.path.join(CURRENT_PATH, "ref_data", "Homo_sapiens.GRCh38.dna.primary_assembly_bg.fa.gz")
CPG_FILEPATH=os.path.join(CURRENT_PATH, "ref_data", "cpg_positions.txt")
GNOMAD_PATH=os.path.join(CURRENT_PATH, "ref_data", "gnomad.exomes.v4.0.sites.slimmed_nochr.vcf.gz")
CLINVAR_PATH=os.path.join(CURRENT_PATH, "ref_data", "clinvar.vcf.gz")

# Detect OS and architecture
OS = platform.system()      # 'Linux' or 'Darwin'
ARCH = platform.machine()   # 'x86_64' or 'arm64'

# Determine the correct binary directory
if OS == "Linux" and ARCH == "x86_64":
    BIN_DIR = os.path.join(CURRENT_PATH, "apps", "linux_x86_64")
elif OS == "Darwin" and ARCH == "arm64":
    BIN_DIR = os.path.join(CURRENT_PATH, "apps", "macos_arm64")
else:
    sys.exit(f"Unsupported system: {OS} {ARCH}")