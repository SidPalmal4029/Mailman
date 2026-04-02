#!/usr/bin/env python3

import os
import re
import sys
import json
import shutil
import argparse
import subprocess
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

import argcomplete
from argcomplete.completers import FilesCompleter
from tqdm import tqdm

# -----------------------------
# CONFIG
# -----------------------------
BATCH_SIZE = 10
VALID_EXT = (".fa", ".fna", ".fasta")
MAX_SAFE_THREADS = 10

# -----------------------------
# UI
# -----------------------------
def stage(i, total, msg):
    print(f"\n[{i}/{total}] {msg}...")

# -----------------------------
# ARGUMENTS
# -----------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="NCBI Genome Fetcher (clean, robust, standalone)"
    )

    inp = parser.add_argument("-i", "--input", required=True)
    inp.completer = FilesCompleter(
        allowednames=("txt", "tsv", "csv", "xlsx", "docx")
    )

    parser.add_argument("-o", "--outdir", required=True)
    parser.add_argument("-j", "--job", required=True)
    parser.add_argument("-t", "--threads", type=int, default=8)

    argcomplete.autocomplete(parser)
    return parser.parse_args()

# -----------------------------
# INPUT PARSING
# -----------------------------
def parse_accessions(path):
    ext = path.lower()

    if ext.endswith((".txt", ".tsv", ".csv")):
        text = open(path).read()

    elif ext.endswith((".xls", ".xlsx")):
        import pandas as pd
        df = pd.read_excel(path, header=None)
        text = "\n".join(df.astype(str).values.flatten())

    elif ext.endswith(".docx"):
        from docx import Document
        doc = Document(path)
        text = "\n".join(p.text for p in doc.paragraphs)

    else:
        sys.exit("Unsupported input format")

    acc = sorted(set(re.findall(r"GCF_\d+\.\d+", text)))

    if not acc:
        sys.exit("No valid GCF accessions found")

    return acc

# -----------------------------
# DIRECTORIES
# -----------------------------
def resolve_outdir(path):
    if os.path.exists(path) and os.access(path, os.W_OK):
        return path
    try:
        os.makedirs(path)
        return path
    except:
        if os.access(os.getcwd(), os.W_OK):
            return os.getcwd()
    sys.exit("No writable directory available")

def create_job_dir(base, job):
    job_dir = os.path.join(base, job)
    os.makedirs(job_dir, exist_ok=True)
    return job_dir

# -----------------------------
# BATCHING
# -----------------------------
def chunk(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i+size]

def create_batches(acc, batch_dir):
    os.makedirs(batch_dir, exist_ok=True)
    files = []
    for i, c in enumerate(chunk(acc, BATCH_SIZE), 1):
        f = os.path.join(batch_dir, f"batch_{i:03}.txt")
        with open(f, "w") as out:
            out.write("\n".join(c))
        files.append(f)
    return files

# -----------------------------
# DOWNLOAD
# -----------------------------
def download_batch(batch_file, outdir):
    name = os.path.basename(batch_file).replace(".txt", "")
    bdir = os.path.join(outdir, name)
    os.makedirs(bdir, exist_ok=True)

    zipf = os.path.join(bdir, f"{name}.zip")

    cmd = [
        "datasets", "download", "genome", "accession",
        "--inputfile", batch_file,
        "--include", "genome",
        "--dehydrated",
        "--filename", zipf
    ]

    try:
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        return bdir, True
    except:
        return bdir, False

def parallel_download(batch_files, outdir, workers):
    ok = []

    with ThreadPoolExecutor(max_workers=workers) as exe:
        futures = [exe.submit(download_batch, bf, outdir) for bf in batch_files]

        for f in tqdm(futures, desc="   Downloading", ncols=80):
            d, status = f.result()
            if status:
                ok.append(d)

    return ok

# -----------------------------
# UNZIP
# -----------------------------
def unzip_batch(batch_dir):
    for f in os.listdir(batch_dir):
        if f.endswith(".zip"):
            path = os.path.join(batch_dir, f)
            with zipfile.ZipFile(path, 'r') as z:
                z.extractall(batch_dir)
            os.remove(path)

# -----------------------------
# REHYDRATE
# -----------------------------
def rehydrate(batch_dir, attempts=3):
    workers = 3

    for i in range(attempts):
        try:
            subprocess.run([
                "datasets", "rehydrate",
                "--directory", batch_dir,
                "--match", "genomic.fna",
                "--max-workers", str(workers),
                "--no-progressbar"
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
            )

            return True

        except subprocess.CalledProcessError:
            pass

    return False

def parallel_rehydrate(dirs, threads):

    # Control total concurrency
    batch_workers = max(1, min(threads // 3, 3))   # 1–3 batches
    inner_workers = 3                              # per batch

    failed = []

    def process(d):
        unzip_batch(d)
        ok = rehydrate(d, attempts=3)
        return d, ok

    with ThreadPoolExecutor(max_workers=batch_workers) as exe:
        futures = [exe.submit(process, d) for d in dirs]

        for f in tqdm(as_completed(futures),
                      total=len(futures),
                      desc="   Rehydrating",
                      ncols=80):
            d, ok = f.result()
            if not ok:
                failed.append(d)

    return failed


# -----------------------------
# FASTA
# -----------------------------
def discover_fasta(root):
    files = []
    for r, _, fs in os.walk(root):
        for f in fs:
            if f.lower().endswith(VALID_EXT):
                files.append(os.path.join(r, f))
    return files

def has_fasta(root):
    for _, _, fs in os.walk(root):
        for f in fs:
            if f.lower().endswith(VALID_EXT):
                return True
    return False

def collect_fasta(files, dest):
    os.makedirs(dest, exist_ok=True)
    out = []

    for f in tqdm(files, desc="   Collecting", ncols=80, leave=False):
        stem = os.path.splitext(os.path.basename(f))[0]
        new = os.path.join(dest, f"{stem}.fasta")

        c = 1
        while os.path.exists(new):
            new = os.path.join(dest, f"{stem}_{c}.fasta")
            c += 1

        shutil.copy2(f, new)
        out.append(new)

    return out

# -----------------------------
# METADATA
# -----------------------------
def extract_acc(name):
    m = re.search(r"(GCF_\d+\.\d+)", name)
    return m.group(1) if m else None

def load_metadata(root):
    meta = {}

    for r, _, fs in os.walk(root):
        for f in fs:
            if f == "assembly_data_report.jsonl":
                path = os.path.join(r, f)

                with open(path) as fh:
                    for line in fh:
                        try:
                            j = json.loads(line)
                            acc = j.get("accession")
                            org = j.get("organism", {}).get("organismName", "")
                            if acc:
                                meta[acc] = org
                        except:
                            pass
    return meta

# -----------------------------
# GUIDE + RENAME
# -----------------------------
def generate_guide(files, meta, guide_path):
    with open(guide_path, "w") as out:
        for f in files:
            acc = extract_acc(f)
            if not acc:
                continue

            org = meta.get(acc, "")
            if org:
                parts = org.split()
                name = f"{parts[0]}_{parts[1]}_{acc}" if len(parts) >= 2 else f"{parts[0]}_{acc}"
            else:
                name = acc

            out.write(f"{name}\t{acc}\n")

def run_renamer(src_dir, dest_dir, guide):
    os.makedirs(dest_dir, exist_ok=True)

    tag_map = {}
    with open(guide) as f:
        for line in f:
            if "\t" in line:
                name, tag = line.strip().split("\t")
                tag_map[tag.lower()] = name

    for f in tqdm(os.listdir(src_dir), desc="   Renaming", ncols=80, leave=False):
        if not f.endswith(".fasta"):
            continue

        src = os.path.join(src_dir, f)
        fl = f.lower()

        new = f
        for tag, name in tag_map.items():
            if tag in fl:
                new = f"{name}.fasta"
                break

        dest = os.path.join(dest_dir, new)
        c = 1
        while os.path.exists(dest):
            base, ext = os.path.splitext(new)
            dest = os.path.join(dest_dir, f"{base}_{c}{ext}")
            c += 1

        shutil.move(src, dest)

# -----------------------------
# VALIDATION
# -----------------------------
def report_missing(accessions, meta, jobdir):
    expected = set(accessions)
    observed = set(meta.keys())
    missing = expected - observed

    print(f"   Validation: {len(observed)}/{len(expected)} recovered")

    if missing:
        path = os.path.join(jobdir, "missing_accessions.txt")
        with open(path, "w") as f:
            for m in sorted(missing):
                f.write(m + "\n")
        print(f"   Missing: {len(missing)} (see missing_accessions.txt)")

    return missing

# -----------------------------
# MAIN
# -----------------------------
def main():
    args = parse_args()

    threads = max(1, min(args.threads, MAX_SAFE_THREADS))
    outdir = resolve_outdir(args.outdir)
    jobdir = create_job_dir(outdir, args.job)
    os.chdir(jobdir)

    stage(1,7,"Parsing input")
    acc = parse_accessions(args.input)

    stage(2,7,"Creating batches")
    batches = create_batches(acc, "batches")

    stage(3,7,"Downloading")
    dirs = parallel_download(batches, "downloads", threads)

    stage(4,7,"Rehydrating")
    failed = parallel_rehydrate(dirs, threads) 

    if failed:
        print(f"   Failed batches: {len(failed)}")

    if not has_fasta("downloads"):
        sys.exit(" !!! No genomes recovered")

    stage(5,7,"Collecting FASTA")
    fasta = discover_fasta("downloads")
    collected = collect_fasta(fasta, "unified_fasta")

    stage(6,7,"Renaming")
    meta = load_metadata("downloads")
    report_missing(acc, meta, jobdir)

    guide = "rename_guide.tsv"
    generate_guide(collected, meta, guide)
    run_renamer("unified_fasta", "final_genomes", guide)

    stage(7,7,"Completed")
    print("[DONE] Job completed successfully")

if __name__ == "__main__":
    main()
