# Knapsack solver

This is a implementation of a knapsack problem solver using three different methods, in C++ and Python. The description of the problem and the methods are found below. The usage of this program is described further down in this page.

This repository was made as part of the Introduction to Integer Optimization course (PCO115) at Federal University of Itajubá (Unifei).

## The problem

The knapsack problem is an NP-complete optimization problem. Given a set of items (defined by their weights and values), the problem consists in selecting a subset of those items that maximizes the sum of the items values, under a restriction in the sum of the items weights (described as the knapsack capacity).

## Solver methods

As a NP-complete problem, there is no general solution for this problem. All the existing methods explore the possible combinations looking for an optimal or good-enough solution. Due to the nature of the methods, one might be more suitable for a given instance than the other ones. These are the methods that are implemented in this program:

- Greedy algorithm;
- Dynamic programming;
- Branch and bound.

TODO: add a brief description of each method and their respective equations.

# Usage

## C++ solver

`make`
`./bin/knapsack_solver input_path output_path [-m greedy|dp|bnb] [-i]`

## Python solver

`python3 src/knapsack_solver.py input_path output_path [-m greedy|dp|bnb] [-i]`

- `-m`: Defines the knapsack solver method. Possible values: `greedy`, `dp` and `bnb`.
- `-i`: Ignores memory usage warning.

## Input format

For this program, an input file has the following text format:

```
num_items capacity
value[0] weight[0]
value[1] weight[1]
...
value[num_items-1] weight[num_items-1]
```

Where each value is an positive integer. Example input instances are provided in the inputs folder of this repository.

## Output format

The generated solutions are formatted as following:

```
sum_values
solution[0] solution[1] ... solution[num_items-1]
```

Where `sum_values` represents the sum of the selected items, and `solution[i]` is 1 if the item i was picked, or 0 otherwise.

## Solve all instances script

Use this script to solve all instances in the input folder and save their solutions in the output folder.

`python3 solve_all.py cpp|py [-m greedy|dp|bnb] [-i]`

Choose either `cpp` (C++) or `py` (Python) in the first passed argument to define the solver program.