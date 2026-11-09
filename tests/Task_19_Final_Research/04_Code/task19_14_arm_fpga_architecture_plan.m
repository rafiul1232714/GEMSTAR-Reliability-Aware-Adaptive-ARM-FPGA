
%% TASK 19.14 - ARM-FPGA Architecture and Measurement Plan
% GEMSTAR Task 19
%
% Produces:
% 1. Hardware/software partition table
% 2. Candidate FPGA interface specification
% 3. Hardware validation and measurement plan
% 4. Architecture visualization
% 5. Research planning notes
%
% No FPGA hardware is assumed to be available yet.
% No performance, power or resource numbers are invented.
% No additional MATLAB toolbox required.

clear;
clc;
close all;

%% 1. Directories

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");
configDir = fullfile(base,"03_Configurations");
findingDir = fullfile(base,"06_Research_Findings");

folders = [dataDir graphDir configDir findingDir];

for k = 1:numel(folders)
    if ~isfolder(folders(k))
        mkdir(folders(k));
    end
end

fprintf("\n=== TASK 19.14 ARM-FPGA ARCHITECTURE ===\n");

%% 2. Hardware/software partitioning

names = [
    "OSI decoding"
    "XYZ data reception"
    "Valid return counting"
    "ROI filtering"
    "Voxel indexing"
    "Voxel centroid aggregation"
    "RANSAC sample selection"
    "Plane hypothesis calculation"
    "Point-to-plane distance"
    "Inlier counting"
    "SVD plane refinement"
    "Ground classification"
    "Observability monitoring"
    "Processing scheduler"
    "Latency and energy logging"
];

cpuRole = [
    "Initial implementation"
    "Buffer ownership and control"
    "Reference implementation"
    "Reference implementation"
    "Reference implementation"
    "Reference implementation"
    "Initial implementation"
    "Initial implementation"
    "Reference implementation"
    "Reference implementation"
    "Initial implementation"
    "Reference implementation"
    "Initial implementation"
    "Initial implementation"
    "Instrumentation and reporting"
];

fpgaRole = [
    "Not initially proposed"
    "DMA streaming interface"
    "Optional streaming counter"
    "Candidate comparator pipeline"
    "Candidate fixed-point indexing"
    "Later research candidate"
    "Not in first accelerator"
    "Not in first accelerator"
    "First accelerator candidate"
    "First accelerator candidate"
    "Optional later accelerator"
    "First accelerator candidate"
    "Optional lightweight flags"
    "Not initially proposed"
    "Counters only; board power external"
];

priority = [
    "Software"
    "Infrastructure"
    "Medium"
    "Medium"
    "Medium"
    "Later"
    "Software"
    "Software"
    "High"
    "High"
    "Software"
    "High"
    "Medium"
    "Software"
    "High"
];

partition = table();

partition.Operation = names;
partition.CPUResponsibility = cpuRole;
partition.FPGACandidate = fpgaRole;
partition.Priority = priority;

partitionFile = fullfile(dataDir, ...
    "task19_14_hardware_software_partition.csv");

writetable(partition,partitionFile);

%% 3. Proposed accelerator interface
% This is a logical interface contract, not a board-
% specific address map or completed AXI implementation.

signal = [
    "input_valid"
    "input_ready"
    "point_x"
    "point_y"
    "point_z"
    "plane_a"
    "plane_b"
    "plane_c"
    "plane_d"
    "distance_threshold"
    "output_valid"
    "output_ready"
    "ground_flag"
    "inlier_count"
    "frame_done"
];

direction = [
    "Input"
    "Output"
    "Input"
    "Input"
    "Input"
    "Input"
    "Input"
    "Input"
    "Input"
    "Input"
    "Output"
    "Input"
    "Output"
    "Output"
    "Output"
];

definition = [
    "Incoming point transfer valid"
    "Accelerator accepts the next point"
    "Signed fixed-point X coordinate"
    "Signed fixed-point Y coordinate"
    "Signed fixed-point Z coordinate"
    "Quantized plane coefficient A"
    "Quantized plane coefficient B"
    "Quantized plane coefficient C"
    "Quantized plane offset D"
    "Quantized classification tolerance"
    "Output result is valid"
    "Downstream result acceptance"
    "Point classified as plane inlier"
    "Number of accepted inliers"
    "Frame processing completed"
];

interface = table();

interface.Signal = signal;
interface.Direction = direction;
interface.Definition = definition;

interfaceFile = fullfile(configDir, ...
    "task19_14_candidate_accelerator_interface.csv");

writetable(interface,interfaceFile);

%% 4. Planned evaluation matrix

testName = [
    "Floating-point CPU reference"
    "INT16 software emulation"
    "RTL functional simulation"
    "FPGA-only kernel timing"
    "ARM CPU implementation"
    "ARM plus FPGA integrated timing"
    "Energy per processed frame"
    "Deadline miss comparison"
    "Quantization quality validation"
];

requiredEvidence = [
    "Repeatable MATLAB or C results"
    "Fixed-scale numerical error and label changes"
    "RTL testbench and waveform evidence"
    "Hardware cycle counts at measured clock"
    "ARM execution-time measurements"
    "DMA plus accelerator plus CPU timings"
    "Board power trace and duration"
    "Timestamped execution samples"
    "Comparison against independent reference labels"
];

status = repmat("NOT_MEASURED",numel(testName),1);

status(1) = "SOFTWARE_BASELINE_AVAILABLE";
status(2) = "PARTIAL_FRAME150_STUDY";

validation = table();

validation.Experiment = testName;
validation.RequiredEvidence = requiredEvidence;
validation.Status = status;

validationFile = fullfile(dataDir, ...
    "task19_14_hardware_validation_matrix.csv");

writetable(validation,validationFile);

%% 5. Diagram

fig = figure("Color","w", ...
    "Position",[100 100 1200 650]);

axis([0 12 0 7]);
axis off;
hold on;

drawBox(3.6,5.9,4.8,0.75, ...
    "GEMSTAR / OSI / XYZ", [0.90 0.94 0.99]);

drawBox(3.6,4.55,4.8,0.75, ...
    "ARM: buffers + health + scheduler", ...
    [0.92 0.92 0.92]);

drawBox(0.6,2.65,4.4,0.95, ...
    "ARM CPU processing path", ...
    [0.91 0.95 0.91]);

drawBox(7.0,2.65,4.4,0.95, ...
    "FPGA fixed-point accelerator", ...
    [0.99 0.95 0.85]);

drawBox(3.0,0.6,6.0,0.85, ...
    "Validation: labels / latency / energy", ...
    [0.94 0.90 0.98]);

plot([6 6],[5.9 5.3],"k-","LineWidth",1.8);

plot([6 6],[4.55 4.0],"k-","LineWidth",1.8);
plot([2.8 9.2],[4.0 4.0],"k-","LineWidth",1.8);
plot([2.8 2.8],[4.0 3.6],"k-","LineWidth",1.8);
plot([9.2 9.2],[4.0 3.6],"k-","LineWidth",1.8);

plot([2.8 2.8],[2.65 1.9],"k-","LineWidth",1.8);
plot([9.2 9.2],[2.65 1.9],"k-","LineWidth",1.8);
plot([2.8 9.2],[1.9 1.9],"k-","LineWidth",1.8);
plot([6 6],[1.9 1.45],"k-","LineWidth",1.8);

title("GEMSTAR - Proposed ARM-FPGA HW/SW Architecture", ...
    "FontSize",14);

subtitle("Conceptual architecture only - no hardware validation yet");

graphFile = fullfile(graphDir, ...
    "task19_14_arm_fpga_architecture.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 6. Research notes

notesFile = fullfile(findingDir, ...
    "task19_14_hardware_implementation_plan.txt");

fid = fopen(notesFile,"w");

assert(fid~=-1,"Could not create research notes.");

fprintf(fid,"TASK 19.14 - ARM-FPGA IMPLEMENTATION PLAN\n\n");

fprintf(fid,"1. SOFTWARE REFERENCE\n");
fprintf(fid,"Preserve existing double-precision processing.\n");
fprintf(fid,"Use reproducible input point clouds and reference outputs.\n\n");

fprintf(fid,"2. FIRST FPGA KERNEL\n");
fprintf(fid,"Implement point-to-plane distance and inlier counting.\n");
fprintf(fid,"Use signed fixed-point arithmetic with explicit scaling.\n");
fprintf(fid,"Widen products and accumulators to avoid overflow.\n\n");

fprintf(fid,"3. NUMERICAL VALIDATION\n");
fprintf(fid,"Start with INT16 XYZ candidate precision.\n");
fprintf(fid,"Calibrate scales on separate frames/recordings.\n");
fprintf(fid,"Use independent frames for validation.\n");
fprintf(fid,"Validate plane coefficients and arithmetic precision.\n\n");

fprintf(fid,"4. HARDWARE INTEGRATION\n");
fprintf(fid,"Select actual ARM-FPGA board and toolchain.\n");
fprintf(fid,"Specify AXI stream/control and DMA requirements.\n");
fprintf(fid,"Confirm clock frequency, memory and resource limits.\n");
fprintf(fid,"Use identical input data for CPU and FPGA comparison.\n\n");

fprintf(fid,"5. MEASUREMENTS\n");
fprintf(fid,"Measure software, DMA, accelerator and total latency.\n");
fprintf(fid,"Measure real board power with appropriate instrumentation.\n");
fprintf(fid,"Energy per frame = measured energy over the frame interval.\n");
fprintf(fid,"Account for idle baseline and system-level power.\n");
fprintf(fid,"Report LUT, FF, BRAM and DSP utilization from implementation.\n\n");

fprintf(fid,"6. RESEARCH LIMITATIONS\n");
fprintf(fid,"No FPGA implementation completed in Task 19.14.\n");
fprintf(fid,"No measured hardware energy or FPGA speedup.\n");
fprintf(fid,"INT8 and INT16 results currently from one frame.\n");
fprintf(fid,"Full RANSAC agreement is not verified obstacle accuracy.\n");

fclose(fid);

%% 7. Completion

fprintf("\n=== TASK 19.14 COMPLETE ===\n");
fprintf("Partition CSV: %d\n",isfile(partitionFile));
fprintf("Interface CSV: %d\n",isfile(interfaceFile));
fprintf("Validation matrix: %d\n",isfile(validationFile));
fprintf("Architecture graph: %d\n",isfile(graphFile));
fprintf("Research notes: %d\n",isfile(notesFile));

fprintf("\nProposed first FPGA kernel:\n");
fprintf("Fixed-point point-to-plane distance + inlier count.\n");

fprintf("\nIMPORTANT:\n");
fprintf("This is an architecture specification, not implemented hardware.\n");
fprintf("No ARM-FPGA performance or energy has been measured.\n");

%% Local function

function drawBox(x,y,w,h,txt,color)

    rectangle("Position",[x y w h], ...
        "FaceColor",color, ...
        "EdgeColor",[0.3 0.3 0.3], ...
        "LineWidth",1.5);

    text(x+w/2,y+h/2,txt, ...
        "HorizontalAlignment","center", ...
        "VerticalAlignment","middle", ...
        "FontSize",11, ...
        "FontWeight","bold");

end
