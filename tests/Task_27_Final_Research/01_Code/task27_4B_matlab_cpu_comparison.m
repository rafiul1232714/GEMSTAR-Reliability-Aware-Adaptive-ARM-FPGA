%% GEMSTAR TASK 27.4B
% MATLAB analysis of six archived CPU workloads.
% Different processing scopes are NOT equivalent frame times.

clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_27_Final_Research';
csvDir = fullfile(root,'02_CSV_Data');
plotDir = fullfile(root,'04_Plots');
findDir = fullfile(root,'06_Research_Findings');

fprintf('=== TASK 27.4B MATLAB CPU WORKLOAD COMPARISON ===\n');

%% 1. Load research data

S = readtable(fullfile(csvDir, ...
    'task27_4A_cpu_workload_summary.csv'), ...
    'VariableNamingRule','preserve');

G = readtable(fullfile(csvDir, ...
    'task27_4A_cpu_workload_groups.csv'), ...
    'VariableNamingRule','preserve');

L = readtable(fullfile(csvDir, ...
    'task27_3A_lidar_workload_metrics.csv'), ...
    'VariableNamingRule','preserve');

assert(height(S)==6,'Expected six workloads');
assert(height(G)==184,'Expected 184 timing groups');
assert(height(L)==53,'Expected 53 LiDAR frames');
assert(sum(S.timing_rows)==6025,'Timing row mismatch');
assert(sum(G.measurements)==6025,'Group count mismatch');

workloads = [
    "EKF"
    "Camera"
    "LiDAR"
    "Radar"
    "YOLO11s"
    "Partial_LiDAR_Radar"
];

shortNames = {
    'EKF replay'
    'Camera'
    'LiDAR stages'
    'Radar batches'
    'YOLO11s'
    'Partial LiDAR/Radar'
};

med = zeros(6,1);
groupCount = zeros(6,1);

for k = 1:6
    mask = string(S.workload)==workloads(k);
    assert(nnz(mask)==1,'Missing or duplicate workload');

    med(k) = double( ...
        S.median_of_group_medians_ms(mask));

    groupCount(k) = double(S.groups(mask));
end

assert(isequal(groupCount,[2;6;106;12;5;53]), ...
    'Unexpected workload group counts');

%% 2. Preserve existing outputs

names = {
    'Task27_Fig13_CPU_Workload_Overview'
    'Task27_Fig14_CPU_Group_Median_Distribution'
    'Task27_Fig15_Camera_Weather_Timing'
    'Task27_Fig16_LiDAR_Filter_Cluster_Timing'
};

for k = 1:numel(names)
    assert(~isfile(fullfile(plotDir,[names{k} '.png'])), ...
        'Existing PNG preserved');
    assert(~isfile(fullfile(plotDir,[names{k} '.fig'])), ...
        'Existing FIG preserved');
end

summaryPath = fullfile(csvDir, ...
    'task27_4B_matlab_cpu_visual_summary.csv');

reportPath = fullfile(findDir, ...
    'task27_4B_matlab_cpu_findings.txt');

assert(~isfile(summaryPath),'Existing summary preserved');
assert(~isfile(reportPath),'Existing findings preserved');

%% 3. Figure 13 — Six-workload timing overview

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1200 620]);

bar(1:6,med);
set(gca,'YScale','log');
xticks(1:6);
xticklabels(shortNames);
xtickangle(22);

ylabel('Median of Group Medians (ms, log scale)');
title('Task 27: Archived CPU Workload Timing Overview');
subtitle('Different timing scopes; not equivalent frame latencies');
grid on;

savefig(f,fullfile(plotDir,[names{1} '.fig']));
exportgraphics(f,fullfile(plotDir,[names{1} '.png']), ...
    'Resolution',300);
close(f);

%% 4. Figure 14 — Distribution of group medians

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1200 620]);

hold on;

for k = 1:6
    mask = string(G.workload)==workloads(k);
    values = double(G.median_ms(mask));

    assert(numel(values)==groupCount(k), ...
        'Group distribution mismatch');

    % Deterministic spread solely for plotting visibility.
    x = k + linspace(-0.20,0.20,numel(values))';

    scatter(x,values,26,'filled');
    plot(k,median(values),'kd', ...
        'MarkerSize',9,'MarkerFaceColor','k');
end

set(gca,'YScale','log');
xlim([0.5 6.5]);
xticks(1:6);
xticklabels(shortNames);
xtickangle(22);

ylabel('Per-Group Median Time (ms, log scale)');
title('Task 27: CPU Timing Variation Across Input Groups');
subtitle('Each dot represents one benchmark group');
grid on;

savefig(f,fullfile(plotDir,[names{2} '.fig']));
exportgraphics(f,fullfile(plotDir,[names{2} '.png']), ...
    'Resolution',300);
close(f);

%% 5. Figure 15 — Camera weather and ROI timing

weather = ["CLEAR";"FOG100";"FOG20"];
modes = ["FULL","ROI"];
cameraTimes = nan(3,2);

camRows = G(string(G.workload)=="Camera",:);
assert(height(camRows)==6,'Expected six Camera groups');

for i = 1:3
    for j = 1:2
        label = "weather=" + weather(i) + ...
            "|mode=" + modes(j);

        mask = string(camRows.group)==label;
        assert(nnz(mask)==1, ...
            "Missing Camera timing group: " + label);

        cameraTimes(i,j) = double( ...
            camRows.median_ms(mask));
    end
end

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1100 570]);

bar(categorical(cellstr(weather)),cameraTimes);

xlabel('Recorded Weather Configuration');
ylabel('Archived CPU Median Preprocessing Time (ms)');
title('Camera CPU Preprocessing: FULL vs ROI');
legend('FULL','ROI','Location','best');
grid on;

savefig(f,fullfile(plotDir,[names{3} '.fig']));
exportgraphics(f,fullfile(plotDir,[names{3} '.png']), ...
    'Resolution',300);
close(f);

%% 6. Figure 16 — LiDAR filtering and clustering

[frame,idx] = sort(double(L.frame));
L = L(idx,:);

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1150 570]);

plot(frame,double(L.median_filter_ms), ...
    '-o','LineWidth',1.4);
hold on;

plot(frame,double(L.median_cluster_ms), ...
    '-s','LineWidth',1.4);

xlabel('Recorded Frame ID');
ylabel('Archived CPU Stage Median (ms)');
title('LiDAR Filtering and Clustering: 53 Frames');
legend('Filtering','Clustering','Location','best');
grid on;

savefig(f,fullfile(plotDir,[names{4} '.fig']));
exportgraphics(f,fullfile(plotDir,[names{4} '.png']), ...
    'Resolution',300);
close(f);

%% 7. Save analysis summary

Output = table(workloads,groupCount,med, ...
    'VariableNames', { ...
    'Workload','Groups','MedianOfGroupMediansMs'});

writetable(Output,summaryPath);

%% 8. Save research findings

fid = fopen(reportPath,'w');
assert(fid>0,'Could not create findings report');

fprintf(fid,'GEMSTAR TASK 27.4B MATLAB CPU COMPARISON\n');
fprintf(fid,'========================================\n\n');

fprintf(fid,'Workloads: %d\n',height(S));
fprintf(fid,'Timing observations: %d\n',sum(S.timing_rows));
fprintf(fid,'Benchmark groups: %d\n\n',height(G));

for k = 1:6
    fprintf(fid,'%s: %d groups, %.6f ms median of medians\n', ...
        workloads(k),groupCount(k),med(k));
end

fprintf(fid,'\nCAMERA MEDIANS IN ms:\n');

for i = 1:3
    fprintf(fid,'%s FULL=%.6f ROI=%.6f\n', ...
        weather(i),cameraTimes(i,1),cameraTimes(i,2));
end

fprintf(fid,'\nLIDAR STAGE MEDIANS:\n');
fprintf(fid,'Filtering: %.6f ms\n', ...
    median(L.median_filter_ms));
fprintf(fid,'Clustering: %.6f ms\n', ...
    median(L.median_cluster_ms));

fprintf(fid,'\nLIMITATIONS:\n');
fprintf(fid,'Benchmark groups have different input sizes and scopes.\n');
fprintf(fid,'EKF time is a multi-observation replay.\n');
fprintf(fid,'Radar time is per batch, not per return.\n');
fprintf(fid,'LiDAR times are individual stages.\n');
fprintf(fid,'YOLO timing does not establish detection accuracy.\n');
fprintf(fid,'Camera weather timing does not prove sensor reliability.\n');
fprintf(fid,'Partial integrated timing excludes Camera and EKF.\n');
fprintf(fid,'No full three-sensor real-time validation.\n');
fprintf(fid,'No measured ARM-FPGA energy or speedup.\n');
fprintf(fid,'No hardware accelerator has been selected.\n');

fclose(fid);

%% 9. Completion status

fprintf('WORKLOADS_ANALYZED: %d\n',height(S));
fprintf('TIMING_ROWS: %d\n',sum(S.timing_rows));
fprintf('WORKLOAD_GROUPS: %d\n',height(G));
fprintf('CAMERA_WEATHER_GROUPS: %d\n',height(camRows));
fprintf('LIDAR_FRAMES: %d\n',height(L));
fprintf('FIGURES_CREATED: 4 PNG + 4 FIG\n');
fprintf('SUMMARY_CSV_CREATED: YES\n');
fprintf('FINDINGS_CREATED: YES\n');
fprintf('HARDWARE_ENERGY_MEASURED: NO\n');
fprintf('TASK27_4B_MATLAB_CPU_COMPARISON_DONE\n');