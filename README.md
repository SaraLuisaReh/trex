# T-Rex

---

## Overview

**T-Rex** (**T**rio **R**are variant analysis of **Ex**omes) is a desktop application for standardized and local analysis of Illumina whole exome sequencing germline trio data.

It enables users to process **FASTQ, BAM, VCF, CSV, and TSV files** with customizable filtering options for variant type, statistical significance, and population allele frequency based on the gnomAD database.

---

## Key Features

- Intuitive desktop GUI built with CustomTkinter (Python)  
- Compatible with macOS (arm64), Linux (x86, Ubuntu ≥24), and Windows (via WSL2 on Windows 11+)  
- End-to-end integrated analysis pipeline with:
  - Read preprocessing using **Trimmomatic**  
  - Alignment to GRCh38 reference genome using **BWA-MEM**  
  - Post-processing with **Picard**  
  - Variant calling by **GATK4 HaplotypeCaller** and **VarScan2**  
  - Variant annotation via **SnpEff / SnpSift**  
  - Quality control after each analysis step  
- Statistical tests supported: Chi-square test and Transmission Disequilibrium Test with automatic Bonferroni correction (α ≤ 0.05)  
- Filtering based on allele frequency from gnomAD v4.0 (European population >582,716 individuals)  
- Pathogenicity annotation using ClinVar data  
- Tested with 13 medical doctors and scientists for stability and intuitive user design

---

## Getting Started


### Installation & System Requirements

- **macOS:** arm64 (M1+ chips)  
- **Linux:** x86 architecture (Ubuntu 24+)  
- **Windows:** Windows 11 with **WSL2 enabled** (see [official WSL installation guide](https://learn.microsoft.com/en-us/windows/wsl/install))
- The app was tested on M1 chips and on Ubuntu 24.

### Launching the App

- For **macOS (arm64)** and **Linux (x86 Ubuntu ≥24)** users, we recommend to download the precompiled app from [Zenodo](https://doi.org/10.5281/zenodo.19135262).  
- For **Windows 11+** users, **WSL2** (Windows Subsystem for Linux 2) must be installed and activated before running the app. We then recommend downloading the precompiled Linux version from [Zenodo](https://doi.org/10.5281/zenodo.19135262).

> **Important:**  
> T-Rex runs inside WSL2 on Windows. Follow Microsoft’s official guide to install and enable WSL2:  
> https://learn.microsoft.com/en-us/windows/wsl/install

### Installation via GitHub on macOS and Linux

**1. Clone the repository:**

>git clone https://github.com/yourusername/trex.git

>cd trex

**2. Ensure Python 3.12 is installed**
>python3.12 --version

**3. Check that tkinter is installed**
_(Tkinter is a standard (built-in) Python library and is usually included with most Python installations.)_

>python3.12 -m tkinter

If a small window opens, tkinter is installed correctly.

If not:

On Ubuntu/Linux:

>sudo apt install python3-tk

On macOS:
Install Python via Homebrew or from the official Python installer, as tkinter is sometimes not included in system Python:

>brew install python@3.12

**4. Create a virtual environment**

>python3.12 -m venv venv

**5. Activate the virtual environment**
>source venv/bin/activate

**6. Install required Python packages**
>pip install --upgrade pip

>pip install -r requirements.txt

**7. Download required data and binaries from [Zenodo](https://doi.org/10.5281/zenodo.19077464):**

The T-Rex application requires both reference data and precompiled binaries, which are distributed via Zenodo.

i) Download the following archives:

ref_data.zip – reference datasets

apps_macos.zip – macOS binaries (macOS users only)

apps_linux.zip – Linux binaries (Linux users only)

ii) Extract and place files

**Reference data:**

- Unzip ref_data.zip

- Copy all files inside into: **ref_data/**

_Important: Only copy the individual files, not the outer folder.
**Do not rename or move the files**, as T-Rex relies on the exact file names for correct operation._

**Binaries:**

Unzip the correct archive for your system:

macOS:

- Extract apps_macos.zip
  
- Copy contents into: **apps/**

Linux:

- Extract apps_linux.zip
  
- Copy contents into: **apps/**

_For the fully precompiled T-Rex app from Zenodo: You do not need to download this reference dataset nor binaries. The precompiled app already includes all necessary reference files and binaries._

**8. Run the application:**
> python view.py

**9. Fixing Execution Permissions**

In some cases, the downloaded app may not have the correct execution permissions.

To fix this, run:

> chmod -R u+x /path/to/your/folder

This grants execution rights to all files in the folder for your user.

If you prefer a more restrictive approach (only making files executable):

> find /path/to/your/folder -type f -exec chmod +x {} ;

---

## Starting an Analysis

- Click **“New Analysis”** in the app and follow the on-screen instructions.

### Input File Formats

- Supports FASTQ, BAM, VCF, CSV, and TSV input files.  
- For **TSV/CSV input**, the file must include these exact headers (order doesn’t matter):
    - sample
    - location (format: chromosome:position, e.g. 9:141950, no 'chr')
    - ref (reference base)
    - alt (alternate/variant base)
    - biotype (protein coding variants must be 'protein_coding')
    - af_c (allele frequency of the child, decimal ≤ 1.0)
    - af_f (allele frequency of the father)
    - af_m (allele frequency of the mother)
    - gnomad_af (allele frequency in reference population)
    - gnomad_an (allele number in reference population)


- **Recommendation:** We recommend to start the analysis with FASTQ, BAM or VCF files due to the stricter format requirements for TSV/CSV files.

### Test Files
T-Rex can be tested by downloading the file “trio-test-data.zip” from [Zenodo](https://doi.org/10.5281/zenodo.19135262).
The dataset contains FASTQ, BAM, VCF, and TSV files from three artificial trios.

The dataset is very small and only requires a few minutes to run.

The dataset includes four variants with a gnomAD allele frequency of approximately 85%.
To ensure that all variants are displayed in the application, please set the maximum allele frequency to 100%.

---

## Source Code & Citation

The full source code is available on GitHub.
If you use this software, please cite it via its [Zenodo archive DOI](https://doi.org/10.5281/zenodo.19135262). In addition, we kindly ask you to cite the associated preprint:

Reh, S.-L., Walter, C., Lohse, J., Ghete, T., Metzler, M., Quante, A., Hauer, J., & Auer, F. (2026). T-Rex: Standardized Analysis of Germline Variants in Whole-Exome Sequencing Trios. bioRxiv. [https://doi.org/10.64898/2026.03.30.715083](https://doi.org/10.64898/2026.03.30.715083).

---

## Credits


- **Code developed by:** Sara-Luisa Reh, Carolin Walter  
- **Supervisors:** Franziska Auer, Julia Hauer  
- **Contributors:** Judith Lohse, Tabita Ghete, Markus Metzler, Anne Quante, Arndt Borkhardt  
- **Logo design:** Anne-Christine Reh
- **Acknowledgments** We thank the 13 medical doctors and scientists who participated in user testing for their valuable feedback.

---

## Reference Data

T-Rex uses publicly available reference datasets:
- Ensembl GRCh38 (© EMBL-EBI and the Ensembl project, CC BY 4.0)
- gnomAD v4.0 (© Broad Institute, CC BY 4.0)
- ClinVar (NCBI, Public Domain)

Preprocessed reference files compatible with T-Rex are available on Zenodo.

These files are derived from the original datasets and have been modified
(e.g., formatting, filtering, indexing) for compatibility with the pipeline.

Full license and attribution information is provided in `licenses.txt`. Full scientific citations for these datasets are provided in the associated publication.

---

## License

- T-Rex is licensed under the **GNU General Public License v3.0 (GPLv3)**.  
- See the included LICENSE and LICENSES.txt files for third-party tools and dependencies.

---

## Disclaimer

THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. USE IT AT YOUR OWN RISK.


