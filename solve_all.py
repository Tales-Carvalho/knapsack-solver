import os, sys
import time

# TODO: parse arguments accordingly to new changes

if len(sys.argv) < 2:
	print(f"Not enough arguments. Usage: python3 {sys.argv[0]} cpp|py [-m greedy|dp|bnb] [i]")
elif sys.argv[1] != "py" and sys.argv[1] != "cpp":
	print(f"Invalid argument: {sys.argv[1]}. Expected arguments: cpp or py.")
else:
	method = ""
	ignore_warning = ""

	for i in range(2, len(sys.argv)):
		if sys.argv[i] == "-m":
			i = i + 1
			method = sys.argv[i].strip()
		if sys.argv[i] == "-i":
			ignore_warning = "-i"

	if method != "dp" and method != "greedy" and method != "bnb":
		print("WARNING: Invalid method passed. Automatic method selected.")
		method = "auto"

	ignore_warning = ""
	if len(sys.argv) > 3:
		ignore_warning = sys.argv[3]
	
	for file in os.listdir('input'):
		print(" ===//===//===//===//===//===//===//===//===//=== ")
		print(f"\nInput file: input/{file}\n")
		start_time = time.time()
		if sys.argv[1] == "py":
			os.system(f"python3 src/knapsack_solver.py ./input/{file} ./output/{file}.sol -m {method} {ignore_warning}")
		else:
			os.system(f"./bin/knapsack_solver ./input/{file} ./output/{file}.sol -m {method} {ignore_warning}")
		end_time = time.time()
		print(f"\nOutput saved in output/{file}.sol\n")
		print(f"Execution time (s): {end_time - start_time}\n")

