# Copyright (c) 2026 Sara-Luisa Reh
# Licensed under the GNU General Public License v3.0

import os
import subprocess
from annotation import convert_vcf_files_to_tsv


def return_script_success(result, script_type):
    if result.returncode == 0:
        return script_type
    else:
        # Print the output (stdout) and error (stderr)
        print("Output:", result.stdout)
        print("Error:", result.stderr)
        return "FAIL"

def alignment(script_path, sample_names_string, input_folder, output_folder, reference_genome, bedfile):
    # sample_names_string has form "trio1 trio2 trio3"
    # Run Alignment bash script
    try:
        result = subprocess.run([script_path, sample_names_string, input_folder, output_folder, reference_genome, bedfile], capture_output=True, check=True, text=True)
    except subprocess.CalledProcessError:
        return "Alignment FAIL"
    # return if Success
    return return_script_success(result, "bam")

def varscan_variant_calling(script_path, sample_names_string, input_folder, output_folder, reference_genome):
    # sample_names_string has form "trio1 trio2 trio3"
    # Run Varscan bash script
    try:
        result = subprocess.run([script_path, sample_names_string, input_folder, output_folder, reference_genome],
                            capture_output=True, check=True, text=True)
    except subprocess.CalledProcessError:
        return "FAIL"
    # return if Success
    return return_script_success(result, "vcf_var")

def gatk_variant_calling(script_path, sample_names_string, input_folder, output_folder, reference_genome, bedfile):
    # sample_names_string has form "trio1 trio2 trio3"
    # Run GATK bash script
    try:
        result = subprocess.run([script_path, sample_names_string, input_folder, output_folder, reference_genome, bedfile],
                            capture_output=True, check=True, text=True)
    except subprocess.CalledProcessError:
        return "FAIL"
    # return if Success
    return return_script_success(result, "vcf_gatk")

def variant_calling(varscan_script_path, gatk_script_path, vc_combi_path, sample_names_string, input_folder, output_folder, reference_genome, bedfile):
    # first call varscan
    print("varscan")
    varscan_result = varscan_variant_calling(varscan_script_path, sample_names_string, input_folder, output_folder, reference_genome)
    print(varscan_result)
    # then call gatk
    print("gatk")
    gatk_result = gatk_variant_calling(gatk_script_path, sample_names_string, input_folder, output_folder, reference_genome, bedfile)
    # then combine
    print(varscan_result, gatk_result)
    if varscan_result=="vcf_var" and gatk_result=="vcf_gatk":
        # combine gatk and varscan
        try:
            result = subprocess.run([vc_combi_path, output_folder, sample_names_string],capture_output=True, check=True, text=True)
            return return_script_success(result, "vcf")
        except subprocess.CalledProcessError:
            return "FAIL"
    else:
        if varscan_result=="vcf_var" and gatk_result=="FAIL":
            return "FAIL"
        if gatk_result=="vcf_gatk" and varscan_result=="FAIL":
            return "FAIL"
        else:
            return "FAIL"

def snpeff_annotation(script_path, sample_names_string, input_folder, output_folder, gnomad_path, clinvar_path):
    try:
        result = subprocess.run([script_path, sample_names_string, input_folder, output_folder,gnomad_path, clinvar_path],
                            capture_output=True, check=True, text=True)
    except subprocess.CalledProcessError:
        return "FAIL"
    # return if Success
    return return_script_success(result, "snpeff")

def annotation(script_path, sample_names_string, input_folder, output_folder, gnomad_path, clinvar_path):
    snpeff_result = snpeff_annotation(script_path, sample_names_string, input_folder, output_folder, gnomad_path, clinvar_path)
    print(snpeff_result)
    if snpeff_result=="snpeff":
        new_input_path = os.path.join(output_folder, "annotated_vcf")
        convertion_result = convert_vcf_files_to_tsv(new_input_path, output_folder, sample_names_string)
        if convertion_result=="success":
            return "tsv"
        else:
            return "FAIL"
    else:
        return "FAIL"



