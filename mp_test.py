import multiprocessing as mp
import os

def worker(x):
    debug_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'mp_test_debug.txt'))
    with open(debug_path, 'a') as f:
        f.write(f"[WORKER] Started with x={x}\n")
    return x * x

if __name__ == "__main__":
    mp.set_start_method("fork", force=True)
    with mp.Pool(4) as pool:
        results = pool.map(worker, [1, 2, 3, 4])
    print("Results:", results)
    debug_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'mp_test_debug.txt'))
    with open(debug_path, 'a') as f:
        f.write(f"[MAIN] Pool results: {results}\n")
