%% GEMSTAR TASK 27.3B
% LiDAR spatial and computational workload analysis
% Uses original Task 24 points and archived CPU timings.
% Never modifies the original datasets.

clear; clc; close all;

tests = 'E:\GEMSTAR_Project\sensor-health-monitor\tests';

task27 = fullfile(tests,'Task_27_Final_Research');
dataDir = fullfile(task27,'02_CSV_Data');
plotDir = fullfile(task27,'04_Plots');
findDir = fullfile(task27,'06_Research_Findings');

rawPath = fullfile(tests, ...
    'Task_24_Final_Research', ...
    '09_Controlled_Scenario', ...
    'C02_MovingTarget', ...
    'C02_V2_EKF_Input_53Frames_V1', ...
    'lidar_points.csv');

metricPath = fullfile(dataDir, ...
    'task27_3A_lidar_workload_metrics.csv');

fprintf('=== TASK 27.3B MATLAB LIDAR ANALYSIS ===\n');

%% 1. Load verified datasets

R = readtable(rawPath,'VariableNamingRule','preserve');
M = readtable(metricPath,'VariableNamingRule','preserve');

assert(height(R)==172839,'Unexpected raw LiDAR count');
assert(height(M)==53,'Unexpected workload frame count');
assert(sum(M.input_points)==172839,'Input count mismatch');
assert(sum(M.filtered_points)==16295,'Filtered count mismatch');

frames = double(M.frame);
[frames,idx] = sort(frames);
M = M(idx,:);

%% 2. Reproduce original spatial-filter conditions

x = double(R.x_vehicle_m);
y = double(R.y_vehicle_m);
z = double(R.z_vehicle_m);

valid = isfinite(x) & isfinite(y) & isfinite(z) ...
    & x>=3.0 & x<=60.0 ...
    & abs(y)<=15.0 ...
    & z>=0.45 & z<=3.50;

assert(nnz(valid)==16295, ...
    'Spatial filtering differs from Task 27.3A');

%% 3. Select recorded frame 530 for visualization

frameID = 530;
frameMask = double(R.frame)==frameID;
keptMask = frameMask & valid;

assert(any(frameMask),'Frame 530 missing');
assert(nnz(keptMask)==M.filtered_points(M.frame==frameID), ...
    'Frame 530 filtered count mismatch');

%% 4. Figure 1: 3D LiDAR raw and filtered data

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1200 560]);

tiledlayout(1,2);

nexttile;
scatter3(x(frameMask),y(frameMask),z(frameMask), ...
    5,z(frameMask),'filled');
xlabel('X (m)'); ylabel('Y (m)'); zlabel('Z (m)');
title(sprintf('Raw LiDAR - Frame %d',frameID));
axis equal; grid on; view(35,25);
colorbar;

nexttile;
scatter3(x(keptMask),y(keptMask),z(keptMask), ...
    12,z(keptMask),'filled');
xlabel('X (m)'); ylabel('Y (m)'); zlabel('Z (m)');
title(sprintf('Filtered LiDAR - Frame %d',frameID));
axis equal; grid on; view(35,25);
colorbar;

savefig(f,fullfile(plotDir, ...
    'Task27_Fig05_LiDAR_3D_Raw_Filtered.fig'));

exportgraphics(f,fullfile(plotDir, ...
    'Task27_Fig05_LiDAR_3D_Raw_Filtered.png'), ...
    'Resolution',300);
close(f);

%% 5. Figure 2: Point retention by frame

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1100 540]);

plot(frames,M.input_points,'-o','LineWidth',1.4);
hold on;
plot(frames,M.filtered_points,'-s','LineWidth',1.4);

xlabel('Frame ID');
ylabel('Number of LiDAR Points');
title('LiDAR Input vs Filtered Points');
legend('Input','Filtered','Location','best');
grid on;

savefig(f,fullfile(plotDir, ...
    'Task27_Fig06_LiDAR_Retention.fig'));

exportgraphics(f,fullfile(plotDir, ...
    'Task27_Fig06_LiDAR_Retention.png'), ...
    'Resolution',300);
close(f);

%% 6. Figure 3: CPU filtering and clustering time

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1100 540]);

plot(frames,M.median_filter_ms,'-o','LineWidth',1.4);
hold on;
plot(frames,M.median_cluster_ms,'-s','LineWidth',1.4);

xlabel('Frame ID');
ylabel('Archived CPU Median Time (ms)');
title('LiDAR CPU Filtering vs Clustering');
legend('Filtering','Clustering','Location','best');
grid on;

savefig(f,fullfile(plotDir, ...
    'Task27_Fig07_LiDAR_CPU_Timing.fig'));

exportgraphics(f,fullfile(plotDir, ...
    'Task27_Fig07_LiDAR_CPU_Timing.png'), ...
    'Resolution',300);
close(f);

%% 7. Figure 4: Grid occupancy and clustering time

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1100 540]);

scatter(M.occupied_grid_cells, ...
    M.median_cluster_ms,55, ...
    M.filtered_points,'filled');

xlabel('Occupied Grid Cells');
ylabel('Archived Median Clustering Time (ms)');
title('LiDAR Grid Occupancy vs CPU Clustering');
cb = colorbar;
cb.Label.String = 'Filtered Points';
grid on;

savefig(f,fullfile(plotDir, ...
    'Task27_Fig08_LiDAR_Grid_Clustering.fig'));

exportgraphics(f,fullfile(plotDir, ...
    'Task27_Fig08_LiDAR_Grid_Clustering.png'), ...
    'Resolution',300);
close(f);

%% 8. Numerical summary and findings

totalInput = sum(M.input_points);
totalKept = sum(M.filtered_points);
reduction = 100*(1-totalKept/totalInput);

filterMedian = median(M.median_filter_ms);
clusterMedian = median(M.median_cluster_ms);

resultPath = fullfile(findDir, ...
    'task27_3B_matlab_lidar_findings.txt');

fid = fopen(resultPath,'w');
assert(fid>0,'Cannot create findings report');

fprintf(fid,'GEMSTAR TASK 27.3B FINDINGS\n');
fprintf(fid,'===========================\n');
fprintf(fid,'Frames analyzed: %d\n',height(M));
fprintf(fid,'Total input points: %d\n',totalInput);
fprintf(fid,'Total filtered points: %d\n',totalKept);
fprintf(fid,'Point reduction: %.4f%%\n',reduction);
fprintf(fid,'Mean occupied cells: %.4f\n', ...
    mean(M.occupied_grid_cells));
fprintf(fid,'Median of per-frame filter medians: %.6f ms\n', ...
    filterMedian);
fprintf(fid,'Median of per-frame cluster medians: %.6f ms\n', ...
    clusterMedian);
fprintf(fid,'3D example frame: %d\n',frameID);
fprintf(fid,'\nLIMITATIONS:\n');
fprintf(fid,'Clustering candidates are not validated object identities.\n');
fprintf(fid,'CPU times are archived development-host measurements.\n');
fprintf(fid,'No ARM or FPGA energy measurement.\n');
fprintf(fid,'No memory bandwidth measurement.\n');
fprintf(fid,'No detection-quality equivalence established.\n');

fclose(fid);

%% 9. Completion report

fprintf('FRAMES_ANALYZED: %d\n',height(M));
fprintf('INPUT_POINTS: %d\n',totalInput);
fprintf('FILTERED_POINTS: %d\n',totalKept);
fprintf('POINT_REDUCTION_PCT: %.4f\n',reduction);
fprintf('MEDIAN_FILTER_MS: %.6f\n',filterMedian);
fprintf('MEDIAN_CLUSTER_MS: %.6f\n',clusterMedian);
fprintf('FIGURES_CREATED: 4 PNG + 4 FIG\n');
fprintf('FINDINGS_CREATED: YES\n');
fprintf('TASK27_3B_MATLAB_LIDAR_ANALYSIS_DONE\n');