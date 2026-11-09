from pathlib import Path
from collections import Counter
import csv
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_16_Final_Research"
)

DATA = BASE / "02_CSV_Data"
GAP = BASE / "05_Research_Gap"
GRAPHS = BASE / "01_Graphs"
GRAPHS.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


papers = read_csv(DATA / "task16_literature_database.csv")
risks = read_csv(GAP / "task16_novelty_risk_assessment.csv")

# Graph 1: Literature categories
categories = Counter(
    paper["Category"] for paper in papers
)

labels, values = zip(
    *sorted(categories.items(), key=lambda x: x[1])
)

fig, ax = plt.subplots(figsize=(11, 8))

ax.barh(labels, values)

ax.set_title("Task 16 - Literature by Research Category")
ax.set_xlabel("Number of Papers")
ax.set_ylabel("Research Category")

ax.set_xlim(0, max(values) + 1)
ax.set_xticks(range(0, max(values) + 2))

fig.tight_layout()

graph1 = GRAPHS / "task16_literature_categories.png"
fig.savefig(graph1, dpi=200, bbox_inches="tight")
plt.close(fig)


# Graph 2: Novelty risks
risk_counts = Counter(
    item["NoveltyRisk"] for item in risks
)

risk_labels = sorted(risk_counts)
risk_values = [risk_counts[x] for x in risk_labels]

fig, ax = plt.subplots(figsize=(7, 5))

bars = ax.bar(risk_labels, risk_values)

ax.set_title("Task 16 - Preliminary Novelty Risk")
ax.set_ylabel("Number of Research Areas")
ax.set_ylim(0, max(risk_values) + 1)

for bar, value in zip(bars, risk_values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        value + 0.1,
        str(value),
        ha="center"
    )

fig.tight_layout()

graph2 = GRAPHS / "task16_novelty_risk.png"
fig.savefig(graph2, dpi=200, bbox_inches="tight")
plt.close(fig)

print("\n=== TASK 16.13 RESEARCH GRAPHS ===")
print("Literature papers:", len(papers))
print("Novelty areas:", len(risks))
print("Graph 1 exists:", graph1.exists())
print("Graph 2 exists:", graph2.exists())
print("Graphs saved in:", GRAPHS)