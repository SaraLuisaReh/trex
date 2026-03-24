# Copyright (c) 2026 Sara-Luisa Reh
# Licensed under the GNU General Public License v3.0

import numpy as np
import scipy.stats as stats

def chi_square_test(ac_pop, an_pop, ac_group, an_group):
    freq_pop = np.array([ac_pop,an_pop-ac_pop])/an_pop*100
    freq_group = np.array([ac_group, an_group-ac_group])/an_group*100
    p_value = stats.chisquare(f_obs=freq_group,f_exp=freq_pop)[1]
    return p_value

def fishers_exact_test(ac_pop, an_pop, ac_group, an_group):
    # create contingency_table
    contingency_table = [[ac_group, ac_pop],[an_group-ac_group, an_pop-ac_pop]]
    p_value = stats.fisher_exact(contingency_table, alternative="greater")[1]
    return p_value

def statistical_test_for_unpaired_groups(ac_pop, an_pop, ac_group, an_group):
    ac_group_expected= an_group*(ac_pop/an_pop)
    if ac_group_expected<=5:
        p_value = fishers_exact_test(ac_pop, an_pop, ac_group, an_group)
    else:
        p_value = chi_square_test(ac_pop, an_pop, ac_group, an_group)
    return p_value

def binomial_test(hetero_transmitted, hetero_non_transmitted):
    n=hetero_transmitted+hetero_non_transmitted
    result = stats.binomtest(hetero_transmitted, n, p=0.5, alternative='two-sided')
    p_value =result.pvalue
    return p_value

def mc_nemar_statistics(hetero_transmitted, hetero_non_transmitted):
    mcnemar_test_statistic = ((hetero_transmitted - hetero_non_transmitted) ** 2) / (hetero_transmitted + hetero_non_transmitted)
    p_value = 1 - stats.chi2.cdf(mcnemar_test_statistic, df=1)
    return p_value

def transm_disequ_test(hetero_transmitted, hetero_non_transmitted):
    n= hetero_transmitted + hetero_non_transmitted
    if n<25:
        p_value = binomial_test(hetero_transmitted, hetero_non_transmitted)
    else:
        p_value = mc_nemar_statistics(hetero_transmitted, hetero_non_transmitted)
    return p_value


if __name__=="__main__":
    print(transm_disequ_test(30,10))

