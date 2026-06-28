import clingo
import random
import time
import os
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.ticker as ticker
from matplotlib.ticker import ScalarFormatter

# --- Configuration Constants ---
VALUES = ["LS", "L", "VL", "AC", "C"]
EDGE_TYPES = ["support", "attack"]
RULE_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rule.lp")
DATA_FILE_PATH = os.path.join("figures", "performance_data.txt")

# Enumeration Mode (Finding ALL models)
SCALES_ENUM = [10, 15, 20]
RATIOS_ENUM = [0.5, 0.6, 0.7] # Lowered max ratio to 0.7 to avoid over-constraining
ITERATIONS_ENUM = 10  

# Scalability Mode (Finding ONE model)
SCALES_SCAL = [100, 500, 1000, 5000, 10000]
RATIOS_SCAL = [0.3, 0.5, 0.7] # Lowered max ratio to 0.7 to avoid over-constraining
ITERATIONS_SCAL = 5   


def generate_instance(num_nodes_edges: int, known_node_ratio: float, known_edge_ratio: float) -> str:
    """
    Generates a random argumentation framework. 
    Prioritizes assigning known values to leaf nodes and their outgoing edges 
    to dramatically increase the chance of generating satisfiable (SAT) instances,
    while strictly maintaining the specified known ratios.
    """
    facts = []
    facts.append(f"node(1..{num_nodes_edges}).")
    facts.append("")

    # 1. Generate Directed Edges
    generated_edges = set()
    while len(generated_edges) < num_nodes_edges:
        from_node = random.randint(1, num_nodes_edges)
        to_node = random.randint(1, num_nodes_edges)
        if from_node != to_node:
            generated_edges.add((from_node, to_node))

    edge_list = list(generated_edges)
    
    # Identify leaf nodes (nodes with in-degree == 0)
    has_incoming = set(to_node for from_node, to_node in edge_list)
    all_nodes = set(range(1, num_nodes_edges + 1))
    
    leaf_nodes = list(all_nodes - has_incoming)
    non_leaf_nodes = list(all_nodes & has_incoming)
    
    random.shuffle(leaf_nodes)
    random.shuffle(non_leaf_nodes)
    
    # 2. Assign Known Nodes (Prioritize leaf nodes)
    # This guarantees exactly 'num_known_nodes' are selected.
    num_known_nodes = int(num_nodes_edges * known_node_ratio)
    prioritized_nodes = leaf_nodes + non_leaf_nodes
    known_nodes = prioritized_nodes[:num_known_nodes]
    
    if known_nodes:
        facts.append("% A_init (Prioritized Leaf Nodes)")
        for node_id in known_nodes:
            credibility_value = random.choice(VALUES)
            facts.append(f'user_assigned({node_id}). credibility({node_id}, "{credibility_value}").')
        facts.append("")

    # 3. Assign Known Edges (Prioritize edges outgoing from leaf nodes)
    related_edges = [(u, v) for u, v in edge_list if u in leaf_nodes]
    other_edges = [(u, v) for u, v in edge_list if u not in leaf_nodes]
    
    random.shuffle(related_edges)
    random.shuffle(other_edges)
    
    # This guarantees exactly 'num_known_edges' are selected.
    num_known_edges = int(num_nodes_edges * known_edge_ratio)
    prioritized_edges = related_edges + other_edges
    known_edges = prioritized_edges[:num_known_edges]
    unknown_edges = prioritized_edges[num_known_edges:]

    if known_edges:
        facts.append("% R_init (Prioritized Related Edges)")
        for from_node, to_node in known_edges:
            edge_type = random.choice(EDGE_TYPES)
            relevance_value = random.choice(VALUES)
            facts.append(f'edge({from_node}, {to_node}, {edge_type}, "{relevance_value}").')
        facts.append("")

    if unknown_edges:
        facts.append("% unknown_edge")
        for from_node, to_node in unknown_edges:
            edge_type = random.choice(EDGE_TYPES)
            facts.append(f'unknown_edge({from_node}, {to_node}, {edge_type}).')
        facts.append("")

    return "\n".join(facts)



def run_single_test(num_nodes_edges: int, known_ratio: float, mode: str) -> tuple:
    """
    Runs a single grounding and solving process. 
    Returns: (total_time_ms, number_of_models)
    """
    instance_facts = generate_instance(num_nodes_edges, known_ratio, known_ratio)
    
    if mode == "ENUMERATION":
        ctl = clingo.Control(["0", "--project"])  # Find all models
    else:
        ctl = clingo.Control(["1"])  # Find one model
    
    try:
        ctl.load(RULE_FILE_PATH)
    except FileNotFoundError:
        print(f"Error: Rule file not found at '{RULE_FILE_PATH}'.")
        return 0.0, 0

    ctl.add("base", [], instance_facts)
    
    model_count = [0]
    def on_model(m):
        model_count[0] += 1

    start_time = time.perf_counter()
    ctl.ground([("base", [])])
    ctl.solve(on_model=on_model)
    end_time = time.perf_counter()
    
    total_time_ms = (end_time - start_time) * 1000
    return total_time_ms, model_count[0]



def run_experiment_pipeline(scales, ratios, mode, iterations):
    """
    Runs the pipeline across scales and ratios, averaging results over N iterations.
    """
    print(f"\n===== Running Pipeline: {mode} (Averaging over {iterations} runs) =====")
    avg_results = {ratio: [] for ratio in ratios}
    
    for ratio in ratios:
        for scale in scales:
            times = []
            models = []
            for i in range(iterations):
                t_ms, m_count = run_single_test(scale, ratio, mode)
                times.append(t_ms)
                models.append(m_count)
            
            avg_time = sum(times) / iterations
            avg_models = sum(models) / iterations
            avg_results[ratio].append(avg_time)
            
            print(f"  [{mode}] Scale: {scale:<5} | Ratio: {ratio:.1f} | Avg Models: {avg_models:<6.1f} | Avg Time: {avg_time:.2f} ms")
            
    return avg_results



def save_all_data_to_file(results_enum, results_scal, filepath):
    """Saves the averaged experimental data to a text file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("========================================================================\n")
        f.write("                 FIBAF Performance Evaluation Results                   \n")
        f.write("========================================================================\n\n")
        
        f.write(f"[1. Enumeration Mode (Finding ALL Models, Avg of {ITERATIONS_ENUM} runs)]\n")
        header_enum = f"{'Scale':<12} | " + " | ".join([f"Ratio={r:<10}" for r in RATIOS_ENUM]) + "\n"
        f.write(header_enum)
        f.write("-" * (15 + len(RATIOS_ENUM) * 15) + "\n")
        for i, scale in enumerate(SCALES_ENUM):
            row = f"{scale:<12} | " + " | ".join([f"{results_enum[r][i]:<10.3f}" for r in RATIOS_ENUM]) + "\n"
            f.write(row)
            
        f.write("\n" + "="*72 + "\n\n")
        
        f.write(f"[2. Scalability Mode (Finding ONE Model, Avg of {ITERATIONS_SCAL} runs)]\n")
        header_scal = f"{'Scale':<12} | " + " | ".join([f"Ratio={r:<10}" for r in RATIOS_SCAL]) + "\n"
        f.write(header_scal)
        f.write("-" * (15 + len(RATIOS_SCAL) * 15) + "\n")
        for i, scale in enumerate(SCALES_SCAL):
            row = f"{scale:<12} | " + " | ".join([f"{results_scal[r][i]:<10.3f}" for r in RATIOS_SCAL]) + "\n"
            f.write(row)
        
    print(f"\nAll averaged experimental data successfully logged to '{filepath}'")



def plot_academic_figures(results_enum, results_scal):
    """Plots academic figures based on averaged data."""
    print("\n===== Plotting Academic Figures =====")
    matplotlib.use('Agg')
    
    plt.rcParams.update({
        'font.family': 'serif',
        'font.size': 9,
        'axes.labelsize': 10,
        'legend.fontsize': 8,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'figure.dpi': 300,
    })

    styles = [
        ('o-', '#d62728'),  
        ('s-', '#1f77b4'),  
        ('^-', '#2ca02c'),  
    ]

    # Create a plain formatter to avoid scientific notation (e.g., no 10^3)
    plain_formatter = ScalarFormatter(useOffset=False, useMathText=False)
    plain_formatter.set_scientific(False)

    def draw_enum_subplot(ax):
        ratios = sorted(results_enum.keys())
        for idx, ratio in enumerate(ratios):
            style, color = styles[idx % len(styles)]
            ax.plot(SCALES_ENUM, results_enum[ratio], style, color=color, 
                    markersize=5, linewidth=1.1, label=f'Known Ratio = {ratio}')
        
        # Linear scale for enumeration mode since scales are small
        ax.set_xscale('linear')
        ax.set_xticks(SCALES_ENUM)
        ax.set_xticklabels([str(s) for s in SCALES_ENUM])
        
        ax.set_yscale('linear') # Use linear scale to avoid scientific notation
        
        ax.set_xlabel('Number of Arguments/Relations')
        ax.set_ylabel('Average Total Runtime (ms)')
        ax.set_title('(a) Enumeration Mode (ALL Models)', fontsize=10, pad=8)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.5)
        ax.legend(loc='upper left', framealpha=0.9)

    def draw_scal_subplot(ax):
        ratios = sorted(results_scal.keys())
        for idx, ratio in enumerate(ratios):
            style, color = styles[idx % len(styles)]
            ax.plot(SCALES_SCAL, results_scal[ratio], style, color=color, 
                    markersize=5, linewidth=1.1, label=f'Known Ratio = {ratio}')
        
        # Log scale for large graphs, but disable scientific notation
        ax.set_xscale('log')
        ax.set_xticks(SCALES_SCAL)
        ax.xaxis.set_major_formatter(plain_formatter)
        
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(plain_formatter)
        
        ax.set_xlabel('Number of Arguments/Relations')
        ax.set_ylabel('Average Total Runtime (ms)')
        ax.set_title('(b) Scalability Mode (ONE Model)', fontsize=10, pad=8)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.5)
        ax.legend(loc='upper left', framealpha=0.9)

    # Combined plot
    fig_combined, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.8)) 
    draw_enum_subplot(ax1)
    draw_scal_subplot(ax2)
    plt.tight_layout(pad=0.4)
    fig_combined.savefig('figures/performance_combined.pdf', bbox_inches='tight', pad_inches=0.02)
    fig_combined.savefig('figures/performance_combined.png', bbox_inches='tight', pad_inches=0.02)

    # Separate plot A
    fig_a, ax_a = plt.subplots(figsize=(3.6, 2.7))
    draw_enum_subplot(ax_a)
    ax_a.set_title('') 
    plt.tight_layout(pad=0.3)
    fig_a.savefig('figures/performance_enumeration.pdf', bbox_inches='tight', pad_inches=0.02)
    fig_a.savefig('figures/performance_enumeration.png', bbox_inches='tight', pad_inches=0.02)

    # Separate plot B
    fig_b, ax_b = plt.subplots(figsize=(3.6, 2.7))
    draw_scal_subplot(ax_b)
    ax_b.set_title('')
    plt.tight_layout(pad=0.3)
    fig_b.savefig('figures/performance_scalability.pdf', bbox_inches='tight', pad_inches=0.02)
    fig_b.savefig('figures/performance_scalability.png', bbox_inches='tight', pad_inches=0.02)

    print("Success: Generated PDF/PNG plots in 'figures/' directory.")



if __name__ == "__main__":
    # --- CRITICAL: Set random seed for scientific reproducibility ---
    random.seed(42)  
    
    print("==========================================================")
    print("      FIBAF Pipeline Experiment: One-Click Execution      ")
    print("==========================================================")
    
    # 1. Run Enumeration Experiment (Averaging over 10 iterations)
    results_enumeration = run_experiment_pipeline(SCALES_ENUM, RATIOS_ENUM, "ENUMERATION", ITERATIONS_ENUM)
    
    # 2. Run Scalability Experiment (Averaging over 5 iterations)
    results_scalability = run_experiment_pipeline(SCALES_SCAL, RATIOS_SCAL, "SCALABILITY", ITERATIONS_SCAL)
    
    # 3. Log Output
    save_all_data_to_file(results_enumeration, results_scalability, DATA_FILE_PATH)
    
    # 4. Draw Figures
    plot_academic_figures(results_enumeration, results_scalability)
    
    print("\n[Finished] All tasks completed successfully.")
