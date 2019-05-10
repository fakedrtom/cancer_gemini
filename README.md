Cancer-GEMINI
=============================================================================

Overview
========
Cancer-GEMINI is an adaptation of [GEMINI](https://github.com/arq5x/gemini) intended for the improved identification of
biologically and clincally relevant tumor variants from multi-sample and longitudinal
tumor sequencing data. Using a GEMINI-compatible database (generated from an annotated 
VCF file), Cancer-GEMINI is able to filter tumor variants based on included genomic
annotations and various allele frequency signatures. 


Installation
============


Documentation
================
The official documentation is here.

Since Cancer-GEMINI retains much of the functionality of GEMINI, it may also be 
helpful to refer to GEMINI's official documentation which can be found [here](http://gemini.readthedocs.org/en/latest/).

VCF Preparation
----------------
Like GEMINI, multi-allelic sites need to be decomposed and normalized using [vt](https://genome.sph.umich.edu/wiki/Vt).
A more thorough explanation and guide for doing this can be found at the [GEMINI documentation](https://gemini.readthedocs.io/en/latest/#new-gemini-workflow).

Cancer-GEMINI relies upon VCF annotations for the creation of searchable fields within 
a database. Therefore it is important that a VCF be annotated with all information that
a user desires for filtering. With that in mind, Cancer-GEMINI was designed to be used 
alongside [vcfanno](https://github.com/brentp/vcfanno) to accomplish all VCF annotation needs. 

Database Creation
----------------
Properly prepared and annotated VCFs can be used to create Caner_GEMINI databases with [vcf2db](https://github.com/quinlan-lab/vcf2db).
The creation of a database with vcf2db also requires a pedigree-like file, referred to as a 
sample manifest, to be included. The structure of this file is similar to a more traditional
pedigree file, but inlcudes additional columns corresponding to a patient
identifier, the sequential point in which that sample was obtained (to reflect longitudinal
data across multiple timepoints), and any sample purity values, if known.

```
#family_id      name    paternal_id     maternal_id     sex     phenotype       patient_id      time    purity
1               A0      0               0               2       1               A               0       1
1               A1      0               0               2       2               A               1       0.1
1               A2      0               0               2       2               A               2       0.1
1               B0      0               0               2       1               B               0       1
1               B1      0               0               2       2               B               1       0.5
```

Together, the annotated VCF and sample manifest file are used by the vcf2db script to generate
the Cancer-GEMINI database.

```
python vcf2db.py annotated.vcf.gz sample_manifest.ped database.db
```

Citation
================
If you use Cancer-GEMINI in your research, please cite the following manuscript:


Acknowledgements
================
Cancer-GEMINI is being developed in the Quinlan lab (quinlanlab.org) at the University
of Utah and is led by Tom Nicholas and Aaron Quinlan.  Substantial contributions and discussions 
have been made by Brent Pedersen, Yi Qiao, Xiaomeng Huang, and Gabor Marth.
