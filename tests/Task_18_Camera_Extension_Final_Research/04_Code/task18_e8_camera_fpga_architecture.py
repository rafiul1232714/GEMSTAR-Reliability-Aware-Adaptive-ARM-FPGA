from pathlib import Path
import csv
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_18_Camera_Extension_Final_Research"
)

DATA = BASE / "02_CSV_Data"
CONFIG = BASE / "03_Configurations"
GRAPHS = BASE / "01_Graphs"
FINDINGS = BASE / "06_Research_Findings"

for folder in (DATA, CONFIG, GRAPHS, FINDINGS):
    folder.mkdir(parents=True, exist_ok=True)

def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

print("\n=== TASK 18.E8 FPGA ARCHITECTURE ===")

# 1. Candidate RTL modules

modules = [
    ("camera_axi_input.vhd", "AXI stream input, framing",
     "8-bit pixel input", "HIGH"),
    ("camera_line_buffer.vhd", "Two line buffers",
     "8-bit pixels, configurable image width", "HIGH"),
    ("camera_window_3x3.vhd", "Sliding 3x3 pixel window",
     "Nine unsigned 8-bit pixels", "HIGH"),
    ("camera_sobel_x.vhd", "Horizontal gradient",
     "Signed 11-bit", "HIGH"),
    ("camera_sobel_y.vhd", "Vertical gradient",
     "Signed 11-bit", "HIGH"),
    ("camera_gradient_combine.vhd",
     "Absolute values, averaging, output saturation",
     "Widened unsigned intermediate, 8-bit output", "HIGH"),
    ("camera_axi_output.vhd", "AXI output and frame markers",
     "8-bit output pixels", "HIGH"),
    ("camera_control.vhd", "Reset, status and frame counters",
     "Integer/control signals", "MEDIUM"),
    ("camera_sobel_top.vhd", "Integrate RTL hierarchy",
     "Parameterized pipeline", "HIGH"),
    ("tb_camera_sobel.vhd", "RTL verification testbench",
     "Bit-accurate expected values", "HIGH"),
]

module_rows = [
    {
        "Module": name,
        "Purpose": purpose,
        "DataFormat": precision,
        "Priority": priority,
        "Status": "PLANNED_NOT_IMPLEMENTED"
    }
    for name, purpose, precision, priority in modules
]

module_file = DATA / "task18_e8_rtl_module_inventory.csv"
write_csv(module_file, module_rows)

# 2. Numerical design contract

spec = {
    "task": "18.E8",
    "implementation_status": "ARCHITECTURE_ONLY",
    "target_platform": "AMD Kria K26 candidate",
    "input_width": 640,
    "input_height": 480,
    "input_pixel_format": "uint8_grayscale",
    "sobel_gradient_format": "signed_11_bit",
    "sobel_gradient_min": -1020,
    "sobel_gradient_max": 1020,
    "absolute_gradient_max": 1020,
    "abs_gradient_sum_max": 2040,
    "sum_intermediate_format": "unsigned_11_bit",
    "output_format": "uint8",
    "two_row_buffer_min_bytes": 1280,
    "sobel_x": [
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1]
    ],
    "sobel_y": [
        [-1, -2, -1],
        [0, 0, 0],
        [1, 2, 1]
    ],
    "output_operation": (
        "OpenCV-style 0.5*abs(Gx)+0.5*abs(Gy), "
        "rounded and saturated to uint8; "
        "exact rounding to be verified in RTL"
    ),
    "border_policy": (
        "Match OpenCV BORDER_DEFAULT "
        "(reflect_101) before comparison"
    ),
    "stream_interface": "AXI4-Stream candidate",
    "frame_boundary_policy": (
        "To define and verify using TLAST/"
        "TUSER in the eventual AXI video wrapper"
    ),
    "hardware_latency_measured": False,
    "hardware_energy_measured": False,
    "rtl_verified": False
}

spec_file = CONFIG / "task18_e8_camera_fixed_point_spec.json"

spec_file.write_text(
    json.dumps(spec, indent=2),
    encoding="utf-8"
)

# 3. Verification matrix

tests = [
    ("All-black image", "Zero gradients"),
    ("Uniform gray image", "Zero gradients"),
    ("Horizontal edge", "Correct vertical gradient"),
    ("Vertical edge", "Correct horizontal gradient"),
    ("Maximum contrast", "No arithmetic overflow"),
    ("Border pixels", "Match reflect_101 policy"),
    ("Randomized image", "Bit-accurate software comparison"),
    ("Backpressure", "No dropped or duplicated pixels"),
    ("Reset during frame", "Defined recovery behavior"),
    ("Multiple frames", "Correct frame boundaries"),
    ("Frame size", "Correct image dimensions"),
    ("Kria deployment", "Actual FPGA and DMA verification"),
]

verification_rows = [
    {
        "Test": test,
        "ExpectedBehavior": expected,
        "Status": "NOT_RUN"
    }
    for test, expected in tests
]

verification_file = (
    DATA / "task18_e8_camera_rtl_verification_plan.csv"
)

write_csv(verification_file, verification_rows)

# 4. Draw conceptual architecture

fig, ax = plt.subplots(figsize=(12, 9))
ax.set_xlim(0, 12)
ax.set_ylim(0, 11)
ax.axis("off")

def box(x, y, w, h, label):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.08",
        linewidth=1.3,
        facecolor="#eaf0f6",
        edgecolor="#50647b"
    )
    ax.add_patch(patch)
    ax.text(
        x+w/2, y+h/2, label,
        ha="center", va="center",
        fontsize=10, fontweight="bold"
    )

def arrow(x1, y1, x2, y2):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops={"arrowstyle": "->", "lw": 1.8}
    )

box(3.3, 9.7, 5.4, 0.75,
    "ARM / DMA -> AXI4-Stream input")
box(3.3, 8.4, 5.4, 0.75,
    "Two row buffers + 3x3 sliding window")

box(0.9, 6.65, 4.2, 0.9,
    "Sobel Gx: signed 11-bit")
box(6.9, 6.65, 4.2, 0.9,
    "Sobel Gy: signed 11-bit")

box(3.3, 4.9, 5.4, 0.9,
    "Absolute gradients + combine")

box(3.3, 3.4, 5.4, 0.75,
    "Round + saturate -> uint8")

box(3.3, 2.0, 5.4, 0.75,
    "AXI4-Stream output -> ARM")

box(3.3, 0.6, 5.4, 0.75,
    "Future Kria RTL / DMA validation")

arrow(6, 9.7, 6, 9.15)
arrow(6, 8.4, 6, 7.95)
arrow(6, 7.95, 3, 7.55)
arrow(6, 7.95, 9, 7.55)
arrow(3, 6.65, 5, 5.8)
arrow(9, 6.65, 7, 5.8)
arrow(6, 4.9, 6, 4.15)
arrow(6, 3.4, 6, 2.75)
arrow(6, 2, 6, 1.35)

ax.set_title(
    "GEMSTAR Camera Sobel FPGA Architecture\n"
    "Conceptual design - RTL not implemented",
    fontsize=15, fontweight="bold"
)

graph_file = GRAPHS / "task18_e8_camera_fpga_architecture.png"

fig.savefig(graph_file, dpi=180, bbox_inches="tight")
plt.close(fig)

# 5. Research notes

notes = """TASK 18.E8 - CAMERA FPGA ARCHITECTURE

PURPOSE
Translate the completed GEMSTAR Sobel fixed-point
experiment into a hardware implementation specification.

COMPLETED SOFTWARE EVIDENCE
- Task 18.E3: 20 extracted camera frames.
- Task 18.E4: brightness/contrast/edge statistics.
- Task 18.E5: provisional observability monitor.
- Task 18.E6: PC preprocessing timing comparison.
- Task 18.E7: exact INT16 Sobel gradient comparison.

PROPOSED HARDWARE
- Unsigned 8-bit grayscale input.
- 3x3 Sobel convolution.
- Signed 11-bit X and Y gradient datapaths.
- Correctly widened magnitude arithmetic.
- Eight-bit output with defined rounding/saturation.
- Two line buffers and sliding window.
- AXI4-Stream interfaces and ARM-side DMA.

IMPORTANT DESIGN RISKS
- Exactly match image border handling.
- Exactly match output rounding and saturation.
- Correctly align valid data and frame markers.
- Respect ready/valid handshake and backpressure.
- Check overflow and signed arithmetic.
- Do not claim one pixel per clock until verified.
- Test resource/timing feasibility after synthesis.

FUTURE HARDWARE WORK
- Implement VHDL/Verilog modules.
- Build bit-accurate testbench.
- Synthesize and place/route.
- Integrate on AMD Kria.
- Measure CPU-only and FPGA-assisted latency.
- Measure actual energy and power consumption.

CURRENT STATUS
Architecture prepared; RTL and FPGA not implemented.
"""

notes_file = (
    FINDINGS / "task18_e8_camera_fpga_research_notes.txt"
)
notes_file.write_text(notes, encoding="utf-8")

print("\n=== TASK 18.E8 COMPLETE ===")
print("RTL module inventory:", module_file.is_file())
print("Fixed-point spec:", spec_file.is_file())
print("RTL verification plan:", verification_file.is_file())
print("Architecture diagram:", graph_file.is_file())
print("Research notes:", notes_file.is_file())
print("Proposed RTL modules:", len(module_rows))
print("Verification cases:", len(verification_rows))

print("\nIMPORTANT:")
print("This is hardware architecture preparation.")
print("No RTL implementation or Kria FPGA result yet.")

