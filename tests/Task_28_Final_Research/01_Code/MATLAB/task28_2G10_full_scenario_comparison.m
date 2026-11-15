% ============================================================
% GEMSTAR TASK 28.2G.10
% Full scenario comparison using validated Task 28 CSVs
% Four three-sensor candidates + separate Radar-only diagnostic
% ============================================================

clear;
clc;
close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';

task = fullfile(root, 'tests', ...
    'Task_28_Final_Research');

dataDir = fullfile(task, '02_CSV_Data');
plotDir = fullfile(task, '04_Plots', ...
    'Full_Scenario_Comparison');

if ~exist(plotDir, 'dir')
    mkdir(plotDir);
end

classificationFile = fullfile(dataDir, ...
    'task28_2G9B_dataset_classification.csv');

assert(isfile(classificationFile), ...
    'Task 28.2G.9B classification not found.');

C = readtable(classificationFile, ...
    'TextType', 'string');

scenarios = [
    "baseline_clear"
    "baseline_fog_working_radar"
    "fog_mor100"
    "fog_postfix_validation"
];

labels = {
    'Clear'
    'Fog + Radar'
    'Fog MOR 100'
    'Fog postfix'
};

nScenario = numel(scenarios);

frameCount = zeros(nScenario,1);
cameraBytesMean = zeros(nScenario,1);
lidarRaysMean = zeros(nScenario,1);
radarRaysMean = zeros(nScenario,1);

cameraRepeatPct = zeros(nScenario,1);
lidarRepeatPct = zeros(nScenario,1);
radarRepeatPct = zeros(nScenario,1);

dtMedian = zeros(nScenario,1);
dtP95 = zeros(nScenario,1);
dtP99 = zeros(nScenario,1);

allDt = cell(nScenario,1);

fprintf('\n==========================================\n');
fprintf('TASK 28.2G.10 - SCENARIO COMPARISON\n');
fprintf('==========================================\n');

for i = 1:nScenario

    scenario = scenarios(i);

    cRow = C(C.Scenario == scenario,:);

    assert(height(cRow) == 1, ...
        'Missing or duplicate classification: %s', scenario);

    assert(cRow.ThreeSensorComparisonEligible == 1, ...
        'Scenario is not three-sensor eligible: %s', scenario);

    inputFile = fullfile(dataDir, ...
        "task28_2G5_" + scenario + ...
        "_first1000000_frames.csv");

    assert(isfile(inputFile), ...
        'Missing recording CSV: %s', inputFile);

    T = readtable(inputFile);

    n = height(T);

    assert(n == cRow.Frames, ...
        'Frame count mismatch: %s', scenario);

    assert(all(T.CameraPresent == 1) && ...
           all(T.LiDARPresent == 1) && ...
           all(T.RadarPresent == 1), ...
        'Missing three-sensor payloads: %s', scenario);

    frameCount(i) = n;

    cameraBytesMean(i) = mean(T.CameraBytes);
    lidarRaysMean(i) = mean(T.LiDARRays);
    radarRaysMean(i) = mean(T.RadarRays);

    % Rates are fractions of all frames. The first frame has
    % no previous frame to compare with.
    cameraRepeatPct(i) = ...
        100 * sum(T.CameraPayloadRepeated == 1) / n;

    lidarRepeatPct(i) = ...
        100 * sum(T.LiDARPayloadRepeated == 1) / n;

    radarRepeatPct(i) = ...
        100 * sum(T.RadarPayloadRepeated == 1) / n;

    dt = T.DT_ms;
    dt = dt(isfinite(dt) & dt > 0);

    assert(~isempty(dt), ...
        'No valid frame intervals: %s', scenario);

    allDt{i} = dt;

    dtMedian(i) = median(dt);
    dtP95(i) = prctile(dt,95);
    dtP99(i) = prctile(dt,99);

    fprintf('\n%s\n', scenario);
    fprintf('Frames: %d\n', n);
    fprintf('LiDAR repeated: %.2f%%\n', ...
        lidarRepeatPct(i));
    fprintf('Radar repeated: %.2f%%\n', ...
        radarRepeatPct(i));
    fprintf('Median interval: %.3f ms\n', ...
        dtMedian(i));
    fprintf('P95 interval: %.3f ms\n', ...
        dtP95(i));
end

%% FIGURE 1 - Sensor payload repetition

f1 = figure('Color','w', ...
    'Name','Sensor Repetition Comparison', ...
    'Position',[100 100 1150 620]);

repeatData = [
    cameraRepeatPct, lidarRepeatPct, radarRepeatPct
];

bar(repeatData,'grouped');
grid on;

xticks(1:nScenario);
xticklabels(labels);

ylabel('Repeated payloads (% of frames)');
title('GEMSTAR - Full Recording Sensor Payload Repetition');

legend({'Camera','LiDAR','Radar'}, ...
    'Location','northwest');

ylim([0 max(50, ceil(max(repeatData(:))/10)*10)]);

%% FIGURE 2 - Raw input workload sizes

f2 = figure('Color','w', ...
    'Name','Raw Sensor Input Workload', ...
    'Position',[120 120 1150 750]);

tiledlayout(3,1);

nexttile;
bar(cameraBytesMean / 1e6);
grid on;
ylabel('MB/frame');
title('Mean Camera Image Payload');
xticks(1:nScenario);
xticklabels(labels);

nexttile;
bar(lidarRaysMean);
grid on;
ylabel('Reflections/frame');
title('Mean LiDAR Raw Reflection Count');
xticks(1:nScenario);
xticklabels(labels);

nexttile;
bar(radarRaysMean);
grid on;
ylabel('Reflections/frame');
title('Mean Radar Raw Reflection Count');
xticks(1:nScenario);
xticklabels(labels);

%% FIGURE 3 - Frame interval distributions

f3 = figure('Color','w', ...
    'Name','Frame Interval Distributions', ...
    'Position',[140 140 1150 750]);

tiledlayout(2,2);

for i = 1:nScenario
    nexttile;

    histogram(allDt{i},30);
    grid on;
    xlabel('Recorded frame interval (ms)');
    ylabel('Count');
    title(labels{i});
end

sgtitle('GEMSTAR - Recorded Inter-Frame Timing');

%% FIGURE 4 - Frame interval percentiles

f4 = figure('Color','w', ...
    'Name','Frame Timing Percentiles', ...
    'Position',[160 160 1150 620]);

timing = [dtMedian,dtP95,dtP99];

bar(timing,'grouped');
grid on;

xticks(1:nScenario);
xticklabels(labels);
ylabel('Inter-frame interval (ms)');
title('GEMSTAR - Frame Timing Percentiles');

legend({'Median','P95','P99'}, ...
    'Location','northwest');

%% FIGURE 5 - Radar-only diagnostic

radarScenario = "task05_fog_test";

radarRow = C(C.Scenario == radarScenario,:);

assert(height(radarRow) == 1 && ...
    radarRow.Classification == "RADAR_ONLY_DIAGNOSTIC", ...
    'Radar-only dataset classification mismatch.');

radarFile = fullfile(dataDir, ...
    "task28_2G5_" + radarScenario + ...
    "_first1000000_frames.csv");

assert(isfile(radarFile), ...
    'Radar-only diagnostic CSV missing.');

R = readtable(radarFile);

assert(height(R) == radarRow.Frames, ...
    'Radar-only frame count mismatch.');

assert(all(R.CameraPresent == 0) && ...
       all(R.LiDARPresent == 0) && ...
       all(R.RadarPresent == 1), ...
    'Radar-only recording does not match classification.');

f5 = figure('Color','w', ...
    'Name','Radar-Only Recording Diagnostic', ...
    'Position',[180 180 1150 650]);

tiledlayout(2,1);

nexttile;
stairs(R.Frame, R.RadarPayloadRepeated, ...
    'LineWidth',1.3);
grid on;
ylim([-0.1 1.1]);
yticks([0 1]);
xlabel('Frame');
ylabel('Repeated');
title('Radar-Only: Repeated Serialized Radar Views');

nexttile;
plot(R.Frame, R.RadarRays, ...
    'LineWidth',1.3);
grid on;
xlabel('Frame');
ylabel('Raw reflections');
title('Radar-Only: Raw Reflection Count');

sgtitle('Task 05 Fog Test - Diagnostic Only');

%% FIGURE SAVING

figs = {f1,f2,f3,f4,f5};

names = {
    'task28_2G10_sensor_repetition'
    'task28_2G10_raw_workload'
    'task28_2G10_timing_distributions'
    'task28_2G10_timing_percentiles'
    'task28_2G10_radar_only_diagnostic'
};

for k = 1:numel(figs)

    figFile = fullfile(plotDir, ...
        [names{k} '.fig']);

    pngFile = fullfile(plotDir, ...
        [names{k} '.png']);

    assert(~isfile(figFile) && ~isfile(pngFile), ...
        'Figure output already exists: %s', names{k});
end

for k = 1:numel(figs)

    savefig(figs{k}, ...
        fullfile(plotDir, [names{k} '.fig']));

    exportgraphics(figs{k}, ...
        fullfile(plotDir, [names{k} '.png']), ...
        'Resolution',300);
end

%% CONSOLIDATED NUMERICAL SUMMARY

Summary = table( ...
    scenarios, frameCount, ...
    cameraBytesMean, ...
    lidarRaysMean, radarRaysMean, ...
    cameraRepeatPct, lidarRepeatPct, radarRepeatPct, ...
    dtMedian,dtP95,dtP99, ...
    'VariableNames', { ...
    'Scenario','Frames', ...
    'MeanCameraBytes','MeanLiDARRays','MeanRadarRays', ...
    'CameraRepeatedPct','LiDARRepeatedPct','RadarRepeatedPct', ...
    'MedianDT_ms','P95DT_ms','P99DT_ms'});

summaryFile = fullfile(dataDir, ...
    'task28_2G10_three_sensor_comparison_summary.csv');

assert(~isfile(summaryFile), ...
    'Summary already exists; not overwriting.');

writetable(Summary,summaryFile);

disp(' ');
disp('=== THREE-SENSOR COMPARISON SUMMARY ===');
disp(Summary);

fprintf('\nRADAR-ONLY DIAGNOSTIC\n');
fprintf('Frames: %d\n',height(R));
fprintf('Repeated Radar views: %d\n', ...
    sum(R.RadarPayloadRepeated == 1));

fprintf('\n==========================================\n');
fprintf('TASK 28.2G.10 COMPLETE\n');
fprintf('==========================================\n');
fprintf('Figures: 5 PNG + 5 FIG saved\n');
fprintf('Summary CSV: %s\n',summaryFile);
fprintf('Plots folder: %s\n',plotDir);

fprintf('\nRESEARCH LIMITATIONS:\n');
fprintf('- Four scenarios are three-sensor candidates only.\n');
fprintf('- Task05 is Radar-only and analyzed separately.\n');
fprintf('- Raw reflection counts are not valid-return counts.\n');
fprintf('- Frame intervals are not execution latencies.\n');
fprintf('- Payload repetition is not acquisition freshness.\n');
fprintf('- Weather causality and energy savings are unproven.\n');
