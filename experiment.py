import clingo
import random
import time
import os
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.ticker as ticker


VALUES = ["LS", "L", "VL", "AC", "C"]
EDGE_TYPES = ["support", "attack"]
RULE_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rule.lp")
DATA_FILE_PATH = os.path.join("figures", "performance_data.txt")

# Enumeration Mode 
SCALES_ENUM = [10, 15, 20]
RATIOS_ENUM = [0.6, 0.8, 0.9]

# Scalability Mode
SCALES_SCAL = [100, 500, 1000, 5000, 10000]
RATIOS_SCAL = [0.1, 0.5, 0.9]



def generate_instance(num_nodes_edges: int, known_node_ratio: float, known_edge_ratio: float) -> str:
    """generate_instance"""
    facts = []
    facts.append(f"node(1..{num_nodes_edges}).")
    facts.append("")

    num_known_edges = int(num_nodes_edges * known_edge_ratio)
    generated_edges = set()
    while len(generated_edges) < num_nodes_edges:
        from_node = random.randint(1, num_nodes_edges)
        to_node = random.randint(1, num_nodes_edges)
        if from_node != to_node:
            generated_edges.add((from_node, to_node))

    edge_list = list(generated_edges)
    random.shuffle(edge_list)

    known_edges = edge_list[:num_known_edges]
    unknown_edges = edge_list[num_known_edges:]

    if known_edges:
        facts.append("% R_init")
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

    
    has_incoming = set(to_node for from_node, to_node in edge_list)
    all_nodes = set(range(1, num_nodes_edges + 1))
    leaf_nodes = list(all_nodes - has_incoming)

    
    num_known_nodes = int(num_nodes_edges * known_node_ratio)
    num_to_select = min(num_known_nodes, len(leaf_nodes))

    if num_to_select > 0 and len(leaf_nodes) > 0:
        known_nodes = random.sample(leaf_nodes, num_to_select)
        facts.append("% A_init")
        for node_id in known_nodes:
            credibility_value = random.choice(VALUES)
            facts.append(f'user_assigned({node_id}). credibility({node_id}, "{credibility_value}").')
        facts.append("")

    return "\n".join(facts)



def run_single_test(num_nodes_edges: int, known_ratio: float, mode: str) -> float:
    """run_single_test"""
    instance_facts = generate_instance(num_nodes_edges, known_ratio, known_ratio)
    
    
    if mode == "ENUMERATION":
        ctl = clingo.Control(["0", "--project"])  
    else:
        ctl = clingo.Control(["1"])  
    
    try:
        ctl.load(RULE_FILE_PATH)
    except FileNotFoundError:
        print(f"Error: Rule file not found at '{RULE_FILE_PATH}'.")
        return 0.0

    ctl.add("base", [], instance_facts)
    
    
    model_count = [0]
    def on_model(m):
        model_count[0] += 1

    start_time = time.perf_counter()
    ctl.ground([("base", [])])
    ctl.solve(on_model=on_model)
    end_time = time.perf_counter()
    
    total_time_ms = (end_time - start_time) * 1000
    print(f"  [{mode}] Scale: {num_nodes_edges:<5} | Ratio: {known_ratio:.1f} | Models: {model_count[0]:<5} | Time: {total_time_ms:.2f} ms")
    return total_time_ms


def run_experiment_pipeline(scales, ratios, mode):
    """run_experiment_pipeline"""
    print(f"\n===== Running Pipeline: {mode} =====")
    results = {ratio: [] for ratio in ratios}
    for ratio in ratios:
        for scale in scales:
            time_ms = run_single_test(scale, ratio, mode)
            results[ratio].append(time_ms)
    return results



def save_all_data_to_file(results_enum, results_scal, filepath):
    """save_all_data_to_file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("========================================================================\n")
        f.write("                 FIBAF Performance Evaluation Results                   \n")
        f.write("========================================================================\n\n")
        
        
        f.write("[1. Enumeration Mode (Finding ALL Models - Small Scale)]\n")
        header_enum = f"{'Scale':<12} | " + " | ".join([f"Ratio={r:<10}" for r in RATIOS_ENUM]) + "\n"
        f.write(header_enum)
        f.write("-" * (15 + len(RATIOS_ENUM) * 15) + "\n")
        for i, scale in enumerate(SCALES_ENUM):
            row = f"{scale:<12} | " + " | ".join([f"{results_enum[r][i]:<10.3f}" for r in RATIOS_ENUM]) + "\n"
            f.write(row)
            
        f.write("\n" + "="*72 + "\n\n")
        
        
        f.write("[2. Scalability Mode (Finding ONE Model - Large Scale)]\n")
        header_scal = f"{'Scale':<12} | " + " | ".join([f"Ratio={r:<10}" for r in RATIOS_SCAL]) + "\n"
        f.write(header_scal)
        f.write("-" * (15 + len(RATIOS_SCAL) * 15) + "\n")
        for i, scale in enumerate(SCALES_SCAL):
            row = f"{scale:<12} | " + " | ".join([f"{results_scal[r][i]:<10.3f}" for r in RATIOS_SCAL]) + "\n"
            f.write(row)
            
        f.write("\n======================= Raw Dictionary Format =======================\n\n")
        f.write(f"results_enum = {results_enum}\n\n")
        f.write(f"results_scal = {results_scal}\n")
        
    print(f"\nAll experimental data successfully logged to '{filepath}'")



def plot_academic_figures(results_enum, results_scal):
    """plot_academic_figures"""
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

    
    def draw_enum_subplot(ax):
        ratios = sorted(results_enum.keys())
        for idx, ratio in enumerate(ratios):
            style, color = styles[idx % len(styles)]
            ax.plot(SCALES_ENUM, results_enum[ratio], style, color=color, 
                    markersize=5, linewidth=1.1, label=f'Known Ratio = {ratio}')
        
        
        ax.set_xscale('linear')
        ax.set_xticks(SCALES_ENUM)
        ax.set_xticklabels([str(s) for s in SCALES_ENUM])
        
        
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%g'))
        
        ax.set_xlabel('Number of Arguments/Relations')
        ax.set_ylabel('Total Runtime (ms)')
        ax.set_title('(a) Enumeration Mode (ALL Models)', fontsize=10, pad=8)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.5)
        ax.legend(loc='upper left', framealpha=0.9)

    
    def draw_scal_subplot(ax):
        ratios = sorted(results_scal.keys())
        for idx, ratio in enumerate(ratios):
            style, color = styles[idx % len(styles)]
            ax.plot(SCALES_SCAL, results_scal[ratio], style, color=color, 
                    markersize=5, linewidth=1.1, label=f'Known Ratio = {ratio}')
        
        
        ax.set_xscale('log')
        ax.set_xticks(SCALES_SCAL)
        ax.get_xaxis().set_major_formatter(ticker.FormatStrFormatter('%g'))
        
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%g'))
        
        ax.set_xlabel('Number of Arguments/Relations')
        ax.set_ylabel('Total Runtime (ms)')
        ax.set_title('(b) Scalability Mode (ONE Model)', fontsize=10, pad=8)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.5)
        ax.legend(loc='upper left', framealpha=0.9)

   
    fig_combined, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.8)) 
    draw_enum_subplot(ax1)
    draw_scal_subplot(ax2)
    plt.tight_layout(pad=0.4)
    fig_combined.savefig('figures/performance_combined.pdf', bbox_inches='tight', pad_inches=0.02)
    fig_combined.savefig('figures/performance_combined.png', bbox_inches='tight', pad_inches=0.02, dpi=300)

   
    fig_a, ax_a = plt.subplots(figsize=(3.6, 2.7))
    draw_enum_subplot(ax_a)
    ax_a.set_title('') 
    plt.tight_layout(pad=0.3)
    fig_a.savefig('figures/performance_enumeration.pdf', bbox_inches='tight', pad_inches=0.02)
    fig_a.savefig('figures/performance_enumeration.png', bbox_inches='tight', pad_inches=0.02, dpi=300)

    
    fig_b, ax_b = plt.subplots(figsize=(3.6, 2.7))
    draw_scal_subplot(ax_b)
    ax_b.set_title('')
    plt.tight_layout(pad=0.3)
    fig_b.savefig('figures/performance_scalability.pdf', bbox_inches='tight', pad_inches=0.02)
    fig_b.savefig('figures/performance_scalability.png', bbox_inches='tight', pad_inches=0.02, dpi=300)

    print("Success: Generated PDF/PNG plots in 'figures/' directory.")



if __name__ == "__main__":
    print("==========================================================")
    print("      FIBAF Pipeline Experiment: One-Click Execution      ")
    print("==========================================================")
    
    results_enumeration = run_experiment_pipeline(SCALES_ENUM, RATIOS_ENUM, "ENUMERATION")
    
    results_scalability = run_experiment_pipeline(SCALES_SCAL, RATIOS_SCAL, "SCALABILITY")
    
    save_all_data_to_file(results_enumeration, results_scalability, DATA_FILE_PATH)
    
    plot_academic_figures(results_enumeration, results_scalability)
    
    print("\n[Finished] All tasks completed successfully.")
