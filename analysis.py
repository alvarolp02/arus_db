import pandas as pd
import matplotlib.pyplot as plt
import os

def analyze_log(filepath, output_dir):
    df = pd.read_csv(filepath, sep="\t", names=["timestamp","signal","value"])
    avg = df["value"].mean()

    plt.figure()
    plt.plot(df["timestamp"], df["value"])
    plt.title(f"Señales de {os.path.basename(filepath)}")
    plt.xlabel("Tiempo")
    plt.ylabel("Valor")
    os.makedirs(output_dir, exist_ok=True)
    graph_path = os.path.join(output_dir, os.path.basename(filepath) + ".png")
    plt.savefig(graph_path)
    plt.close()

    return avg, graph_path
