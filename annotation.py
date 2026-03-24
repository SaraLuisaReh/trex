# Copyright (c) 2026 Sara-Luisa Reh
# Licensed under the GNU General Public License v3.0

import csv
import os

INPUT_VCF = "annotated.vcf"
OUTPUT_TSV = "output.tsv"
SAMPLE_ROLES = ["father", "mother", "child"]

# TSV headers
tsv_headers = [
    "variantID", "Gene", "Location", "Feature_type", "Feature_id", "Consequence",
    "Existing_variation", "SYMBOL", "BIOTYPE", "EXON", "INTRON", "HGVSc", "HGVSp",
    "ref", "alt", "chr", "MAPINFO", "impact",
    "dp_c", "dp_m", "dp_f",
    "af_c", "af_m", "af_f",
    "af_c_predicted", "af_m_predicted", "af_f_predicted",
    "gnomAD_AC", "gnomAD_AN","gnomAD_AF","gnomAD_nhomalt",
    "gnomAD_AC_nfe", "gnomAD_AN_nfe", "gnomAD_AF_nfe",
    "gnomAD_AC_fin", "gnomAD_AN_fin", "gnomAD_AF_fin",
    "gnomAD_AC_european", "gnomAD_AN_european", "gnomAD_AF_european",
    "ClinVar_Significance",
    "ClinVar_ReviewStatus",
    "ClinVar_Disease",
    "ClinVar_VariantType",
    "ClinVar_Origin",
    "ClinVar_Conflicting",
    "Annotation",
    "Sample"
]

# Helper functions
def compute_af(gt):
    if gt in [None, ".", "./.", ".|."]:
        return ""
    alleles = gt.replace("|","/").split("/")
    total = len(alleles)
    alt = sum(1 for a in alleles if a != "0" and a != ".")
    return alt / total

def get_af(freq):
    if freq in [None, ".", "./.", ".|."]:
        return ""
    freq=freq.replace(",", ".")
    new_freq = round(float(freq.strip("%"))/100,3)
    return new_freq

def parse_info(info_str):
    #Convert info field to a dict
    info_dict = {}
    for field in info_str.split(";"):
        if "=" in field:
            key, val = field.split("=",1)
            info_dict[key] = val
        else:
            info_dict[field] = True
    return info_dict

def parse_format(format_str, sample_str):
    #Convert format and sample column into a dict
    keys = format_str.split(":")
    values = sample_str.split(":")
    return dict(zip(keys, values))

def split_and_sum(value):
    if value in ("", ".", "-1", None):
        return -1
    try:
        return sum(int(v) for v in value.split(",") if v.isdigit())
    except ValueError:
        print("error in split_and_sum")
        print(value)
        return -1

def safe_sum(a, b):
    if a >= 0 and b >= 0:
        return a + b
    return -1

def compute_af_from_ac_an(ac, an, af):
    if af in ("", ".", "-1", None) or "," in af:
        try:
            if ac >= 0 and an > 0:
                return round(ac / an, 5)
        except ZeroDivisionError:
            pass
        return -1
    else:
        # if af is already computed: do not recompute
        return af


# main function
def convert_annotated_vcf_to_tsv(input_vcf_file, output_tsv_file, sample_name):
    person_to_column = {}
    with open(input_vcf_file, "r") as vcf:
        with open(output_tsv_file, "w", newline='') as tsv:
            # write header
            writer = csv.DictWriter(tsv, fieldnames=tsv_headers, delimiter="\t")
            writer.writeheader()
            # read vcf file
            for line in vcf:
                if line.startswith("##"):
                    continue
                if line.startswith("#CHROM"):
                    headers=line.strip().split("\t")
                    # store column of father, mother, and child in dictionnary
                    for i in range(9,len(headers)):
                        person_to_column[headers[i].lower()]=i
                    continue
                elif not line or line.startswith("#"):
                    continue
                else:
                    # Parse VCF line
                    parts = line.strip().split("\t")
                    chrom, pos, vid, ref, alt, qual, filt, info_str, format_str = parts[:9]
                    if filt.lower()=="pass":
                        chrom=chrom.replace("chr","")
                        samples = {role: parts[person_to_column[role]] for role in SAMPLE_ROLES}

                        # Parse INFO field
                        info_dict = parse_info(info_str)

                        # Raw INFO values
                        raw_ac = info_dict.get("AC", "-1")
                        raw_an = info_dict.get("AN", "-1")
                        raw_af = info_dict.get("AF", "-1")
                        raw_ac_nfe = info_dict.get("AC_nfe", "-1")
                        raw_an_nfe = info_dict.get("AN_nfe", "-1")
                        raw_af_nfe = info_dict.get("AF_nfe", "-1")
                        raw_ac_fin = info_dict.get("AC_fin", "-1")
                        raw_an_fin = info_dict.get("AN_fin", "-1")
                        raw_af_fin = info_dict.get("AF_fin", "-1")
                        raw_nhomalt = info_dict.get("nhomalt", "-1")

                        # Sum AC / AN / nhomalt over alleles
                        gnomad_ac = split_and_sum(raw_ac)
                        gnomad_an = split_and_sum(raw_an)
                        gnomad_nhomalt = split_and_sum(raw_nhomalt)
                        gnomad_ac_nfe = split_and_sum(raw_ac_nfe)
                        gnomad_an_nfe = split_and_sum(raw_an_nfe)
                        gnomad_ac_fin = split_and_sum(raw_ac_fin)
                        gnomad_an_fin = split_and_sum(raw_an_fin)

                        # Recompute AF from AC / AN if ac/an is comma-separated. If not, return the raw values
                        gnomad_af = compute_af_from_ac_an(gnomad_ac, gnomad_an, raw_af)
                        gnomad_af_nfe = compute_af_from_ac_an(gnomad_ac_nfe, gnomad_an_nfe, raw_af_nfe)
                        gnomad_af_fin = compute_af_from_ac_an(gnomad_ac_fin, gnomad_an_fin, raw_af_fin)

                        # Compute european values
                        gnomad_an_european = safe_sum(gnomad_an_fin, gnomad_an_nfe)
                        gnomad_ac_european = safe_sum(gnomad_ac_fin, gnomad_ac_nfe)
                        gnomad_af_european=compute_af_from_ac_an(gnomad_ac_european, gnomad_an_european, "")

                        # extract clinvar fields
                        clinvar_sig = info_dict.get("CLNSIG", "")
                        clinvar_revstat = info_dict.get("CLNREVSTAT", "")
                        clinvar_disease = info_dict.get("CLNDN", "")
                        clinvar_vartype = info_dict.get("CLNVC", "")
                        clinvar_origin = info_dict.get("CLNORIGIN", "")
                        clinvar_conflict = info_dict.get("CLNSIGCONF", "")

                        # Flatten ANN field
                        ann_list = info_dict.get("ANN", "").split(",")
                        if not ann_list or ann_list[0] == "":
                            first_ann_fields = []
                        else:
                            # take only the first transcript
                            first_ann = ann_list[0]
                            first_ann_fields = first_ann.split("|")

                        # make sure there are enough fields
                        while len(first_ann_fields) < 12:
                            first_ann_fields.append("")

                        allele = first_ann_fields[0]
                        consequence = first_ann_fields[1]
                        impact = first_ann_fields[2]
                        gene = first_ann_fields[3]
                        gene_id = first_ann_fields[4]
                        feature_type = first_ann_fields[5]
                        feature_id = first_ann_fields[6]
                        biotype = first_ann_fields[7]
                        if "protein_coding" in biotype:
                            exon = first_ann_fields[8]
                            intron = ""
                        else:
                            exon = ""
                            intron = first_ann_fields[8]
                        hgvsc = first_ann_fields[9]
                        hgvsp = first_ann_fields[10]

                        # Per-sample AF and DP
                        dp_c = parse_format(format_str, samples["child"]).get("DP", "")
                        dp_m = parse_format(format_str, samples["mother"]).get("DP", "")
                        dp_f = parse_format(format_str, samples["father"]).get("DP", "")

                        af_c_predicted = compute_af(parse_format(format_str, samples["child"]).get("GT", ""))
                        af_m_predicted = compute_af(parse_format(format_str, samples["mother"]).get("GT", ""))
                        af_f_predicted = compute_af(parse_format(format_str, samples["father"]).get("GT", ""))

                        af_c = get_af(parse_format(format_str, samples["child"]).get("FREQ", ""))
                        af_m = get_af(parse_format(format_str, samples["mother"]).get("FREQ", ""))
                        af_f = get_af(parse_format(format_str, samples["father"]).get("FREQ", ""))


                        # Write row using only first transcript
                        writer.writerow({
                            "variantID": f"{chrom}:{pos}_{ref}/{alt}",
                            "Gene": gene_id,
                            "Location": f"{chrom}:{pos}",
                            "Feature_type": feature_type,
                            "Feature_id" : feature_id,
                            "Consequence": consequence,
                            "Existing_variation": vid,
                            "SYMBOL": gene,
                            "BIOTYPE": biotype,
                            "EXON": exon,
                            "INTRON": intron,
                            "HGVSc" : hgvsc,
                            "HGVSp" : hgvsp,
                            "ref": ref,
                            "alt": alt,
                            "chr": chrom,
                            "MAPINFO": pos,
                            "impact": impact,
                            "dp_c": dp_c,
                            "dp_m": dp_m,
                            "dp_f": dp_f,
                            "af_c": af_c,
                            "af_m": af_m,
                            "af_f": af_f,
                            "af_c_predicted": af_c_predicted,
                            "af_m_predicted": af_m_predicted,
                            "af_f_predicted": af_f_predicted,
                            "gnomAD_AC": gnomad_ac,
                            "gnomAD_AN": gnomad_an,
                            "gnomAD_AF": gnomad_af,
                            "gnomAD_nhomalt": gnomad_nhomalt,
                            "gnomAD_AC_nfe": gnomad_ac_nfe,
                            "gnomAD_AN_nfe": gnomad_an_nfe,
                            "gnomAD_AF_nfe": gnomad_af_nfe,
                            "gnomAD_AC_fin": gnomad_ac_fin,
                            "gnomAD_AN_fin": gnomad_an_fin,
                            "gnomAD_AF_fin": gnomad_af_fin,
                            "gnomAD_AC_european": str(gnomad_ac_european),
                            "gnomAD_AN_european": str(gnomad_an_european),
                            "gnomAD_AF_european": str(gnomad_af_european),
                            # ClinVar
                            "ClinVar_Significance": clinvar_sig,
                            "ClinVar_ReviewStatus": clinvar_revstat,
                            "ClinVar_Disease": clinvar_disease,
                            "ClinVar_VariantType": clinvar_vartype,
                            "ClinVar_Origin": clinvar_origin,
                            "ClinVar_Conflicting": clinvar_conflict,
                            "Annotation": info_dict.get("ANN", ""),
                            "Sample": sample_name
                        })

def convert_vcf_files_to_tsv(inputfolder, outputfolder, sample_name_string):
    try:
        sample_names = sample_name_string.split(" ")
        for samplename in sample_names:
            inputfilepath = os.path.join(inputfolder, f"{samplename}.annotated.vcf")
            outputfilepath = os.path.join(outputfolder,"tsv", f"{samplename}.tsv")
            os.makedirs(os.path.dirname(outputfilepath), exist_ok=True)
            convert_annotated_vcf_to_tsv(inputfilepath, outputfilepath, samplename)
        return "success"
    except IndexError:
        return "FAIL"
