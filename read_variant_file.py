# Copyright (c) 2026 Sara-Luisa Reh
# Licensed under the GNU General Public License v3.0

import os
from statistics import statistical_test_for_unpaired_groups, transm_disequ_test
from relevant_csv_headers import store_input_line_in_dict, store_position_of_relevant_headers, relevant_headers, excluded_headers_outputfile
# currently used entries of linedict: af_c, af_f, af_m, gnomad_af,gnomad_af_nfe, gnomad_af_european, gnomad_an, gnomad_an_nfe, gnomad_an_european, biotype, location, alt, ref

significance_level = 0.05

def filter_for_variants(inputfolder, inputfiletype, outputpath, cutoff, ref_pop_suffix, cpg_filepath, option_dict):
    try:
        filter_file_for_variants(inputfolder, inputfiletype, outputpath, cutoff,ref_pop_suffix, cpg_filepath, option_dict)
        return "finish"
    except Exception as e:
        return "FAIL"


def filter_file_for_variants(inputfolder, inputfiletype, outputpath, cutoff, ref_pop_suffix, cpg_filepath, option_dict):
    print(option_dict)
    # if cpg: get cpg_positions
    cpg_dict = {}   # has form chr:set(pos1, pos2)
    if option_dict["cpg"]:
        cpg_dict=read_cpg_file(cpg_filepath)
    # prepare file reading
    cutoff = float(cutoff)/100 # cutoff input is in percent
    print(cutoff)
    sep="," if inputfiletype=="csv" else "\t"

    # open outputfile
    outputfilename ="trio_analysis_filtered_for" + get_outputfilenamesuffix(option_dict,
                                                                                cutoff) + "." + inputfiletype
    outputfilepath = os.path.join(outputpath, outputfilename)
    with open(outputfilepath, "w") as outputfile:
        # prepare variables to store filtered variants
        variant_to_n_and_trio_dict = {}  # has form variant:[n, set(trios)]
        variant_to_outputline_dict = {}  # has form variant:[relevant_line_parts]
        variant_to_af_ref = {}  # has form variant:allele frequency in the reference population
        variant_to_an_ref = {}
        variant_to_hetero_parents = {}  # has form variant: number of heterozygous parents with variant
        variant_to_child_of_hetero_parents = {}  # has form variant: number of children of heterozygous parents with variant (including de novo)
        sample_set = set()

        # get files in folder
        firstfile=True
        for inputfile in os.listdir(inputfolder):
            if inputfile.endswith(inputfiletype) or inputfile.endswith("txt"):
                inputfilepath=os.path.join(inputfolder, inputfile)
                # open and read file
                with open(inputfilepath, "r", encoding='utf-8', errors='ignore') as readfile:
                    header=True
                    for line in readfile:
                        if header:
                            # get position of headers for file reading
                            col_to_header_dict = store_position_of_relevant_headers(sep, relevant_headers, line)
                            header = False
                            # get postions of headers that should be written in outputfile and write in outputfile
                            relevant_output_cols, output_header = get_header_for_outputfile(sep, line, option_dict, excluded_headers_outputfile)
                            if firstfile:
                                outputfile.write(output_header)
                                firstfile=False
                        else:
                            line_dict = store_input_line_in_dict(sep, line, col_to_header_dict)
                            try:
                                # if statistical testing: store sample in sample_set
                                if option_dict["tdt"] or option_dict["chi_square"]:
                                    sample_set.add(line_dict["sample"])
                                # in each case: first filter cutoff of variant and check if variant fulfils filtering options
                                if 0<= float(line_dict["gnomad_af"+ref_pop_suffix])<= cutoff and float(line_dict["gnomad_an"+ref_pop_suffix])>=100 and variant_is_accepted_without_significance(option_dict,line_dict, cpg_dict):
                                    variant = line_dict["location"] + "_" + line_dict["ref"] + "/" + line_dict["alt"]
                                    # check if tdt shall be checked -> also allele frequencies of the parents have to be considered
                                    if option_dict["tdt"]:
                                        test_for_tdt(variant_to_hetero_parents, variant, line_dict,
                                                     variant_to_child_of_hetero_parents)
                                    if float(line_dict["af_c"])>=0.3:
                                        # store data of filtered variant in dicts
                                        store_data_of_filtered_variant(variant, variant_to_n_and_trio_dict,
                                                                       variant_to_outputline_dict, line, relevant_output_cols,
                                                                       sep, line_dict["sample"], float(line_dict["af_c"]))
                                        # if chi square test shall be performed: store allele frequency of reference population in dict
                                        if option_dict["chi_square"] and variant not in variant_to_af_ref.keys():
                                            variant_to_af_ref[variant]=line_dict["gnomad_af"+ref_pop_suffix]
                                            variant_to_an_ref[variant] = line_dict["gnomad_an"+ref_pop_suffix]
                            except ValueError:
                                n=0
        # file was read: now write outputfile
        write_outputfile(outputfile, sep, variant_to_outputline_dict, variant_to_n_and_trio_dict,
                        variant_to_af_ref,variant_to_an_ref, len(sample_set), variant_to_hetero_parents,
                        variant_to_child_of_hetero_parents, option_dict["chi_square"], option_dict["tdt"])



def variant_is_accepted_without_significance(option_dict, line_dict, cpg_dict):
    bool_homozygous = check_homozygous(option_dict["homozygous"], float(line_dict["af_c"]))
    bool_protein = check_protein_coding(option_dict["protein_coding"], line_dict["biotype"])
    bool_denovo = check_denovo(option_dict["denovo"], float(line_dict["af_c"]), float(line_dict["af_f"]), float(line_dict["af_m"]))
    bool_cpg = check_cpg(option_dict["cpg"], line_dict["location"], line_dict["ref"], line_dict["alt"], cpg_dict)
    accepted = bool_homozygous and bool_protein and bool_denovo and bool_cpg
    return accepted

def check_homozygous(homozygous:bool, af_c:float):
    if homozygous:
        if af_c<0.8:
            return False
    return True

def check_protein_coding(protein_coding, var_type):
    if protein_coding:
        if var_type!="protein_coding":
            return False
    return True

def check_denovo(denovo:bool, af_c:float, af_f:float, af_m:float):
    if denovo:
        if af_c < 0.3:
            return False
        # if child is heterozygot: nicht denovo wenn mind. ein Elternteil heterozygot ist
        if af_c <0.8:
            if af_f>=0.3 or af_m>=0.3:
                return False
        # if child is homozygous: nicht de novo wenn beide Eltern mind. heterozygot sind
        if af_c>=0.8:
            if af_f >= 0.3 and af_m >= 0.3:
                return False
    return True

def check_cpg(cpg:bool, location:str, ref:str, alt:str, cpg_dict:dict):
    # only consider missense mutations and ignore frameshift mutations
    if len(ref)==len(alt)==1:
        chr, pos = location.split(":")
        # chr is either "1","2",... or "x","y"
        if cpg:
            try:
                if pos in cpg_dict[chr.lower()]:
                    return True
                else:
                    return False
            except KeyError:
                return False
        return True
    return False

def read_cpg_file(cpg_filepath):
    cpg_dict = {}
    # read cpgfilepath
    with open(cpg_filepath, "r") as cpg_file:
        header = True
        for line in cpg_file:
            if header:
                header = False
            else:
                lineparts = line.rstrip("\n").split("\t")
                chr = lineparts[2][3:].lower() # chromosome is denoted as "chr1" in file -> remove prefix "chr" and only store number "1" or "x"
                #  cpg start is always smallest int of start and end
                pos = str(min(int(lineparts[3]), int(lineparts[4])))
                cpg_dict.setdefault(chr, set()).add(pos)
    return cpg_dict

def get_outputfilenamesuffix(option_dict, cutoff):
    outputstr="_cutoff_"+str(cutoff)
    for key, val in option_dict.items():
        if val:
            outputstr+="_"+key
    return outputstr

def get_header_for_outputfile(sep, header_line, option_dict, excluded_headers_in_outputfile):
    header_parts = header_line.rstrip("\n").split(sep)
    relevant_output_cols = set()    # store cols that shall be written in output
    # add new cols to header and file
    new_header = "Variant" + sep + "Allele frequency" + sep + "Samples" + sep + "n_samples"
    if option_dict["chi_square"]:
        new_header += sep + "p_value Chisquare"
    if option_dict["tdt"]:
        new_header += sep + "p_value Transmission Disequilibrium Test"+sep+"n(variant transm. by heterozygous parents)"+sep+"n(var. not transm. by heteroz. parents)"
    # loop over headers and store the index of the cols that shall be rewritten to the output file
    for i in range(len(header_parts)):
        header = header_parts[i]
        if header.lower() not in excluded_headers_in_outputfile:
            relevant_output_cols.add(i)
            new_header+=sep + header
    new_header+="\n"
    return relevant_output_cols, new_header


# variant has been positively filtered -> store necessary information to write output
def store_data_of_filtered_variant(variant, variant_to_n_and_trio_dict, variant_to_outputline_dict, line, relevant_output_cols, sep, sample, af_c):
    # store sample and increase count of variant
    variant_to_n_and_trio_dict.setdefault(variant, [0, set()])
    if check_homozygous(True, af_c):
        variant_to_n_and_trio_dict[variant][0]+=2   # count twice if homozygous
    else:
        variant_to_n_and_trio_dict[variant][0]+=1
    variant_to_n_and_trio_dict[variant][1].add(sample)
    # store relevant line parts if variant has not been stored before
    if variant not in variant_to_outputline_dict.keys():
        line_parts = line.rstrip("\n").split(sep)
        relevant_line_parts = []
        # loop over line parts and check if col shall be stored
        for i in range(len(line_parts)):
            if i in relevant_output_cols:
                relevant_line_parts.append(line_parts[i])
        variant_to_outputline_dict[variant] = relevant_line_parts


def check_for_hetero_var(variant_to_hetero_parents, variant, af_p):
    if 0.3<= af_p < 0.8:
        variant_to_hetero_parents.setdefault(variant, 0)
        variant_to_hetero_parents[variant]+=1
        return True
    return False

def check_for_hetero_or_homo_var_child(variant_to_child_of_hetero_parents, variant, af_c):
    variant_to_child_of_hetero_parents.setdefault(variant, 0)
    # if child is heterozygous: count +1 in variant_to_child_of_hetero_parents dict
    if 0.3<= af_c < 0.8:
        variant_to_child_of_hetero_parents[variant]+=1
    elif af_c >= 0.8:
        # if child is homozygous: count +2 in variant_to_child_of_hetero_parents dict
        variant_to_child_of_hetero_parents[variant] += 2


def test_for_tdt(variant_to_hetero_parents, variant, line_dict, variant_to_child_of_hetero_parents):
    af_f = float(line_dict["af_f"])
    af_m = float(line_dict["af_m"])
    af_c = float(line_dict["af_c"])
    # check if parents are heterozygous; if yes add +1 to the count of heterozygous parents in the variant_to_hetero_parents dict
    hetero_father = check_for_hetero_var(variant_to_hetero_parents, variant, af_f)
    hetero_mother = check_for_hetero_var(variant_to_hetero_parents, variant, af_m)
    # case 1: both parents are heterozygous -> check child
    if hetero_father and hetero_mother:
        # store AF of child
        check_for_hetero_or_homo_var_child(variant_to_child_of_hetero_parents, variant, af_c)
    # check if any parent is homozygous
    else:
        homo_mother = check_homozygous(True, af_m)
        homo_father = check_homozygous(True, af_f)
        # case 2: one parent is heterozygous and no parent is homozygous
        if (hetero_father and not homo_mother) or (hetero_mother and not homo_father):
            # store AF of child
            check_for_hetero_or_homo_var_child(variant_to_child_of_hetero_parents, variant, af_c)
        # case 3: one parent is heterozygous and one parent is homozygous
        elif (hetero_father and homo_mother) or (hetero_mother and homo_father):
            # only add +1 if child is homozygous
            if af_c>=0.8:
                variant_to_child_of_hetero_parents.setdefault(variant,0)
                variant_to_child_of_hetero_parents[variant]+=1
        # case 4: both parents are homozygous -> does not have to be checked because then AF of child is not counted
        # case 5: de novo mutation -> count
        elif check_denovo(True, af_c, af_f, af_m):
            check_for_hetero_or_homo_var_child(variant_to_child_of_hetero_parents, variant, af_c)
            variant_to_hetero_parents.setdefault(variant,0)

def statistical_filtering(variant_to_n_and_trio_dict, variant_to_af_ref, variant_to_an_ref, n_samples, variant_to_hetero_parents, variant_to_child_of_hetero_parents, chi_square, tdt):
    significant_variants = set()
    variant_to_p_chi = {}
    variant_to_p_tdt = {}
    n_checked_variants = len(set(variant_to_n_and_trio_dict.keys()))
    if (not chi_square and not tdt) or n_checked_variants==0:
        significant_variants = set(variant_to_n_and_trio_dict.keys())
        return significant_variants, variant_to_p_chi, variant_to_p_tdt
    # if filtering has been chosen, loop over variants and compute p values
    adjusted_significance_level = significance_level/n_checked_variants
    for variant, storage_list in variant_to_n_and_trio_dict.items():
        af_vc = storage_list[0]
        p_chi = 0
        p_tdt = 0
        if chi_square:
            an_pop = int(variant_to_an_ref[variant])
            ac_pop = int(an_pop*float(variant_to_af_ref[variant]))
            p_chi= statistical_test_for_unpaired_groups(ac_pop=ac_pop, an_pop=an_pop, ac_group=af_vc, an_group=2*n_samples)
            variant_to_p_chi[variant] = round(p_chi, 5)
        if tdt:
            try:
                var_transmitted = variant_to_child_of_hetero_parents[variant]
                var_not_transmitted = max(variant_to_hetero_parents[variant] - var_transmitted, 0)  # de novo variants in the children are counted as transmitted
                p_tdt = transm_disequ_test(var_transmitted, var_not_transmitted)
                variant_to_p_tdt[variant] = round(p_tdt, 9)
            except KeyError:
                # no heterozygous variants in parents -> not significant
                p_tdt = 1
        # adjust for multiple_testing
        if p_chi<= adjusted_significance_level and p_tdt <= adjusted_significance_level:
            significant_variants.add(variant)
    return significant_variants, variant_to_p_chi, variant_to_p_tdt


def write_outputfile(outputfile, sep, variant_to_outputline_dict, variant_to_n_and_trio_dict, variant_to_af_ref,variant_to_an_ref, n_samples, variant_to_hetero_parents, variant_to_child_of_hetero_parents, chi_square, tdt):
    # header is already written
    # compute significant_variants
    significant_variants, variant_to_p_chi, variant_to_p_tdt = statistical_filtering(variant_to_n_and_trio_dict, variant_to_af_ref, variant_to_an_ref, n_samples, variant_to_hetero_parents, variant_to_child_of_hetero_parents, chi_square, tdt)
    for variant, storage_list in variant_to_n_and_trio_dict.items():
        if variant in significant_variants:
            af_vc= storage_list[0]
            samples_with_var = storage_list[1]
            outputfile.write(variant+sep+str(af_vc)+sep+write_set_or_list_as_string(samples_with_var, ", ")+sep+str(len(samples_with_var)))
            if chi_square:
                outputfile.write(sep + str(variant_to_p_chi[variant]))
            if tdt:
                var_transmitted = variant_to_child_of_hetero_parents[variant]
                var_not_transmitted = max(variant_to_hetero_parents[variant] - var_transmitted, 0)
                outputfile.write(sep + str(variant_to_p_tdt[variant])+sep+str(var_transmitted)+sep+str(var_not_transmitted))
            # write rest of line
            outputfile.write(sep + write_set_or_list_as_string(variant_to_outputline_dict[variant], sep)+"\n")


def write_set_or_list_as_string(inputset, sep):
    output = ""
    for ele in inputset:
        output+=ele + sep
    output = output.rstrip(sep)
    return output
