#include <iostream>
#include <vector>
#include <fstream>
#include <algorithm>
#include <string>

using namespace std;

#define MEMORY_WARNING_GB 1 // Threshold for memory warning

typedef long unsigned itype;

struct Item {
	itype index;
	itype value;
	itype weight;
};

// Function prototypes

void read_instance(itype *n, itype *c, vector<Item> &items, string filename);
void save_result(itype n, itype obj, vector<bool> &solution, string filename);

itype solve_knap_dp(itype n, itype K, vector<Item> &items, vector<bool> &sol);
itype solve_knap_greedy(itype n, itype K, vector<Item> &items, vector<bool> &sol);
itype solve_knap_bnb(itype n, itype K, vector<Item> &items, vector<bool> &sol);

itype get_upper_bound(itype n, itype depth, vector<Item> &items, itype capacity_left, itype obj);
itype get_lower_bound(itype n, itype depth, vector<Item> &items, itype capacity_left, itype obj);
itype bnb_step(itype n, itype capacity_left, vector<Item> &items, itype depth, itype obj, vector<bool> &sequence);

// Sorting utilities

typedef bool (*sort_fn)( const Item&, const Item& );
bool sortByWeightDesc(const Item &left, const Item &right) { return left.weight > right.weight; }
bool sortByWeightAsc(const Item &left, const Item &right) { return left.weight < right.weight; }
bool sortByValueDesc(const Item &left, const Item &right) { return left.value > right.value; }
bool sortByDensityDesc(const Item &left, const Item &right) { return (left.value * right.weight) > (right.value * left.weight); }

// Main program function

int main(int argc, char *argv[]) {
	
	if (argc < 3) {
		cout << "This program needs at least 2 arguments. Usage: " << argv[0] << " input_path output_path [-m greedy|dp|bnb] [-i]" << endl;
		return -1;
	}

	string method("auto");
	bool ignore_warning = false;

	itype num_items, capacity, obj;
	vector<Item> items;
	vector<bool> solution;
	read_instance(&num_items, &capacity, items, argv[1]);
	
	// Parse extra arguments
	for (int i = 3; i < argc; i++) {
		string arg(argv[i]);
		if (arg == "-m") {
			method = string(argv[++i]);
		}
		if (arg == "-i") {
			ignore_warning = true;
		}
	}

	if (method == "greedy") {
		cout << "Method: Greedy Algorithm" << endl;
		obj = solve_knap_greedy(num_items, capacity, items, solution);
	}

	if (method == "dp") {
		if (ignore_warning || (((num_items + 1) * (capacity + 1) * sizeof(itype)) >> 30) < MEMORY_WARNING_GB) {
			cout << "Method: Dynamic Programming" << endl;
			obj = solve_knap_dp(num_items, capacity, items, solution);
		}
		else {
			cout << "WARNING: Expected memory usage: " << ((num_items + 1) * (capacity + 1) * sizeof(itype) >> 30) << "GB." << endl;
			cout << "Do you want to continue? (y/N) ";
			char response;
			cin >> response;
			if (response == 'y' || response == 'Y') {
				cout << "Method: Dynamic Programming" << endl;
				obj = solve_knap_dp(num_items, capacity, items, solution);
			}
			else {
				cout << "Program aborted by user." << endl;
				return -1;
			}
		}
	}

	if (method == "bnb") {
		cout << "Method: Branch and Bound" << endl;
		obj = solve_knap_bnb(num_items, capacity, items, solution);
	}
	
	if (method == "auto") {
		if ((((num_items + 1) * (capacity + 1) * sizeof(itype)) >> 30) < MEMORY_WARNING_GB) {
			cout << "Method: Dynamic Programming" << endl;
			obj = solve_knap_dp(num_items, capacity, items, solution);
		}
		else {
			cout << "Method: Branch and Bound" << endl;
			obj = solve_knap_bnb(num_items, capacity, items, solution);
		}
	}

	save_result(num_items, obj, solution, argv[2]);

	cout << "Result: " << obj << endl;
	cout << "Sequence: [ ";
	for (bool value : solution) {
		cout << (int)value << " ";
	}
	cout << "]" << endl;
	
	return 0;
}

// Auxiliary read/save functions

void read_instance(itype *n, itype *c, vector<Item> &items, string filename) {
	ifstream input_stream;
	input_stream.open(filename.c_str());
	input_stream >> *n >> *c;
	for (itype i = 0; i < *n; i++) {
		Item temp;
		temp.index = i;
		input_stream >> temp.value >> temp.weight;
		items.push_back(temp);
	}
	input_stream.close();
}

void save_result(itype n, itype obj, vector<bool> &solution, string filename) {
	ofstream output_stream;
	output_stream.open(filename.c_str());
	output_stream << obj << " " << endl;
	for (itype i = 0; i < n; i++) {
		output_stream << (int)solution[i] << " ";
	}
	output_stream << endl;
	output_stream.close();
}

// Dynamic Programming

itype solve_knap_dp(itype n, itype c, vector<Item> &items, vector<bool> &sol) {
	itype obj;
	vector<vector<itype>> matrix(c + 1, vector<itype>(n + 1));
	sol = vector<bool>(n);

	for (itype i = 0; i < c + 1; i++) {
		for (itype j = 1; j < n + 1; j++) {
			if (items[j-1].weight <= i && i - items[j-1].weight >= 0) {
				if (matrix[i][j-1] > matrix[i-items[j-1].weight][j-1] + items[j-1].value) {
					matrix[i][j] = matrix[i][j-1];
				}
				else {
					matrix[i][j] = matrix[i-items[j-1].weight][j-1] + items[j-1].value;
				}
			}
			else {
				matrix[i][j] = matrix[i][j-1];
			}
		}
	}

	obj = matrix[c][n];

	itype i = c;
    for (int j = n; j > 0; j--) {
        if (matrix[i][j] != matrix[i][j-1]) {
            i = i - items[j-1].weight;
            sol[items[j-1].index] = true;
        }
    }

    return obj;
}

// Branch and Bound

// BnB bounds computation
// Upper bound heuristics: Fill the knapsack with the items with most density
//   When the sack runs out of space for an extra item, take (CapacityLeft /
//   ItemWeight) * ItemValue of the item with highest density
itype get_upper_bound(itype n, itype depth, vector<Item> &items, itype capacity_left, itype obj) {
	itype bound = obj;
	long int first_unused = -1;

	for (itype i = depth; i < n; i++) {
		if (capacity_left > items[i].weight) {
			bound += items[i].value;
			capacity_left -= items[i].weight;
		}
		else {
			if (first_unused == -1) {
				first_unused = i;
			}
		}
	}

	bound += capacity_left * items[first_unused].value / items[first_unused].weight;
	
	return bound;
}

// Lower bound heuristics: Fill the knapsack with the items with most density
//   When the sack runs out of space for an extra item, stop
itype get_lower_bound(itype n, itype depth, vector<Item> &items, itype capacity_left, itype obj) {
	itype bound = obj;

	for (itype i = depth; i < n; i++) {
		if (capacity_left >= items[i].weight) {
			bound += items[i].value;
			capacity_left -= items[i].weight;
		}
	}

	return bound;
}

// Recursive BnB Function
itype bnb_step(itype n, itype capacity_left, vector<Item> &items, itype depth, itype obj, vector<bool> &sequence) {
	
	static itype best_so_far = 0;
	static itype global_lower_bound = 0;
	
	// Stop condition

	if (depth == n) {
		if (obj > best_so_far) {
			cout << "New best: " << obj << endl;
			best_so_far = obj;
		}
		return obj;
	}

	// Local bounds update

	itype lower_bound = get_lower_bound(n, depth, items, capacity_left, obj);
	itype upper_bound = get_upper_bound(n, depth, items, capacity_left, obj);

	// Global bound update

	if (lower_bound > global_lower_bound) {
		global_lower_bound = lower_bound;
	}

	// Pruning

	if (global_lower_bound > upper_bound) {
		return obj;
	}

	// Branching

	vector<bool> next_left_sequence(sequence);
	next_left_sequence.push_back(true);

	itype obj_left = 0;

	if (capacity_left >= items[depth].weight) { // Viability check	
		obj_left = bnb_step(n, capacity_left - items[depth].weight, items, depth + 1, obj + items[depth].value, next_left_sequence);
	}

	vector<bool> next_right_sequence(sequence);
	next_right_sequence.push_back(false);

	itype obj_right = bnb_step(n, capacity_left, items, depth + 1, obj, next_right_sequence);

	if (obj_left > obj_right) {
		sequence = next_left_sequence;
		return obj_left;
	}
	else {
		sequence = next_right_sequence;
		return obj_right;
	}
}

// Main BnB Function
itype solve_knap_bnb(itype n, itype c, vector<Item> &items, vector<bool> &sol) {
	sol = vector<bool>(n);
	vector<bool> sequence = vector<bool>();

	// Sort items by density for better performance

	sort(items.begin(), items.end(), sortByDensityDesc);

	// Call recursive function

	itype obj = bnb_step(n, c, items, 0, 0, sequence);

	// "Un-sort" the result

	for (itype i = 0; i < n; i++) {
		sol[items[i].index] = sequence[i];
	}

	return obj;
}

// Greedy Algorithm

// Compare the result of each sorting heuristics, return highest objective solution.

itype solve_knap_greedy(itype n, itype c, vector<Item> &items, vector<bool> &sol) {
	itype best_obj = 0;
	vector<bool> best_sol;

	static sort_fn sortFunctions[] = {sortByWeightDesc, sortByWeightAsc, sortByValueDesc, sortByDensityDesc};

	for (sort_fn sortFunction : sortFunctions) {
		itype temp_obj = 0;
		vector<bool> temp_sol(n, false); // vector with size n, itialized as 0

		itype capacity_left;

		sort(items.begin(), items.end(), sortFunction);

		capacity_left = c;
		for (Item &item : items) {
			if (item.weight <= capacity_left) {
				temp_sol[item.index] = true;
				temp_obj += item.value;
				capacity_left -= item.weight;
			}
			else {
				continue;
			}
		}

		if (temp_obj > best_obj) {
			best_obj = temp_obj;
			best_sol = temp_sol;
		}
	}
	
	sol = best_sol;
	return best_obj;
}