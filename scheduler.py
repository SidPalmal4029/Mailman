from concurrent.futures import ThreadPoolExecutor, as_completed


def parallel_transfer(files, transfer_func, workers):

    with ThreadPoolExecutor(max_workers=workers) as executor:

        futures = [executor.submit(transfer_func, f) for f in files]

        for future in as_completed(futures):
            future.result()
