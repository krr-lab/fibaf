# Fuzzy Incomplete Bipolar Argumentation Framework (FIBAF)

An Answer Set Programming (ASP) implementation to find consistent covers in a Fuzzy Incomplete Bipolar Argumentation Framework (FIBAF) using `clingo`.

## Prerequisites

Install the `clingo` solver (e.g., via Conda):
```bash
conda install -c potassco clingo
```

## File Structure

*   `rule.lp`: Contains the core logic rules, inference calculations, and consistency checks.
*   `example.lp`: Contains the specific instance data (nodes, edges, assignments) and includes `rule.lp`.

## Usage

To find all consistent covers (all answer sets):
```bash
clingo example.lp 0
```


If `example.lp` does not contain the `#include "rule.lp"` directive, run both files together:
```bash
clingo rule.lp example.lp 0
```

## Output Interpretation

The solver outputs the valid assignments under the following predicates:
*   `consistent_argument_status(Node, Value)`: The credibility value of non-leaf nodes.
*   `leaf_argument_status(Node, Value)`: The credibility value of leaf nodes.
