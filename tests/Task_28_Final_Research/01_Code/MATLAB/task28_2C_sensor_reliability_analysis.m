% ============================================================
% GEMSTAR TASK 28.2C
% SENSOR RELIABILITY AND TIMING ANALYSIS
% ============================================================

clear;
clc;
close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';

inputFile = fullfile(root, 'tests', ...
    'Task_24_Final_Research', '02_CSV_Data', ...
    'task24_03_04_sensor_reliability_manifest.csv');

outputDir = fullfile(root, 'tests', ...
    'Task_28_Final_Research', '04_Plots', ...
    'Sensor_Reliability');

dataDir = fullfile(root, 'tests', ...
    'Task_28_Final_Research', '02_CSV_Data');

if ~exist(inputFile, 'file')
    error('Input CSV not found: %s', inputFile);
end

if ~exist(outputDir, 'dir')
    mkdir(outputDir);
end

if ~exist(dataDir, 'dir')
    mkdir(dataDir);
end

T = readtable(inputFile, 'TextType', 'string');

fprintf('\n=======================================\n');
fprintf('GEMSTAR TASK 28.2C\n');
fprintf('=======================================\n');
fprintf('Total rows: %d\n', height(T));

if height(T) ~= 372
    warning('Expected 372 rows, found %d.', height(T));
end

%% 1. Frame timing analysis

dt = double(T.DT_ms);
validDt = dt(isfinite(dt));

if isempty(validDt)
    error('No valid frame timing values were found.');
end

meanDt = mean(validDt);
medianDt = median(validDt);
p95Dt = prctile(validDt, 95);
p99Dt = prctile(validDt, 99);

fprintf('\nFRAME TIMING RESULTS\n');
fprintf('Mean:   %.4f ms\n', meanDt);
fprintf('Median: %.4f ms\n', medianDt);
fprintf('P95:    %.4f ms\n', p95Dt);
fprintf('P99:    %.4f ms\n', p99Dt);
fprintf('Min:    %.4f ms\n', min(validDt));
fprintf('Max:    %.4f ms\n', max(validDt));

fig1 = figure('Color','w','Name','Frame Timing');

plot(T.Frame, dt, 'LineWidth', 1.2);
hold on;
yline(medianDt, '--', 'Median');
yline(p95Dt, '--', 'P95');

grid on;
xlabel('Frame Number');
ylabel('Inter-frame Interval (ms)');
title('Task 28.2C - GEMSTAR Frame Timing');

savefig(fig1, fullfile(outputDir, ...
    'task28_2C_frame_timing.fig'));

exportgraphics(fig1, fullfile(outputDir, ...
    'task28_2C_frame_timing.png'), ...
    'Resolution',300);

%% 2. Sensor payload freshness

sensorVars = {
    'CameraPayloadFreshness'
    'LiDARPayloadFreshness'
    'RadarPayloadFreshness'
};

fig2 = figure('Color','w', ...
    'Name','Sensor Payload Freshness');

tiledlayout(3,1);

for k = 1:numel(sensorVars)

    nexttile;

    values = categorical( ...
        string(T.(sensorVars{k})));

    counts = countcats(values);
    labels = categories(values);

    bar(counts);
    grid on;

    xticks(1:numel(labels));
    xticklabels(labels);
    xtickangle(25);

    ylabel('Frame Count');
    title(sensorVars{k}, 'Interpreter','none');

    fprintf('\n%s\n', sensorVars{k});

    for j = 1:numel(labels)
        fprintf('%s: %d\n', labels{j}, counts(j));
    end
end

savefig(fig2, fullfile(outputDir, ...
    'task28_2C_payload_freshness.fig'));

exportgraphics(fig2, fullfile(outputDir, ...
    'task28_2C_payload_freshness.png'), ...
    'Resolution',300);

%% 3. Radar review flags

flags = categorical( ...
    string(T.RadarDopplerReviewFlag));

radarCounts = countcats(flags);
radarLabels = categories(flags);

fig3 = figure('Color','w', ...
    'Name','Radar Review Flags');

bar(radarCounts);
grid on;

xticks(1:numel(radarLabels));
xticklabels(radarLabels);
xtickangle(25);

ylabel('Frame Count');
title('Task 28.2C - Radar Doppler Review Flags');

fprintf('\nRADAR FLAGS\n');

for k = 1:numel(radarLabels)
    fprintf('%s: %d\n', radarLabels{k}, radarCounts(k));
end

savefig(fig3, fullfile(outputDir, ...
    'task28_2C_radar_review_flags.fig'));

exportgraphics(fig3, fullfile(outputDir, ...
    'task28_2C_radar_review_flags.png'), ...
    'Resolution',300);

%% 4. Sensor presence

presence = [
    sum(T.CameraPresent == 1)
    sum(T.LiDARPresent == 1)
    sum(T.RadarPresent == 1)
];

fig4 = figure('Color','w', ...
    'Name','Sensor Presence');

bar(presence);
grid on;

xticks(1:3);
xticklabels({'Camera','LiDAR','Radar'});

ylabel('Frame Count');
title('Task 28.2C - Sensor Presence');

fprintf('\nSENSOR PRESENCE\n');
fprintf('Camera: %d/%d\n', presence(1),height(T));
fprintf('LiDAR:  %d/%d\n', presence(2),height(T));
fprintf('Radar:  %d/%d\n', presence(3),height(T));

savefig(fig4, fullfile(outputDir, ...
    'task28_2C_sensor_presence.fig'));

exportgraphics(fig4, fullfile(outputDir, ...
    'task28_2C_sensor_presence.png'), ...
    'Resolution',300);

%% 5. Save timing statistics CSV

metric = [
    "Mean_DT_ms"
    "Median_DT_ms"
    "P95_DT_ms"
    "P99_DT_ms"
    "Min_DT_ms"
    "Max_DT_ms"
];

value = [
    meanDt
    medianDt
    p95Dt
    p99Dt
    min(validDt)
    max(validDt)
];

resultTable = table(metric,value);

writetable(resultTable, fullfile(dataDir, ...
    'task28_2C_timing_statistics.csv'));

%% 6. Final output

fprintf('\n=======================================\n');
fprintf('TASK 28.2C ANALYSIS COMPLETED\n');
fprintf('=======================================\n');
fprintf('Figures saved in:\n%s\n',outputDir);
fprintf('Statistics CSV saved in:\n%s\n',dataDir);
fprintf('Four figures remain open in MATLAB.\n');

