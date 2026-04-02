# Genome Fetcher

A clean, robust, and standalone pipeline for downloading genome assemblies from NCBI using accession IDs (GCF format), with automated batching, 
parallel downloads, rehydration, FASTA extraction, metadata integration, and standardized renaming.

# Overview
Genome_fetcher.py automates the complete workflow of retrieving genomes from NCBI by parsing accession IDs from multiple input formats, organizing them into manageable batches, 
and downloading genome data using the NCBI datasets CLI. 
It then rehydrates the downloaded packages, extracts FASTA files, and consolidates them into a standardized output structure. The tool further enhances usability by 
renaming genomes based on organism metadata and generating reports for any missing accessions.


# Requirements
This script has the following dependencies: 
1. Python ≥ 3.7
2. NCBI Datasets CLI (datasets)

Install datasets CLI:
Please install NCBI Dataset CLI for this by : conda install -c conda-forge ncbi-datasets-cli

Python Dependencies
pip install tqdm argcomplete pandas python-docx
activate-global-python-argcomplete

# Usage
The script can be launched as follows: 

python3 Genome_fetcher.py -i INPUT -o OUTDIR -j JOB [-t THREADS]

Arguments
Argument	Description
-i, --input	Input file containing GCF accession IDs
-o, --outdir	Output directory
-j, --job	Job name (used to create working directory)
-t, --threads	Number of threads (default: 8, max: 10, to prevent NCBI overloading)

Example:

python3 Genome_fetcher.py \
  -i accessions.txt \
  -o results \
  -j ecoli_project \
  -t 8

The accession text ( file in any of the following formats .txt, .tsv, .csv, .xls, .xlsx, .docx) should have the ID of the assembly, preferably in GCF format, like :

GCF_XXXXXXXXX.X
GCF_XXXXXXXXT.T
GCF_AVXXXXXXXX.v
