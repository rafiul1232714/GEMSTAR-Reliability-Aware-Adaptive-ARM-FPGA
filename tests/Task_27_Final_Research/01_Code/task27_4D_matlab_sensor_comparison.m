%% GEMSTAR TASK 27.4D
% Camera, Radar and YOLO workload visualization.
% Archived CPU measurements + calculated nominal data sizes.
% No hardware energy or memory traffic measured.

clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_27_Final_Research';
csvDir = fullfile(root,'02_CSV_Data');
plotDir = fullfile(root,'04_Plots');
reportDir = fullfile(root,'06_Research_Findings');

fprintf('=== TASK 27.4D MATLAB SENSOR COMPARISON ===\n');

%% Load characterized measurements

% Explicit CSV import types.
% The scenario column mixes weather text and Radar numeric IDs.
csvPath = fullfile(csvDir, ...
    'task27_4C_sensor_compute_characterization.csv');

opts = detectImportOptions(csvPath, ...
    'VariableNamingRule','preserve');

opts = setvartype(opts, ...
    {'workload','scenario','mode'}, 'string');

T = readtable(csvPath, opts);

assert(~any(ismissing(T.workload)), ...
    'Missing workload names after CSV import');

assert(~any(ismissing(T.scenario)), ...
    'Missing scenario names after CSV import');

assert(~any(ismissing(T.mode)), ...
    'Missing mode names after CSV import');

fprintf('CSV_TEXT_COLUMNS_IMPORTED: PASS\n');
assert(height(T)==23,'Expected 23 records');

C = T(string(T.workload)=="Camera",:);
R = T(string(T.workload)=="Radar",:);
Y = T(string(T.workload)=="YOLO11s",:);

assert(height(C)==6,'Camera record mismatch');
assert(height(R)==12,'Radar record mismatch');
assert(height(Y)==5,'YOLO record mismatch');

assert(all(double(T.archived_cpu_median_ms)>0), ...
    'Invalid CPU timing');

names = {
    'Task27_Fig17_Camera_Weather_Latency'
    'Task27_Fig18_Camera_Buffer_vs_Latency'
    'Task27_Fig19_Radar_Batch_Workload'
    'Task27_Fig20_YOLO_CPU_Latency'
};

summaryPath = fullfile(csvDir, ...
    'task27_4D_matlab_sensor_summary.csv');

reportPath = fullfile(reportDir, ...
    'task27_4D_matlab_sensor_findings.txt');

% Preserve all existing research output files.
assert(~isfile(summaryPath),'Summary already exists');
assert(~isfile(reportPath),'Report already exists');

for k = 1:numel(names)
    assert(~isfile(fullfile(plotDir,[names{k} '.png'])), ...
        'PNG already exists');
    assert(~isfile(fullfile(plotDir,[names{k} '.fig'])), ...
        'FIG already exists');
end

disp('=== CAMERA DATASET COMBINATIONS ===');
disp(C(:, {'scenario','mode','archived_cpu_median_ms'}));
%% Figure 17 — Camera weather and processing mode

weather = ["CLEAR";"FOG100";"FOG20"];
modes = ["FULL","ROI"];

cameraMs = nan(3,2);
cameraBytes = nan(3,2);
matchCounts = zeros(3,2);

fprintf('\n=== VERIFIED CAMERA ROW MATCHING ===\n');

for k = 1:height(C)

    currentWeather = upper(strtrim(char(string(C.scenario(k)))));
    currentMode = upper(strtrim(char(string(C.mode(k)))));

    i = find(strcmp(cellstr(weather), currentWeather), 1);
    j = find(strcmp(cellstr(modes), currentMode), 1);

    if isempty(i) || isempty(j)
        error('Unknown Camera row: weather=%s mode=%s', ...
            currentWeather,currentMode);
    end

    matchCounts(i,j) = matchCounts(i,j) + 1;

    cameraMs(i,j) = double(C.archived_cpu_median_ms(k));

    cameraBytes(i,j) = double( ...
        C.nominal_intermediate_buffer_sum_bytes(k));

    fprintf('%s / %s : %.6f ms\n', ...
        currentWeather,currentMode,cameraMs(i,j));
end

assert(all(matchCounts(:)==1), ...
    'Camera combination duplicated or missing');

assert(all(isfinite(cameraMs(:))), ...
    'Invalid Camera timing values');

fprintf('CAMERA_COMBINATIONS_VALIDATED: 6\n');
f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1100 550]);

bar(categorical(cellstr(weather)),cameraMs);

xlabel('Weather Scenario');
ylabel('Archived CPU Median Time (ms)');
title('Camera Preprocessing: FULL and ROI');
legend('FULL','ROI','Location','best');
grid on;

savefig(f,fullfile(plotDir,[names{1} '.fig']));
exportgraphics(f,fullfile(plotDir,[names{1} '.png']), ...
    'Resolution',300);
close(f);

%% Figure 18 — Camera nominal buffers versus latency

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1100 550]);

hold on;

for j = 1:2
    scatter(cameraBytes(:,j)/1048576, ...
        cameraMs(:,j),100,'filled', ...
        'DisplayName',char(modes(j)));
end

xlabel('Nominal Camera Buffer Sum (MiB)');
ylabel('Archived CPU Median Time (ms)');
title('Camera Nominal Buffers vs Processing Time');
legend('Location','best');
grid on;

savefig(f,fullfile(plotDir,[names{2} '.fig']));
exportgraphics(f,fullfile(plotDir,[names{2} '.png']), ...
    'Resolution',300);
close(f);

%% Figure 19 — Radar return-batch workload

radarReturns = double(R.processing_items);
radarMs = double(R.archived_cpu_median_ms);

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1100 550]);

scatter(radarReturns,radarMs,90,'filled');

xlabel('Valid Radar Returns per Batch');
ylabel('Archived CPU Median Batch Time (ms)');
title('Radar Processing Time vs Return Count');
grid on;

savefig(f,fullfile(plotDir,[names{3} '.fig']));
exportgraphics(f,fullfile(plotDir,[names{3} '.png']), ...
    'Resolution',300);
close(f);

%% Figure 20 — YOLO median and p99

[frame,order] = sort(double(Y.frame));
Y = Y(order,:);

yoloMedian = double(Y.archived_cpu_median_ms);
yoloP99 = double(Y.archived_cpu_p99_ms);

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1100 550]);

bar(categorical(string(frame)), ...
    [yoloMedian yoloP99]);

xlabel('Recorded Frame ID');
ylabel('Archived CPU Predict Time (ms)');
title('YOLO11s CPU Prediction: Median and p99');
legend('Median','p99','Location','best');
grid on;

savefig(f,fullfile(plotDir,[names{4} '.fig']));
exportgraphics(f,fullfile(plotDir,[names{4} '.png']), ...
    'Resolution',300);
close(f);

%% Numerical summary

workloads = ["Camera";"Radar";"YOLO11s"];
groups = [height(C);height(R);height(Y)];

medianOfGroupMediansMs = [
    median(double(C.archived_cpu_median_ms))
    median(radarMs)
    median(yoloMedian)
];

maxGroupP99Ms = [
    max(double(C.archived_cpu_p99_ms))
    max(double(R.archived_cpu_p99_ms))
    max(yoloP99)
];

S = table(workloads,groups,medianOfGroupMediansMs, ...
    maxGroupP99Ms, ...
    'VariableNames', ...
    {'Workload','Groups','MedianOfGroupMediansMs', ...
    'MaximumGroupP99Ms'});

writetable(S,summaryPath);

%% Research findings

fid = fopen(reportPath,'w');
assert(fid>0,'Cannot write findings');

fprintf(fid,'GEMSTAR TASK 27.4D\n');
fprintf(fid,'Camera, Radar and YOLO Characterization\n');
fprintf(fid,'======================================\n\n');

fprintf(fid,'Camera configurations: %d\n',height(C));
fprintf(fid,'Radar batches: %d\n',height(R));
fprintf(fid,'YOLO frames: %d\n\n',height(Y));

fprintf(fid,'CAMERA MEDIANS (ms):\n');
for i = 1:3
    fprintf(fid,'%s FULL=%.6f ROI=%.6f\n', ...
        char(weather(i)),cameraMs(i,1),cameraMs(i,2));
end

fprintf(fid,'\nRADAR:\n');
fprintf(fid,'Valid benchmark returns: %d\n',sum(radarReturns));
fprintf(fid,'Median of batch medians: %.6f ms\n',median(radarMs));

fprintf(fid,'\nYOLO:\n');
fprintf(fid,'Median of frame medians: %.6f ms\n',median(yoloMedian));
fprintf(fid,'Max group p99: %.6f ms\n',max(yoloP99));

fprintf(fid,'\nLIMITATIONS:\n');
fprintf(fid,'CPU processing scopes differ across workloads.\n');
fprintf(fid,'Camera nominal buffers do not measure RAM traffic.\n');
fprintf(fid,'ROI processes fewer pixels but may exclude objects.\n');
fprintf(fid,'Radar benchmark processes valid returns only.\n');
fprintf(fid,'YOLO model load and disk input excluded from timing.\n');
fprintf(fid,'YOLO accuracy is not validated by these measurements.\n');
fprintf(fid,'No FPGA execution or board energy measurements.\n');
fprintf(fid,'No cross-sensor speedup or energy benefit established.\n');

fclose(fid);

%% Completion

fprintf('CAMERA_CONFIGURATIONS: %d\n',height(C));
fprintf('RADAR_BATCHES: %d\n',height(R));
fprintf('YOLO_FRAMES: %d\n',height(Y));
fprintf('TOTAL_RECORDS: %d\n',height(T));
fprintf('FIGURES_CREATED: 4 PNG + 4 FIG\n');
fprintf('SUMMARY_CSV_CREATED: YES\n');
fprintf('FINDINGS_CREATED: YES\n');
fprintf('HARDWARE_ENERGY_MEASURED: NO\n');
fprintf('TASK27_4D_MATLAB_SENSOR_COMPARISON_DONE\n');