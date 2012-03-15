#!/usr/bin/env python

import sqlite3

def index_variation(cursor):
    cursor.execute('''create index var_chrpos_idx on\
                      variants(chrom, start, end)''')
    cursor.execute('''create index var_type_idx on variants(type)''')
    cursor.execute('''create index var_gt_counts_idx on \
                      variants(num_hom_ref, num_het, num_hom_alt, num_unknown)''')
    cursor.execute('''create index var_aaf_idx on variants(aaf)''')
    cursor.execute('''create index var_in_dbsnp_idx on variants(in_dbsnp)''')
    cursor.execute('''create index var_in_call_rate_idx on variants(call_rate)''')
    cursor.execute('''create index var_gene_idx on variants(gene)''')
    cursor.execute('''create index var_exonic_idx on variants(exonic)''')
    cursor.execute('''create index var_coding_idx on variants(coding)''')
    cursor.execute('''create index var_impact_idx on variants(impact)''')
    cursor.execute('''create index var_depth_idx on variants(depth)''')


def index_samples(cursor):
    cursor.execute('''create unique index sample_name_idx on samples(name)''')
    
def create_indices(cursor):
    """
    Index our master DB tables for speed
    """
    index_variation(cursor)
    index_samples(cursor)

    
def create_tables(cursor):
    """
    Create our master DB tables
    """
    cursor.execute('''create table if not exists variants  (chrom text,                    \
                                                            start integer,                 \
                                                            end integer,                   \
                                                            variant_id integer,            \
                                                            anno_id integer,               \
                                                            ref text,                      \
                                                            alt text,                      \
                                                            qual float,                    \
                                                            filter text,                   \
                                                            type text,                     \
                                                            sub_type text,                 \
                                                            gts blob,                      \
                                                            gt_types blob,                 \
                                                            gt_phases blob,                \
                                                            call_rate float,               \
                                                            in_dbsnp bool,                 \
                                                            rs_ids text default NULL,      \
                                                            in_omim integer,               \
                                                            cyto_band text,                \
                                                            num_hom_ref integer,           \
                                                            num_het integer,               \
                                                            num_hom_alt integer,           \
                                                            num_unknown integer,           \
                                                            aaf float,                     \
                                                            hwe float,                     \
                                                            inbreeding_coeff float,        \
                                                            pi float,                      \
                                                            gene text,                     \
                                                            transcript text,               \
                                                            exonic bool,                   \
                                                            exon text,                     \
                                                            coding bool,                   \
                                                            codon_change text,             \
                                                            aa_change text,                \
                                                            impact text,                   \
                                                            impact_severity text,          \
                                                            is_lof integer,                \
                                                            depth integer default NULL,                 \
                                                            strand_bias float default NULL,             \
                                                            rms_map_qual float default NULL,            \
                                                            in_hom_run integer default NULL,            \
                                                            num_mapq_zero integer default NULL,         \
                                                            num_alleles integer default NULL,           \
                                                            num_reads_w_dels float default NULL,        \
                                                            haplotype_score float default NULL,         \
                                                            qual_depth float default NULL,              \
                                                            allele_count integer default NULL,          \
                                                            allele_bal float default NULL,              \
                                                            PRIMARY KEY(variant_id ASC, anno_id ASC))''')


    cursor.execute('''create table if not exists samples   (sample_id integer,    \
                                                            name text,       \
                                                            family_id integer default NULL,  \
                                                            paternal_id integer default NULL,  \
                                                            maternal_id integer default NULL,  \
                                                            sex text default NULL,     \
                                                            phenotype text default NULL,  \
                                                            ethnicity text default NULL,  \
                                                            PRIMARY KEY(sample_id ASC))''')
                                      



def close_and_commit(cursor, connection):
    """
    Commit changes to the DB and close out DB cursor.
    """
    connection.commit()
    cursor.close

def empty_tables(cursor):
    cursor.execute('''delete * from variation''')
    cursor.execute('''delete * from samples''')

