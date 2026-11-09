%% TASK 21.9 - HARDWARE ACCELERATION CANDIDATES
clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';
task = fullfile(root,'tests','Task_21_Final_Research');

benchDir = fullfile(task,'05_Benchmark_Results');
graphDir = fullfile(task,'03_Graphs');
csvDir = fullfile(task,'04_CSV_Results');
findDir = fullfile(task,'06_Research_Findings');

source = fullfile(benchDir, ...
    'task21_08_language_comparison.csv');

if ~isfile(source)
    error('Task 21.8 comparison CSV missing.');
end

T = readtable(source,'TextType','string');

required = ["Method","MedianMsPerDataset","Language"];
assert(all(ismember(required,string(T.Properties.VariableNames))), ...
    'Unexpected benchmark CSV columns.');

assert(height(T) == 4, ...
    'Expected four benchmark implementations.');

assert(all(isfinite(T.MedianMsPerDataset) & ...
    T.MedianMsPerDataset > 0), ...
    'Benchmark times must be positive and finite.');

fprintf('\n=== TASK 21.9 ACCELERATION ANALYSIS ===\n');

T = sortrows(T,'MedianMsPerDataset');

disp(T(:,{'Method','MedianMsPerDataset','Language'}));

%% COMPARISON GRAPH - LOGARITHMIC TIME AXIS

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1050 650]);

bar(T.MedianMsPerDataset);

set(gca,'XTick',1:height(T), ...
    'XTickLabel',cellstr(T.Method), ...
    'YScale','log');

ylabel('Median execution time (ms, log scale)');
xlabel('Implementation');
title('Radar aggregation: MATLAB vs Python');
grid on;
xtickangle(20);

graphPath = fullfile(graphDir, ...
    'task21_09_language_comparison.png');

print(f,graphPath,'-dpng','-r180');
close(f);

%% PRELIMINARY HARDWARE CANDIDATE SCREENING

% These are engineering hypotheses, not measured FPGA results.
workloads = [
    "Radar frame aggregation"
    "LiDAR point filtering"
    "LiDAR voxel reduction"
    "Camera spatial filtering"
    "Sensor fusion / EKF"
];

status = [
    "Desktop benchmark available"
    "Requires CPU profiling"
    "Requires CPU profiling"
    "Requires CPU profiling"
    "Requires quality + CPU profiling"
];

candidate = [
    "Low initial priority"
    "Potential FPGA candidate"
    "Potential FPGA candidate"
    "Potential FPGA candidate"
    "Prefer CPU baseline initially"
];

reason = [
    "Very small measured compute time; transfer overhead may dominate"
    "Streaming comparisons may be efficient in hardware"
    "Potential point-count and bandwidth reduction"
    "Regular pixel operations suit pipelined hardware"
    "Association and tracking are control-heavy; validate on CPU first"
];

hardwareScreen = table(workloads,status,candidate,reason, ...
    'VariableNames', ...
    {'Workload','EvidenceStatus','InitialDecision','Reason'});

screenPath = fullfile(csvDir, ...
    'task21_09_hardware_candidate_screen.csv');

writetable(hardwareScreen,screenPath);

%% RESEARCH FINDINGS

bestTime = T.MedianMsPerDataset(1);
worstTime = T.MedianMsPerDataset(end);

findingPath = fullfile(findDir, ...
    'task21_09_hardware_candidate_findings.txt');

fid = fopen(findingPath,'w');
if fid < 0
    error('Cannot write research findings.');
end

fprintf(fid,'TASK 21.9 - HARDWARE ACCELERATION SCREEN\n\n');
fprintf(fid,'Fastest measured implementation: %s\n',T.Method(1));
fprintf(fid,'Fastest time: %.9f ms per dataset\n',bestTime);
fprintf(fid,'Slowest time: %.9f ms per dataset\n',worstTime);
fprintf(fid,'Slowest/fastest time ratio: %.3f\n', ...
    worstTime/bestTime);

fprintf(fid,'\nPRELIMINARY INTERPRETATION\n');
fprintf(fid,'Radar aggregation is a low-priority FPGA candidate.\n');
fprintf(fid,'LiDAR and camera kernels require actual profiling.\n');
fprintf(fid,'Small CPU execution time does not prove low energy.\n');
fprintf(fid,'No ARM measurements or FPGA power results exist yet.\n');
fprintf(fid,'PCIe is not assumed; actual SoC AXI/DMA overhead');
fprintf(fid,' must be measured later.\n');
fprintf(fid,'The comparison is desktop compute-kernel only.\n');

fclose(fid);

fprintf('\n=== TASK 21.9 FILE CHECK ===\n');
fprintf('Graph saved: %d\n',isfile(graphPath));
fprintf('Candidate CSV saved: %d\n',isfile(screenPath));
fprintf('Findings saved: %d\n',isfile(findingPath));

fprintf('\n=== TASK 21.9 COMPLETE ===\n');
