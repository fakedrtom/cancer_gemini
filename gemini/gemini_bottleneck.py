#!/usr/bin/env python
from __future__ import absolute_import

from . import GeminiQuery
#from . import sql_utils
from scipy import stats
import numpy as np

# Bottleneck mutations are categorized as exhibiting 
# increasing allele frequencies over time in multiple 
# tumor samples.
# Here we allow for a maximum allele frequency in the
# normal sample(s) (default is 0).
# Tumor samples are ordered by their timepoints.
# If the slope of the allele frequencies across 
# timpoints meets the required slope
# the variant is returned.
# Minimum endpoint frequencies can be specified.
# Minimum differences between first and last
# timepoints can be specified and required.
# Rather than process all samples, a selection
# of samples can be specified.

def bottleneck(parser, args):

    # create a connection to the database that was 
    # passed in as an argument via the command line
    gq = GeminiQuery.GeminiQuery(args.db)

    # get paramters from the args for filtering
    if args.patient is not None:
        patient = args.patient
    if args.maxNorm is None:
        maxNorm = float(0)
    else:
        maxNorm = float(args.maxNorm)
    if args.minSlope is None:
        minSlope = float(0.05)
    else:
        minSlope = float(args.minSlope)
    if args.samples is None or args.samples == 'All':
        samples = 'All'
    else:
        samples = args.samples.split(',')
    if args.minEnd is None:
        minEnd = float(0)
    else:
        minEnd = float(args.minEnd)
    if args.endDiff is None:
        endDiff = float(0)
    else:
        endDiff = float(args.endDiff)

    # define sample search query
    query = "select patient_id, name, time from samples"

    # execute the sample search query
    gq.run(query)

    # designating which patient to perform the query on
    # if no patient is specified at the command line
    # and only 1 patient is present in the database
    # that patient will be used
    # also verify that patient is among possible patient_ids
    patients = []
    names = []
    for row in gq:
        patients.append(row['patient_id'])
        names.append(row['name'])
    if args.patient is None and len(set(patients)) == 1:
        patient = patients[0]
    elif args.patient is None and len(set(patients)) > 1:
        raise NameError('More than 1 patient is present, specify a patient_id with --patient')
    if patient not in patients:
        raise NameError('Specified patient is not found, check the ped file for available patient_ids')
    
    # check that specified samples with slope_samples are present
    if samples != 'All':
        for sample in samples:
            if sample not in names:
                raise NameError('Specified samples, ' + sample + ', is not found')
    elif samples == 'All':
        samples = names

    # iterate again through each sample and save which sample is the normal
    # non-normal sample names are saved to a list
    # establish which timepoints belong to which samples names
    gq.run(query)
    normal_samples = []
    other_samples = []
    timepoints = {}
    for row in gq:
        if int(row['time']) == 0 and row['patient_id'] == patient:
            normal_samples.append(row['name'])
        elif int(row['time']) > 0 and row['patient_id'] == patient:
            other_samples.append(row['name'])
        if row['patient_id'] == patient:
            if samples == 'All':
                if int(row['time']) not in timepoints:
                    timepoints[int(row['time'])] = []
                timepoints[int(row['time'])].append(row['name'])
            else:
                if row['name'] in samples:
                    if int(row['time']) not in timepoints:
                        timepoints[int(row['time'])] = []
                    timepoints[int(row['time'])].append(row['name'])
    all_samples = normal_samples + other_samples
    endpoint = max(timepoints.keys())
    startpoint = min(timepoints.keys())
    times = sorted(timepoints.keys(), reverse=True)
    
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
#    count = 0
#    while(count < len(times)-1):
#        samplesA = timepoints[times[count]]
#        samplesB = timepoints[times[count+1]]
#        for a in samplesA:
#            for b in samplesB:
#                filter_cmd += "gt_alt_freqs." + a + " >= gt_alt_freqs." + b + " and "
#        count += 1
#    for sample in normal_samples:
#        filter_cmd += "gt_alt_freqs." + sample + " <= " + maxNorm + " and "
#    endpoint = timepoints[times[0]]
#    for last in endpoint:
#        filter_cmd += "gt_alt_freqs." + last + " > " + str(float(maxNorm) + float(endDiff)) + " and "
#    gt_filter = filter_cmd
#    if gt_filter.endswith(' and '):
#        gt_filter = gt_filter[:-5]

    # execute the query (but don't do anything with the results)"
#    gq.run(query, gt_filter)
    gq.run(query)
    smp2idx = gq.sample_to_idx
    
    # print header and add the AFs of included samples and the calculated slope
    addHeader = []
    for key in timepoints:
        for s in timepoints[key]:
            if s in samples:
                af = 'alt_AF.' + s
                addHeader.append(af)
    addHeader.append('slope')
    print(gq.header) + "\t" + '\t'.join(addHeader)

    # iterate through each row of the query results
    # make sure that all args parameters are being met
    # print results that meet the requirements
    for row in gq:
        normAFs = []
        endAFs = []
        startAFs = []
        count = 0
        x = []
        y = []
        addEnd = []
        for key in timepoints:
            for s in timepoints[key]:
                if s in samples:
                    if s in normal_samples:
                        normidx = smp2idx[s]
                        normAFs.append(row['gt_alt_freqs'][normidx])
                    if key == endpoint:
                        lastidx = smp2idx[s]
                        endAFs.append(row['gt_alt_freqs'][lastidx])
                    if key == startpoint:
                        startidx = smp2idx[s]
                        startAFs.append(row['gt_alt_freqs'][startidx])
                    x.append(count)
#                        x.append(key)
                    smpidx = smp2idx[s]
                    sampleAF = row['gt_alt_freqs'][smpidx]
                    y.append(row['gt_alt_freqs'][smpidx])
                    addEnd.append(str(sampleAF))
                    count += 1
        if len(normAFs) > 0 and max(normAFs) > maxNorm:
            continue
        if min(endAFs) < minEnd:
            continue
        if min(endAFs) - max(startAFs) < endDiff:
            continue
        slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
        addEnd.append(str(slope))
        if slope < minSlope:
            continue
        print str(row) + "\t" + '\t'.join(addEnd)