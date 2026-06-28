# Fuzzy Incomplete Bipolar Argumentation Framework (FIBAF)

## Background
This project implements a **Fuzzy Incomplete Bipolar Argumentation Framework (FIBAF)** based on Answer Set Programming (ASP), built on top of the `clingo` solver.

Argumentation frameworks are formal models for reasoning over conflicting and supportive information. This framework supports:
- Ordinal credibility levels for individual arguments
- Weighted support and attack relations between arguments
- Partial graph information (unassigned node credibility, unknown edge weights)

The solver is designed to find **all consistent value assignments (consistent covers)** that satisfy the predefined inference rules and global consistency constraints over the argument graph.

## File Structure
| File | Description |
|:-----|:------------|
| `rule.lp` | Core ASP encoding: defines the ordinal value scale, inference calculus, consistency constraints, and standard output predicates. |
| `example.lp` | A sample input instance with 4 argument nodes, pre-assigned credibility values, and a mix of known and unknown edges. |
| `experiment.py` | A Python script for performance evaluation. It generates random test instances, runs tests across different scales, and outputs academic-ready plots. |

## Prerequisites
### For basic reasoning
Install the `clingo` ASP solver (recommended via Conda):
```bash
conda install -c potassco clingo
```

### For performance benchmarking
- Python 3.8 or higher
- `clingo` Python bindings
- `matplotlib` for visualization

Install Python dependencies:
```bash
pip install clingo matplotlib
```

## Usage

### Basic Solving
To enumerate **all consistent assignments** for the provided example:
```bash
clingo example.lp 0 --project
```

To run your own custom instance:
```bash
clingo rule.lp your_custom_instance.lp 0 --project
```

Replace `0` with `1` if you only need one valid solution:
```bash
clingo example.lp 1
```

### Run Performance Experiment
Execute the full experimental pipeline to generate runtime statistics and plots:
```bash
python performance_benchmark.py
```
All numerical results and high-resolution figures will be saved to the `figures/` directory.

## Output Interpretation
The solver returns valid assignments through two standardized predicates:
- `consistent_argument_status(Node, Value)`: The final credibility value of non-leaf nodes in the consistent assignment.
- `leaf_argument_status(Node, Value)`: The credibility value of leaf nodes (arguments with no incoming support/attack edges).
