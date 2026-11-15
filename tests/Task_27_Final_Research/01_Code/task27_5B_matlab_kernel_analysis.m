%% GEMSTAR TASK 27.5B
% Computational structure and nominal memory analysis.
% Actual FLOPs, DRAM bandwidth and hardware energy are NOT measured.

clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_27_Final_Research';
csvDir = fullfile(root,'02_CSV_Data');
plotDir = fullfile(root,'04_Plots');
reportDir = fullfile(root,'06_Research_Findings');

fprintf('=== TASK 27.5B MATLAB KERNEL ANALYSIS ===\n');

%% 1. Load numerical evidence

summaryPath = fullfile(csvDir,'task27_5A_kernel_summary.csv');
structurePath = fullfile(csvDir,'task27_5A_kernel_structure.csv');
lidarPath = fullfile(csvDir,'task27_3A_lidar_workload_metrics.csv');
cameraPath = fullfile(csvDir,'task27_4C_sensor_compute_characterization.csv');

optsS = detectImportOptions(summaryPath,'VariableNamingRule','preserve');
optsS = setvartype(optsS,'stage','string');
S = readtable(summaryPath,optsS);

optsK = detectImportOptions(structurePath,'VariableNamingRule','preserve');
optsK = setvartype(optsK,{'stage','scenario'},'string');
K = readtable(structurePath,optsK);

L = readtable(lidarPath,'VariableNamingRule','preserve');

optsC = detectImportOptions(cameraPath,'VariableNamingRule','preserve');
optsC = setvartype(optsC,{'workload','scenario','mode'},'string');
C = readtable(cameraPath,optsC);

assert(height(S)==5,'Expected five kernel types');
assert(height(K)==129,'Expected 129 structural records');
assert(height(L)==53,'Expected 53 LiDAR frames');
assert(height(C)==23,'Expected 23 sensor records');

assert(~any(ismissing(S.stage)),'Missing kernel stage label');
assert(~any(ismissing(C.workload)),'Missing workload label');
assert(~any(ismissing(C.scenario)),'Missing scenario label');
assert(~any(ismissing(C.mode)),'Missing processing-mode label');

assert(sum(double(L.input_points))==172839, ...
    'LiDAR input count mismatch');
assert(sum(double(L.filtered_points))==16295, ...
    'LiDAR filtered count mismatch');

%% 2. Protect existing outputs

names = {
    'Task27_Fig21_Kernel_CPU_Latency'
    'Task27_Fig22_LiDAR_Workload_Structure'
    'Task27_Fig23_Camera_Memory_vs_Latency'
    'Task27_Fig24_LiDAR_Grid_Probe_Model'
};

outCSV = fullfile(csvDir,'task27_5B_matlab_kernel_summary.csv');
outTXT = fullfile(reportDir,'task27_5B_matlab_kernel_findings.txt');

assert(~isfile(outCSV),'Existing numerical output preserved');
assert(~isfile(outTXT),'Existing findings preserved');

for j = 1:numel(names)
    assert(~isfile(fullfile(plotDir,[names{j} '.png'])), ...
        'Existing PNG preserved');
    assert(~isfile(fullfile(plotDir,[names{j} '.fig'])), ...
        'Existing FIG preserved');
end

%% 3. Figure 21: CPU stage timing

stages = [
    "LiDAR_filter"
    "LiDAR_cluster"
    "Camera_preprocessing"
    "Radar_valid_returns"
    "YOLO11s_predict"
];

labels = {
    'LiDAR filter'
    'LiDAR cluster'
    'Camera preprocessing'
    'Radar batch'
    'YOLO11s predict'
};

stageMedian = zeros(5,1);
stageCount = zeros(5,1);

for j = 1:5
    mask = strcmp(strtrim(S.stage),stages(j));
    assert(nnz(mask)==1,'Missing or duplicate kernel type');

    stageMedian(j) = double( ...
        S.median_of_record_medians_ms(mask));

    stageCount(j) = double(S.records(mask));
end

assert(all(stageMedian>0),'Nonpositive CPU latency');
assert(isequal(stageCount,[53;53;6;12;5]), ...
    'Kernel group counts mismatch');

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1150 600]);

bar(1:5,stageMedian);
set(gca,'YScale','log');
xticks(1:5);
xticklabels(labels);
xtickangle(18);
ylabel('Median of Record Medians (ms, log scale)');
title('GEMSTAR CPU Kernel Timing Overview');
subtitle('Different processing scopes; not equivalent frame deadlines');
grid on;

savefig(f,fullfile(plotDir,[names{1} '.fig']));
exportgraphics(f,fullfile(plotDir,[names{1} '.png']), ...
    'Resolution',300);
close(f);

%% 4. Figure 22: LiDAR workload structure

[frames,order] = sort(double(L.frame));
L = L(order,:);

inputN = double(L.input_points);
filteredN = double(L.filtered_points);
cells = double(L.occupied_grid_cells);

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1150 600]);

yyaxis left
plot(frames,inputN,'-','LineWidth',1.5);
hold on;
plot(frames,filteredN,'-','LineWidth',1.5);
ylabel('LiDAR Points');

yyaxis right
plot(frames,cells,'-o','LineWidth',1.3);
ylabel('Occupied XY Grid Cells');

xlabel('Recorded Frame ID');
title('LiDAR Point Reduction and Grid Working Set');
legend('Input points','Retained points','Occupied cells', ...
    'Location','best');
grid on;

savefig(f,fullfile(plotDir,[names{2} '.fig']));
exportgraphics(f,fullfile(plotDir,[names{2} '.png']), ...
    'Resolution',300);
close(f);

%% 5. Figure 23: Camera buffer size versus CPU time

cam = C(strcmp(strtrim(C.workload),"Camera"),:);
assert(height(cam)==6,'Expected six Camera configurations');

bufferMiB = double( ...
    cam.nominal_intermediate_buffer_sum_bytes)/1048576;
cameraMs = double(cam.archived_cpu_median_ms);

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1100 590]);

hold on;

for j = 1:height(cam)
    mode = strtrim(cam.mode(j));

    if mode == "FULL"
        marker = 'o';
    elseif mode == "ROI"
        marker = 's';
    else
        error('Unknown Camera processing mode');
    end

    scatter(bufferMiB(j),cameraMs(j),100,marker,'filled');

    text(bufferMiB(j)+0.07,cameraMs(j), ...
        char(strtrim(cam.scenario(j))+" "+mode), ...
        'FontSize',9);
end

xlabel('Nominal Named Camera Buffers (MiB)');
ylabel('Archived CPU Median Preprocessing Time (ms)');
title('Camera Buffer Size vs Processing Latency');
xlim([0 max(bufferMiB)+1.3]);
grid on;

savefig(f,fullfile(plotDir,[names{3} '.fig']));
exportgraphics(f,fullfile(plotDir,[names{3} '.png']), ...
    'Resolution',300);
close(f);

%% 6. Figure 24: LiDAR grid-probe workload model

% Original algorithm examines a 3x3 neighborhood for
% each visited occupied grid cell.
% Structural estimate = 9 * occupied cells.
% This is NOT CPU instruction or FLOP count.

probes = 9*cells;
clusterMs = double(L.median_cluster_ms);

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1100 590]);

scatter(probes,clusterMs,65,filteredN,'filled');

xlabel('Modeled Neighbor-Cell Key Checks');
ylabel('Archived Median Clustering Time (ms)');
title('LiDAR Grid Traversal Structure vs CPU Time');
cb = colorbar;
cb.Label.String = 'Retained LiDAR Points';
grid on;

savefig(f,fullfile(plotDir,[names{4} '.fig']));
exportgraphics(f,fullfile(plotDir,[names{4} '.png']), ...
    'Resolution',300);
close(f);

%% 7. Save numerical summary

D = table(stages,stageCount,stageMedian, ...
    'VariableNames',{'Stage','Records','MedianOfRecordMediansMs'});

writetable(D,outCSV);

%% 8. Save research findings

totalInput = sum(inputN);
totalFiltered = sum(filteredN);
reduction = 100*(1-totalFiltered/totalInput);

fid = fopen(outTXT,'w');
assert(fid>0,'Cannot create findings report');

fprintf(fid,'GEMSTAR TASK 27.5B\n');
fprintf(fid,'Computational and Nominal Memory Analysis\n');
fprintf(fid,'========================================\n\n');

fprintf(fid,'Kernel types: %d\n',height(S));
fprintf(fid,'Structural records: %d\n',height(K));
fprintf(fid,'LiDAR frames: %d\n',height(L));
fprintf(fid,'Camera configurations: %d\n',height(cam));

fprintf(fid,'\nLIDAR:\n');
fprintf(fid,'Input points: %.0f\n',totalInput);
fprintf(fid,'Retained points: %.0f\n',totalFiltered);
fprintf(fid,'Point reduction: %.4f%%\n',reduction);
fprintf(fid,'Mean occupied cells: %.4f\n',mean(cells));
fprintf(fid,'Total modeled neighbor probes: %.0f\n',sum(probes));

fprintf(fid,'\nARCHIVED CPU MEDIANS:\n');
for j = 1:5
    fprintf(fid,'%s: %.6f ms\n',char(stages(j)),stageMedian(j));
end

fprintf(fid,'\nLIMITATIONS:\n');
fprintf(fid,'CPU timing boundaries differ across stages.\n');
fprintf(fid,'Camera buffers are named nominal arrays, not DRAM traffic.\n');
fprintf(fid,'Grid probes are structural counts, not CPU instructions.\n');
fprintf(fid,'No validated operation counts or arithmetic intensity.\n');
fprintf(fid,'No hardware compute or memory ceilings measured.\n');
fprintf(fid,'Therefore, this is not an empirical roofline plot.\n');
fprintf(fid,'No FPGA execution or energy measurement.\n');
fprintf(fid,'No perception-quality equivalence established.\n');
fclose(fid);

%% 9. Completion

fprintf('KERNEL_TYPES: %d\n',height(S));
fprintf('STRUCTURAL_RECORDS: %d\n',height(K));
fprintf('LIDAR_FRAMES: %d\n',height(L));
fprintf('CAMERA_CONFIGURATIONS: %d\n',height(cam));
fprintf('TOTAL_MODELED_LIDAR_NEIGHBOR_PROBES: %.0f\n',sum(probes));
fprintf('FIGURES_CREATED: 4 PNG + 4 FIG\n');
fprintf('SUMMARY_CSV_CREATED: YES\n');
fprintf('FINDINGS_CREATED: YES\n');
fprintf('EMPIRICAL_ROOFLINE_ESTABLISHED: NO\n');
fprintf('TASK27_5B_MATLAB_KERNEL_ANALYSIS_DONE\n');