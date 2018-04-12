#!/usr/bin/env python
from __future__ import absolute_import

from . import GeminiQuery
#from . import sql_utils

# LOH mutations are categorized as being heterozygous 
# in a normal tissue sample, but have risen homozygous 
# levels in the tumor samples.
# Here we allow for a maximum and minimum allele
# frequency in the normal sample to set the boundaries
# for the heterozygous calls in the normal. 
# A minimum allele frequency for the tumor samples is
# also used to define homozygous calls in tumor samples.

def loh(parser, args):

    # create a connection to the database that was 
    # passed in as an argument via the command line
    gq = GeminiQuery.GeminiQuery(args.db)

    # define sample search query
    query = "select patient_id, name, time from samples"
    
    # execute the sample search query
    gq.run(query)

    # get paramters from the args for filtering
    if args.patient is not None:
        patient = args.patient
    if args.maxNorm is None:
        maxNorm = str(0.7)
    else:
        maxNorm = args.maxNorm
    if args.minNorm is None:
        minNorm = str(0.3)
    else:
        minNorm = args.minNorm
    if args.minTumor is None:
        minTumor = str(0.8)
    else:
        minTumor = args.minTumor

    # designating which patient to perform the query on
    # if no patient is specified at the command line
    # and only 1 patient is present in the database
    # that patient will be used
    # also verify that patient is among possible patient_ids
    patients = []
    for row in gq:
        patients.append(row['patient_id'])
    if args.patient is None and len(set(patients)) == 1:
        patient = patients[0]
    elif args.patient is None and len(set(patients)) > 1:
        raise NameError('More than 1 patient is present, specify a patient_id with --patient')
    if patient not in patients:
        raise NameError('Specified patient is not found, check the ped file for available patient_ids')
    
    # iterate again through each sample and save which sample is the normal
    # non-normal sample names are saved to a list
    gq.run(query)
    normal_samples = []
    other_samples = []
    for row in gq:
        if int(row['time']) == 0 and row['patient_id'] == patient:
            normal_samples.append(row['name'])
        elif int(row['time']) > 0 and row['patient_id'] == patient:
            other_samples.append(row['name'])

    # check arrays to see if samples have been added
    # if arrays are empty there is probably a problem in samples
    # check the ped file being loaded into the db
    if len(normal_samples) == 0:
        raise NameError('There are no normal samples; check the ped file for proper format and loading')
    if len(other_samples) == 0:
        raise NameError('There are no tumor samples; check the ped file for proper format and loading')

    # create a new connection to the database that includes the genotype columns
    # using the database passed in as an argument via the command line
    gq = GeminiQuery.GeminiQuery(args.db, include_gt_cols=True)
    
    # get from the args the maxNorm value
    #if args.maxNorm is None:
    #    maxNorm = str(0)
    #elif args.maxNorm is not None:
    #    maxNorm = args.maxNorm

    # define the loh query
    if args.columns is not None:
        # the user only wants to report a subset of the columns
        query = "SELECT " + args.columns + " FROM variants"
    else:
        # report the kitchen sink
        query = "SELECT * FROM variants"
    if args.filter is not None:
        # add any non-genotype column limits to the where clause
        query += " WHERE " + args.filter
    # query = "select chrom, start, end, gt_alt_freqs, gt_types from variants where impact_severity !='LOW' and (max_evi =='A' or max_evi == 'B' or max_rating >= 4)"

    # create gt_filter command using saved sample info
    filter_cmd = ""
    for sample in normal_samples:
        filter_cmd += "(gt_alt_freqs." + sample + " >= " + minNorm + " and gt_alt_freqs." + sample + " <= " + maxNorm + ") and "
    for sample in other_samples:
        if sample == other_samples[len(other_samples)-1]:
            filter_cmd += "gt_alt_freqs." + sample + " > " + minTumor
            continue 
        filter_cmd += "gt_alt_freqs." + sample + " > " + minTumor + " and " 
    gt_filter = filter_cmd

    # execute the truncal query (but don't do anything with the results)"
    gq.run(query, gt_filter)

    # iterate through each row of the truncal results and print
    for row in gq:
        print(row)
