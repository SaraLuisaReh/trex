# Copyright (c) 2026 Sara-Luisa Reh
# Licensed under the GNU General Public License v3.0

relevant_headers = [
    "af_c","af_m","af_f","dp_c","dp_f","dp_m","gene","location","feature_type","consequence","existing_variation","symbol","biotype","exon","intron",
    "ref","alt","chr","mapinfo","sample", "gnomad_ac", "gnomad_an", "gnomad_af", "gnomad_ac_nfe", "gnomad_an_nfe", "gnomad_af_nfe", "gnomad_ac_european", "gnomad_an_european", "gnomad_af_european"
]

excluded_headers_outputfile = ["af_c","af_m","af_f","af_c_predicted","af_f_predicted", "af_m_predicted", "dp_c","dp_f","dp_m", "sample"]

def store_input_line_in_dict(seperator, input_line, col_to_header_dict):
    output_dict = {}
    lineparts = input_line.strip("\n").split(seperator)
    relevant_cols = col_to_header_dict.keys()
    for i in range(len(lineparts)):
        if i in relevant_cols:
            content = lineparts[i]
            if col_to_header_dict[i]=="sample":
                output_dict["af_f"] = 1
            # store content in output_dict under the associated header
            output_dict[col_to_header_dict[i]] = content
    return output_dict


def store_position_of_relevant_headers(seperator,relevant_headers, header_line):
    col_to_header = {}
    # store position of relevant headers in col_to_header_dict
    header_parts = header_line.strip("\n").split(seperator)
    for i in range(len(header_parts)):
        # store header in small letters
        header = header_parts[i].lower()
        if header in relevant_headers:
            col_to_header[i] = header
        elif header.startswith("gnomad") and header.endswith("af"):# and "european" in header: # in case of gnomAD allow extensions, but it must include the allele frequency af
            col_to_header[i] = "gnomad_af"
        elif header.startswith("gnomad") and header.endswith("an"):# and "european" in header:
            col_to_header[i] = "gnomad_an"
    return col_to_header



