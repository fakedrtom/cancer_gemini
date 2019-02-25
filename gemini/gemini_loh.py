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

    # get paramters from the args for filtering
    if args.patient is not None:
        patient = args.patient
    if args.minDP is None:
        minDP = int(-1)
    else:
        minDP = int(args.minDP)
    if args.minGQ is None:
        minGQ = int(-1)
    else:
        minGQ = int(args.minGQ)
    if args.samples is None or args.samples == 'All':
        samples = 'All'
    else:
        samples = args.samples.split(',')
    if args.cancers is None:
        cancers = 'none'
    else:
        cancers = args.cancers.split(',')
    if args.maxNorm is None:
        maxNorm = float(0.7)
    else:
        maxNorm = args.maxNorm
    if args.minNorm is None:
        minNorm = float(0.3)
    else:
        minNorm = args.minNorm
    if args.minTumor is None:
        minTumor = float(0.8)
    else:
        minTumor = args.minTumor

    # define sample search query
    if args.purity:
        query = "select patient_id, name, time, purity from samples"
    else:
        query = "select patient_id, name, time from samples"

    # execute the sample search query
    gq.run(query)

    # designating which patient to perform the query on
    # if no patient is specified at the command line
    # and only 1 patient is present in the database
    # that patient will be used
    # also verify that patient is among possible patient_ids
    # sample names are saved to patient specific dict
    patients = []
    names = {}
    purity = {}
    for row in gq:
        patients.append(row['patient_id'])
        if row['patient_id'] not in names:
            names[row['patient_id']] = []
        names[row['patient_id']].append(row['name'])
        if args.purity:
            purity[row['name']] = float(row['purity'])
    if args.patient is None and len(set(patients)) == 1:
        patient = patients[0]
    elif args.patient is None and len(set(patients)) > 1:
        raise NameError('More than 1 patient is present, specify a patient_id with --patient')
    if patient not in patients:
        raise NameError('Specified patient is not found, check the ped file for available patient_ids')

    # check that specified samples with --samples are present
    # otherwise all names for given patient from ped will asigned to samples list
    if samples != 'All':
        for sample in samples:
            if sample not in names[patient]:
                raise NameError('Specified samples, ' + sample + ', is not found')
    elif samples == 'All':
        samples = names[patient]
    
    # iterate again through each sample and save which sample is the normal
    # non-normal, tumor sample names are saved to a list
    # establish which timepoints belong to which samples names
    # this is done for the specified --patient and --samples
    # designate the last and first time points
    gq.run(query)
    normal_samples = []
    tumor_samples = []
    timepoints = {}
    for row in gq:
        if row['patient_id'] == patient and row['name'] in samples:
            if int(row['time']) == 0:
                normal_samples.append(row['name'])
            elif int(row['time']) > 0:
                tumor_samples.append(row['name'])
            if int(row['time']) not in timepoints:
                timepoints[int(row['time'])] = []
            timepoints[int(row['time'])].append(row['name'])
#    endpoint = max(timepoints.keys())
#    startpoint = min(timepoints.keys())
#    times = sorted(timepoints.keys(), reverse=True)
    
    # check arrays to see if samples have been added
    # if arrays are empty there is probably a problem in samples
    # check the ped file being loaded into the db
    if len(normal_samples) == 0 and len(tumor_samples) == 0:
        raise NameError('There are no samples; check the ped file for proper format and loading')
    if len(normal_samples) == 0:
        raise NameError('There are no normal samples; check the ped file for proper format and loading')
    if len(tumor_samples) == 0:
        raise NameError('There are no tumor samples; check the ped file for proper format and loading')

    # create a new connection to the database that includes the genotype columns
    # using the database passed in as an argument via the command line
    gq = GeminiQuery.GeminiQuery(args.db, include_gt_cols=True)
    
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
#    filter_cmd = ""
#    for sample in normal_samples:
#        filter_cmd += "(gt_alt_freqs." + sample + " >= " + minNorm + " and gt_alt_freqs." + sample + " <= " + maxNorm + ") and "
#    for sample in tumor_samples:
#        if sample == tumor_samples[len(tumor_samples)-1]:
#            filter_cmd += "gt_alt_freqs." + sample + " > " + minTumor
#            continue 
#        filter_cmd += "gt_alt_freqs." + sample + " > " + minTumor + " and " 
#    gt_filter = filter_cmd

    # execute the truncal query (but don't do anything with the results)"
    gq.run(query)#, gt_filter)

    # get the sample index numbers so we can get sample specific GT info (AFs, DPs, etc.)
    smp2idx = gq.sample_to_idx

    # print header and add the AFs of included samples and the calculated slope
    addHeader = []
    for key in timepoints:
        for s in timepoints[key]:
            if s in samples:
                af = 'alt_AF.' + s
                addHeader.append(af)
    print(gq.header) + "\t" + '\t'.join(addHeader)

    # iterate through each row of the truncal results and print
    for row in gq:
        normAFs = []
        tumsAFs = []
        depths = []
        quals = []
        addEnd = []
        for key in timepoints:
            for s in timepoints[key]:
                if s in samples:
                    smpidx = smp2idx[s]
                    if args.purity:
                        sampleAF = float(row['gt_alt_freqs'][smpidx]/purity[s])
                    else:
                        sampleAF = row['gt_alt_freqs'][smpidx]
                    if sampleAF > 1:
                        sampleAF = 1
                    if s in normal_samples:
                        normAFs.append(sampleAF)
                    if s in tumor_samples:
                        tumsAFs.append(sampleAF)
                    sampleDP = row['gt_depths'][smpidx]
                    depths.append(sampleDP)
                    sampleGQ = row['gt_quals'][smpidx]
                    quals.append(sampleGQ)
                    addEnd.append(str(sampleAF))
        
        if min(depths) < minDP or min(quals) < minGQ:
            continue
        if any(af < minNorm or af > maxNorm for af in normAFs):
            continue
        if any(af < minTumor for af in tumsAFs):
            continue
        # print results that meet the requirements
        # add selected sample AFs
        if cancers != 'none':
            abbrevs = str(row['civic_abbreviations']).split(',') + str(row['civic_gene_abbreviations']).split(',')  + str(row['cgi_abbreviations']).split(',') + str(row['cgi_gene_abbreviations']).split(',')
            include = 0
            for c in cancers:
                if c in abbrevs:
                    include += 1
            if include > 0:
                print str(row) + "\t" + '\t'.join(addEnd)
        else:
            print str(row) + "\t" + '\t'.join(addEnd)
