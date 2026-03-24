# Copyright (c) 2026 Sara-Luisa Reh
# Licensed under the GNU General Public License v3.0

import argparse
from read_variant_file import filter_for_variants
from analysis_pipeline import alignment, variant_calling, annotation
import os
from GLOBAL_PATHS import CURRENT_PATH, REF_GENOME_PATH, BEDFILE_PATH, CPG_FILEPATH, GNOMAD_PATH, CLINVAR_PATH

# Global dict to store functions used to analyses the filetype (key)
analysis_function_dict = {
    "tsv": filter_for_variants,
    "csv": filter_for_variants,
    "fastq": alignment,
    "bam": variant_calling,
    "vcf": annotation
}

bash_scripts = {
    "fastq":os.path.join(CURRENT_PATH, "01_alignment_single_end.sh"),
    "varscan": os.path.join(CURRENT_PATH, "02_varscan.sh"),
    "gatk": os.path.join(CURRENT_PATH, "02_gatk.sh"),
    "bam": os.path.join(CURRENT_PATH, "02_combine_gatk_varscan.sh"),
    "vcf": os.path.join(CURRENT_PATH, "03_snpeff.sh")
}


def create_analysis_input_dict(input_folder, csv_or_tsv, output_folder, cutoff, ref_pop_suffix, cpgfilepath, sample_names_string, reference_genome, bedfile, option_dict, analysis_type, gnomadfile, clinvarfile):
    # check and store input_folder
    input_folder_dict = {}
    for analysis in ["tsv", "csv", "fastq", "bam", "vcf"]:
        if analysis==analysis_type:
            input_folder_dict[analysis]=input_folder
        else:
            input_folder_dict[analysis]=output_folder+"/"+analysis

    # Map analysis types to their respective input parameters.
    analysis_input_dict = {
        "tsv": (input_folder_dict["tsv"], csv_or_tsv, output_folder, cutoff, ref_pop_suffix, cpgfilepath, option_dict),
        "csv": (input_folder_dict["csv"], csv_or_tsv, output_folder, cutoff, ref_pop_suffix, cpgfilepath, option_dict),
        "fastq": (bash_scripts["fastq"], sample_names_string, input_folder_dict["fastq"], output_folder, reference_genome, bedfile),
        "bam": (bash_scripts["varscan"], bash_scripts["gatk"], bash_scripts["bam"], sample_names_string, input_folder_dict["bam"], output_folder, reference_genome, bedfile),
        "vcf": (bash_scripts["vcf"], sample_names_string, input_folder_dict["vcf"], output_folder, gnomadfile, clinvarfile)
    }
    return analysis_input_dict

def get_sample_names_string(input_folder, analysis_type):
    sample_set = set()
    for inputfile in os.listdir(input_folder):
        if not (
            inputfile.endswith(analysis_type)
            or inputfile.endswith(analysis_type + ".gz")
        ):
            continue
        base = inputfile
        # remove .gz if present
        if base.endswith(".gz"):
            base = base[:-3]
        # remove main extension (.fastq, .bam, .vcf, ...)
        base = base.rsplit(".", 1)[0]
        # only modify fastq/bam sample names
        if analysis_type in {"fastq", "bam"}:
            parts = base.split("_")
            # handle *_m_1 / *_c_2 / *_f_1
            if len(parts) >= 3 and parts[-2] in {"m", "c", "f"} and parts[-1] in {"1", "2"}:
                base = "_".join(parts[:-2])
            # handle *_m / *_c / *_f
            elif len(parts) >= 2 and parts[-1] in {"m", "c", "f"}:
                base = "_".join(parts[:-1])
        sample_set.add(base)
    return " ".join(sorted(sample_set))

# simulate analysis pipeline
def control_analysis(input_folder, analysis_type, output_folder, cutoff, ref_pop_suffix, option_dict, progress_callback=None, stop_event=None, **kwargs):
    try:
        # get optional finish of function
        pipeline_endpoint = kwargs.get("end", "finish")
        # get sample_names_string
        sample_names_string = kwargs.get("samples", None)
        if sample_names_string is None:
            sample_names_string = get_sample_names_string(input_folder, analysis_type)
        # Create dict for analysis inputs
        csv_or_tsv = analysis_type if analysis_type == "csv" else "tsv"
        analysis_input_dict = create_analysis_input_dict(input_folder, csv_or_tsv, output_folder, cutoff, ref_pop_suffix, CPG_FILEPATH, sample_names_string, REF_GENOME_PATH, BEDFILE_PATH, option_dict, analysis_type, GNOMAD_PATH, CLINVAR_PATH)
        # Set initial analysis step
        nextfile = analysis_type
        # Process pipeline until the last step (either defined in kwargs or "finish")
        while nextfile != pipeline_endpoint and nextfile !="FAIL" and nextfile != "finish":
            # Call function for the current analysis step
            analysis_function = analysis_function_dict.get(nextfile)
            if stop_event and stop_event.is_set():
                return "Analysis successfully aborted by user."
            if progress_callback:
                progress_callback("Analyzing "+str(nextfile)+"...")
            print(nextfile)
            if analysis_function:
                nextfile = analysis_function(*analysis_input_dict[nextfile])  # Unpack the inputs
            else:
                print(f"Unknown analysis type: {nextfile}")
                return "The file type you have entered is unknown."
        if nextfile=="FAIL":
            return "Error during file analysis. Have you entered the right file type? Do your files contain data?"
        return "The Analysis has been finished successfully. You can find your results in the output folder specified in the beginning."
    except Exception as e:
        return "Error during File Analysis. Have you entered the right File Type?"

if __name__=="__main__":
    import argparse

    # Set up argparse to handle command-line arguments
    parser = argparse.ArgumentParser(description="Get input and output folder, with optional end and samples")
    # Required positional arguments
    parser.add_argument("inputfolder", help="Input folder")
    parser.add_argument("outputfolder", help="Output folder")
    # Optional arguments
    parser.add_argument("--start", default="fastq", help="File type at start (default: fastq)")
    parser.add_argument("--end", default="tsv", help="Final file type (default: tsv)")
    parser.add_argument("--samples", default=None, help="Sample name (default: none -> analysis of all samples in input folder)")

    # Parse arguments from the command line
    args = parser.parse_args()

    # Call controller
    options = {
        "homozygous": True,
        "protein_coding": True,
        "cpg": False,
        "chi_square": False,
        "tdt": False,
        "denovo": False
    }
    print(control_analysis(
        args.inputfolder,
        args.start,
        args.outputfolder,
        81,
        "",
        option_dict=options,
        #end=args.end,
        samples=args.samples
    ))
