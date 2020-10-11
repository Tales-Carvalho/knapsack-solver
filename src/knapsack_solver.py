import concurrent.futures

from collections import namedtuple
Item = namedtuple("Item", ['index', 'value', 'weight'])

MEMORY_WARNING_GB = 1

# Function that selects the method to solve the problem

def solve_it(input_data, method, ignore_warning):
    
    # Parse the input
    
    lines = input_data.split('\n')

    firstLine = lines[0].split()
    item_count = int(firstLine[0])
    capacity = int(firstLine[1])

    items = []

    for i in range(1, item_count+1):
        line = lines[i]
        parts = line.split()
        items.append(Item(i-1, int(parts[0]), int(parts[1])))

    x, obj = [], 0

    # Select method

    if (method == "bnb"):
        print("Method: Branch and Bound")
        x, obj = solve_knap_bnb(item_count, items, capacity)
    elif (method == "dp"):
        if (ignore_warning == "i" or (((item_count + 1) * (capacity + 1) * sys.getsizeof(capacity)) >> 30) < MEMORY_WARNING_GB):
            print("Method: Dynamic Programming")
            x, obj = solve_knap_dp(item_count, items, capacity)
        else:
            print(f"WARNING: Expected memory usage: {((item_count + 1) * (capacity + 1) * sys.getsizeof(capacity)) >> 30}GB.")
            response = input("Do you want to continue? (y/N) ")
            if (response == 'y' or response == 'Y'):
                print("Method: Dynamic Programming")
                x, obj = solve_knap_dp(item_count, items, capacity)
            else:
                print("Program aborted by user.")
                return ""
    elif (method == "greedy"):
        print("Method: Greedy Algorithm")
        x, obj = solve_knap_greedy(item_count, items, capacity)
    elif ((((item_count + 1) * (capacity + 1) * sys.getsizeof(capacity)) >> 30) < MEMORY_WARNING_GB):
        print("Method: Dynamic Programming")
        x, obj = solve_knap_dp(item_count, items, capacity)
    else:
        print("Method: Branch and Bound")
        x, obj = solve_knap_bnb(item_count, items, capacity)

    print(f"Result: {obj}")
    print(f"Sequence: {x}")

    # Formatting output

    output_data = str(obj) + '\n'
    output_data += ' '.join(map(str, x))
    output_data += '\n'

    return output_data

# Utilities

def returnWeight(item):
    return item.weight

def returnValue(item):
    return item.value

def returnDensity(item):
    return item.value / item.weight

# Dynamic Programming

def solve_knap_dp(num_items, items, capacity):

    print(f"Table size: {num_items+1} x {capacity+1} ({(num_items+1)*(capacity+1)} elements)")

    x = [0] * num_items
    obj = 0

    matrix = [[0] * (num_items + 1) for i in range(capacity + 1)]

    # Fill table with values

    for i in range(capacity + 1):
        for j in range(1, num_items + 1):
            if (items[j-1].weight <= i and i - items[j-1].weight >= 0):
                if (matrix[i][j-1] > matrix[i-items[j-1].weight][j-1] + items[j-1].value):
                    matrix[i][j] = matrix[i][j-1]
                else:
                    matrix[i][j] = matrix[i-items[j-1].weight][j-1] + items[j-1].value
            else:
                matrix[i][j] = matrix[i][j-1]

    # Get the solution from table

    obj = matrix[capacity][num_items]

    i = capacity
    for j in range(num_items, 0, -1):
        if (matrix[i][j] != matrix[i][j-1]):
            i = i - items[j-1].weight
            x[j-1] = 1

    return x, obj

# Branch and Bound

best_so_far = 0
global_lower_bound = 0

# BnB bounds computation
# Upper bound heuristics: Fill the knapsack with the items with most density
#   When the sack runs out of space for an extra item, take (CapacityLeft /
#   ItemWeight) * ItemValue of the item with highest density
def get_upper_bound(depth, items, capacity_left, obj):
    
    bound = obj
    first_unused = -1
    items_left = items[depth:]
    
    for i in range(len(items_left)):
        if (capacity_left > items_left[i].weight):
            bound += items_left[i].value
            capacity_left -= items_left[i].weight
        else:
            if (first_unused == -1):
                first_unused = i

    bound += (capacity_left / items_left[first_unused].weight) * items_left[first_unused].value
    
    return bound

# Lower bound heuristics: Fill the knapsack with the items with most density
#   When the sack runs out of space for an extra item, stop
def get_lower_bound(depth, items, capacity_left, obj):
    bound = obj

    items_left = items[depth:]
    for item in items_left:
        if (capacity_left >= item.weight):
            bound += item.value
            capacity_left -= item.weight

    return bound

# Recursive BnB function
def bnb_step(items, curr_sequence, curr_depth, curr_capacity_left, curr_obj):
    
    # Stop condition

    if (curr_depth == len(items)):
        global best_so_far
        if (curr_obj > best_so_far):
            print(f"New best: {curr_obj}")
            best_so_far = curr_obj
        return curr_obj, curr_sequence

    # Local bounds update

    curr_upper_bound = get_upper_bound(curr_depth, items, curr_capacity_left, curr_obj)
    curr_lower_bound = get_lower_bound(curr_depth, items, curr_capacity_left, curr_obj)

    # Global bound update

    global global_lower_bound
    if (curr_lower_bound > global_lower_bound):
        global_lower_bound = curr_lower_bound

    # Pruning

    if (curr_upper_bound <= global_lower_bound):
        return curr_obj, curr_sequence

    # Branching

    next_node_left_sequence = curr_sequence.copy()
    next_node_left_sequence.append(1)

    obj_left, x_left = 0, []

    if (curr_capacity_left - items[curr_depth].weight >= 0): # Viability check
        with concurrent.futures.ThreadPoolExecutor() as executor: # Thread executor to avoid stack overflow in recursive calls
            future = executor.submit(bnb_step, items, next_node_left_sequence, curr_depth + 1,
                                    curr_capacity_left - items[curr_depth].weight,
                                    curr_obj + items[curr_depth].value)
            obj_left, x_left = future.result()

    next_node_right_sequence = curr_sequence.copy()
    next_node_right_sequence.append(0)

    obj_right, x_right = 0, []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(bnb_step, items, next_node_right_sequence, curr_depth + 1,
                                curr_capacity_left, curr_obj)
        obj_right, x_right = future.result()

    if (obj_left > obj_right):
        return obj_left, x_left
    else:
        return obj_right, x_right

# BnB main function
def solve_knap_bnb(num_items, items, capacity):

    x = [0]*num_items

    # Sort items by density for better performance

    items.sort(key=returnDensity, reverse=True)

    # Call recursive function

    obj, sequence = bnb_step(items, [], 0, capacity, 0)

    # "Un-sort" the result

    for i in range(len(items)):
        x[items[i].index] = sequence[i]

    return x, obj

# Greedy Algorithm

# Heuristics:
# Take items until there's no space left in the sack, prioritizing:
# 1. Items with higher weight;
# 2. Items with lower weight;
# 3. Items with higher value;
# 4. Items with higher value/weight density.
# Afterwards, compare all the outputs and select the highest one.

def solve_knap_greedy(num_items, items, capacity):

    x = [0]*num_items
    obj = 0

    objWeight = 0
    objWeightInv = 0
    objValue = 0
    objDensity = 0
    xWeight = x.copy()
    xWeightInv = x.copy()
    xValue = x.copy()
    xDensity = x.copy()

    itemsSortedWeight = items.copy()
    itemsSortedWeight.sort(key=returnWeight)

    itemsSortedWeightInv = items.copy()
    itemsSortedWeightInv.sort(key=returnWeight, reverse=True)

    itemsSortedValue = items.copy()
    itemsSortedValue.sort(key=returnValue, reverse=True)

    itemsSortedDensity = items.copy()
    itemsSortedDensity.sort(key=returnDensity, reverse=True)

    capacity_left = capacity

    for item in itemsSortedWeight:
        if item.weight <= capacity_left:
            xWeight[item.index] = 1
            objWeight += item.value
            capacity_left -= item.weight
        else:
            break

    capacity_left = capacity

    for item in itemsSortedWeightInv:
        if item.weight <= capacity_left:
            xWeightInv[item.index] = 1
            objWeightInv += item.value
            capacity_left -= item.weight
        else:
            continue

    capacity_left = capacity

    for item in itemsSortedValue:
        if item.weight <= capacity_left:
            xValue[item.index] = 1
            objValue += item.value
            capacity_left -= item.weight
        else:
            continue

    capacity_left = capacity

    for item in itemsSortedDensity:
        if item.weight <= capacity_left:
            xDensity[item.index] = 1
            objDensity += item.value
            capacity_left -= item.weight
        else:
            continue

    if objWeight >= objValue and objWeight >= objDensity and objWeight >= objWeightInv:
        obj = objWeight
        x = xWeight.copy()

    if objWeightInv >= objValue and objWeightInv >= objDensity and objWeightInv >= objWeight:
        obj = objWeightInv
        x = xWeightInv.copy()

    if objValue >= objWeight and objValue >= objDensity and objValue >= objWeightInv:
        obj = objValue
        x = xValue.copy()

    if objDensity >= objValue and objDensity >= objWeight and objDensity >= objWeightInv:
        obj = objDensity
        x = xDensity.copy()

    return x, obj

# Main function

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2:
        file_location = sys.argv[1].strip()
        solution_file_location = sys.argv[2].strip()
        
        method = "auto"
        ignore_warning = False
        
        for i in range(3, len(sys.argv)):
            if sys.argv[i] == "-m":
                i = i + 1
                method = sys.argv[i].strip()
            if sys.argv[i] == "-i":
                ignore_warning = True

        with open(file_location, 'r') as input_data_file:
            input_data = input_data_file.read()
        
        output_data = solve_it(input_data, method, ignore_warning)
        
        solution_file = open(solution_file_location, "w")
        solution_file.write(output_data)
        solution_file.close()
    else:
        print('This script needs at least 2 arguments. Usage: python3 ' + sys.argv[0] + ' input_path output_path [-m greedy|dp|bnb] [-i]')
