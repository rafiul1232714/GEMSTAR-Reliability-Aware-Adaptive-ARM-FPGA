%% ============================================================
% GEMSTAR Task 28.3D.6A
% Camera FULL vs ROI: Research Statistical Analysis
% Four scenarios, 20 paired images, 200 YOLO timing observations
% ============================================================

clearvars;
close all;
clc;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';
task = fullfile(root, 'tests', 'Task_28_Final_Research');

dataDir = fullfile(task, '02_CSV_Data');
plotDir = fullfile(task, '04_Plots', ...
    'Camera_FULL_ROI_Analysis');
findDir = fullfile(task, '06_Research_Findings');

if ~isfolder(plotDir)
    mkdir(plotDir);
end

frameFile = fullfile(dataDir, ...
    'task28_3D5A_full_roi_frame_comparison.csv');

scenarioFile = fullfile(dataDir, ...
    'task28_3D5A_full_roi_scenario_summary.csv');

timingFile = fullfile(dataDir, ...
    'task28_3D5A_full_roi_timing.csv');

outCSV = fullfile(dataDir, ...
    'task28_3D6A_camera_full_roi_statistics.csv');

outReport = fullfile(findDir, ...
    'task28_3D6A_camera_research_findings.txt');

assert(isfile(frameFile), 'Frame comparison CSV missing');
assert(isfile(scenarioFile), 'Scenario CSV missing');
assert(isfile(timingFile), 'Timing CSV missing');

assert(~isfile(outCSV), 'Statistics CSV already exists');
assert(~isfile(outReport), 'Findings report already exists');

prefixes = {
    'task28_3D6A_scenario_latency'
    'task28_3D6A_detection_comparison'
    'task28_3D6A_paired_latency'
    'task28_3D6A_per_image_delta'
};

for k = 1:numel(prefixes)
    assert(~isfile(fullfile(plotDir, ...
        [prefixes{k} '.png'])), 'PNG already exists');
    assert(~isfile(fullfile(plotDir, ...
        [prefixes{k} '.fig'])), 'FIG already exists');
end

frames = readtable(frameFile, ...
    'VariableNamingRule', 'preserve');

scenarios = readtable(scenarioFile, ...
    'VariableNamingRule', 'preserve');

timings = readtable(timingFile, ...
    'VariableNamingRule', 'preserve');

assert(height(frames) == 20, ...
    'Expected 20 paired image records');

assert(height(timings) == 200, ...
    'Expected 200 timing observations');

assert(height(scenarios) == 4, ...
    'Expected four scenario summaries');

scenarioNames = {
    'baseline_clear'
    'baseline_fog_working_radar'
    'fog_mor100'
    'fog_postfix_validation'
};

shortNames = {
    'Clear'
    'Fog + Radar'
    'Fog MOR 100'
    'Fog postfix'
};

frameScenario = string(frames.Scenario);
summaryScenario = string(scenarios.Scenario);
timingScenario = string(timings.Scenario);
timingMode = string(timings.Mode);

assert(all(ismember(frameScenario, string(scenarioNames))), ...
    'Unexpected scenario in frame data');

assert(all(ismember(timingScenario, string(scenarioNames))), ...
    'Unexpected scenario in timing data');

assert(all(ismember(timingMode, ["FULL", "ROI"])), ...
    'Unexpected YOLO mode');

assert(all(isfinite(frames.FullMedian_ms)) && ...
    all(isfinite(frames.ROIMedian_ms)), ...
    'Nonfinite frame latency values');

assert(all(timings.Elapsed_ms > 0) && ...
    all(isfinite(timings.Elapsed_ms)), ...
    'Invalid timing observations');

% ------------------------------------------------------------
% Build scenario-level statistics.
% ------------------------------------------------------------

results = table;

for k = 1:4
    scenario = string(scenarioNames{k});

    f = frames(frameScenario == scenario, :);

    assert(height(f) == 5, ...
        'Expected exactly five paired frames per scenario');

    a = timings(timingScenario == scenario & ...
        timingMode == "FULL", :);

    b = timings(timingScenario == scenario & ...
        timingMode == "ROI", :);

    assert(height(a) == 25 && height(b) == 25, ...
        'Expected 25 timings per mode per scenario');

    delta = f.ROIMedian_ms - f.FullMedian_ms;

    row = table( ...
        scenario, ...
        height(f), ...
        sum(f.FullDetections), ...
        sum(f.ROIDetections), ...
        sum(f.FullBoxesFullyInsideROI), ...
        sum(f.MatchedFullInsideROI), ...
        mean(f.FullMedian_ms), ...
        mean(f.ROIMedian_ms), ...
        median(delta), ...
        mean(delta), ...
        sum(delta < 0), ...
        sum(delta > 0), ...
        median(a.Elapsed_ms), ...
        median(b.Elapsed_ms), ...
        'VariableNames', { ...
        'Scenario', ...
        'Images', ...
        'FullDetections', ...
        'ROIDetections', ...
        'FullBoxesInsideROI', ...
        'MatchedFullInsideROI', ...
        'MeanFullImageMedian_ms', ...
        'MeanROIImageMedian_ms', ...
        'MedianPairedDelta_ms', ...
        'MeanPairedDelta_ms', ...
        'ImagesROIFaster', ...
        'ImagesROISlower', ...
        'PooledFullMedian_ms', ...
        'PooledROIMedian_ms' ...
        });

    results = [results; row]; %#ok<AGROW>
end

% ------------------------------------------------------------
% Figure 1: Scenario latency.
% ------------------------------------------------------------

f1 = figure('Visible', 'off', ...
    'Position', [100 100 1100 650]);

latency = [ ...
    results.MeanFullImageMedian_ms, ...
    results.MeanROIImageMedian_ms ...
];

bar(latency, 'grouped');
grid on;

set(gca, 'XTick', 1:4, ...
    'XTickLabel', shortNames);

ylabel('Mean of image median CPU latency (ms)');
title('Camera YOLO: FULL versus ROI processing');
legend({'FULL', 'ROI'}, 'Location', 'best');

ylim([0, max(latency(:))*1.2]);

savefig(f1, fullfile(plotDir, [prefixes{1} '.fig']));
saveas(f1, fullfile(plotDir, [prefixes{1} '.png']));
close(f1);

% ------------------------------------------------------------
% Figure 2: Detection comparison.
% ------------------------------------------------------------

f2 = figure('Visible', 'off', ...
    'Position', [100 100 1100 650]);

detections = [ ...
    results.FullDetections, ...
    results.ROIDetections, ...
    results.MatchedFullInsideROI ...
];

bar(detections, 'grouped');
grid on;

set(gca, 'XTick', 1:4, ...
    'XTickLabel', shortNames);

ylabel('Number of YOLO detection boxes');
title('Camera YOLO detection consistency: FULL vs ROI');

legend( ...
    {'FULL boxes', 'ROI boxes', 'Matched inside ROI'}, ...
    'Location', 'best');

savefig(f2, fullfile(plotDir, [prefixes{2} '.fig']));
saveas(f2, fullfile(plotDir, [prefixes{2} '.png']));
close(f2);

% ------------------------------------------------------------
% Figure 3: Paired image latency.
% ------------------------------------------------------------

f3 = figure('Visible', 'off', ...
    'Position', [100 100 900 700]);

hold on;

for k = 1:4
    mask = frameScenario == string(scenarioNames{k});

    scatter( ...
        frames.FullMedian_ms(mask), ...
        frames.ROIMedian_ms(mask), ...
        65, 'filled', ...
        'DisplayName', shortNames{k});
end

allLatency = [ ...
    frames.FullMedian_ms; frames.ROIMedian_ms ...
];

lower = min(allLatency) - 1;
upper = max(allLatency) + 1;

plot([lower upper], [lower upper], ...
    'k--', 'LineWidth', 1.2, ...
    'DisplayName', 'Equal latency');

xlim([lower upper]);
ylim([lower upper]);

axis square;
grid on;

xlabel('FULL image median latency (ms)');
ylabel('ROI image median latency (ms)');
title('Paired YOLO latency for the same Camera frames');
legend('Location', 'bestoutside');

savefig(f3, fullfile(plotDir, [prefixes{3} '.fig']));
saveas(f3, fullfile(plotDir, [prefixes{3} '.png']));
close(f3);

% ------------------------------------------------------------
% Figure 4: Per-frame paired latency difference.
% Positive values mean ROI is slower.
% ------------------------------------------------------------

f4 = figure('Visible', 'off', ...
    'Position', [100 100 1150 650]);

delta = frames.ROIMedian_ms - frames.FullMedian_ms;

bar(1:height(frames), delta);
hold on;
yline(0, 'k--', 'Equal latency');

grid on;

xlabel('Paired Camera image index');
ylabel('ROI minus FULL latency (ms)');
title('Paired YOLO latency difference by Camera image');

xticks(1:20);
xlim([0.5 20.5]);

savefig(f4, fullfile(plotDir, [prefixes{4} '.fig']));
saveas(f4, fullfile(plotDir, [prefixes{4} '.png']));
close(f4);

% ------------------------------------------------------------
% Write summary CSV.
% ------------------------------------------------------------

writetable(results, outCSV);

% ------------------------------------------------------------
% Consolidated numerical findings.
% ------------------------------------------------------------

fullBoxes = sum(results.FullDetections);
roiBoxes = sum(results.ROIDetections);

insideBoxes = sum(results.FullBoxesInsideROI);
matchedBoxes = sum(results.MatchedFullInsideROI);

overallFull = mean(frames.FullMedian_ms);
overallROI = mean(frames.ROIMedian_ms);

allDelta = frames.ROIMedian_ms - frames.FullMedian_ms;

fid = fopen(outReport, 'w');

assert(fid > 0, 'Cannot create findings report');

fprintf(fid, ...
    'GEMSTAR TASK 28.3D.6A CAMERA RESEARCH FINDINGS\n');
fprintf(fid, ...
    '=============================================\n\n');

fprintf(fid, 'Images compared: %d\n', height(frames));
fprintf(fid, 'YOLO timing observations: %d\n', height(timings));

fprintf(fid, 'FULL detections: %d\n', fullBoxes);
fprintf(fid, 'ROI detections: %d\n', roiBoxes);
fprintf(fid, 'FULL boxes completely in ROI: %d\n', insideBoxes);
fprintf(fid, 'Matched inside-ROI boxes: %d\n\n', matchedBoxes);

fprintf(fid, ...
    'Mean FULL per-image median latency: %.5f ms\n', ...
    overallFull);

fprintf(fid, ...
    'Mean ROI per-image median latency: %.5f ms\n', ...
    overallROI);

fprintf(fid, ...
    'Mean paired ROI-FULL difference: %.5f ms\n', ...
    mean(allDelta));

fprintf(fid, ...
    'Median paired ROI-FULL difference: %.5f ms\n', ...
    median(allDelta));

fprintf(fid, ...
    'ROI faster on %d/20 images\n', sum(allDelta < 0));

fprintf(fid, ...
    'ROI slower on %d/20 images\n\n', sum(allDelta > 0));

fprintf(fid, 'RESEARCH INTERPRETATION\n');
fprintf(fid, ...
    '- ROI source area is 36 percent of full pixels.\n');
fprintf(fid, ...
    '- YOLO requested inference size remained 640.\n');
fprintf(fid, ...
    '- Reduced input area did not guarantee lower YOLO latency.\n');
fprintf(fid, ...
    '- FULL and ROI produce different detection sets.\n');
fprintf(fid, ...
    '- ROI matching is detector consistency, not accuracy.\n');
fprintf(fid, ...
    '- ROI preprocessing and YOLO inference are distinct costs.\n\n');

fprintf(fid, 'LIMITATIONS\n');
fprintf(fid, ...
    '- Only 20 images, five per recording.\n');
fprintf(fid, ...
    '- Scenario images are not proven matched scenes.\n');
fprintf(fid, ...
    '- CPU benchmark is not KR260 hardware timing.\n');
fprintf(fid, ...
    '- No measured energy or independent object accuracy.\n');
fprintf(fid, ...
    '- RGB convention follows Task 24; source not verified.\n');
fprintf(fid, ...
    '- Repeat timing observations are not independent images.\n');
fprintf(fid, ...
    '- No power or energy saving has been established.\n\n');

fprintf(fid, ...
    'STATUS: TASK 28.3D.6A COMPLETE\n');

fclose(fid);

% ------------------------------------------------------------
% Print final research results.
% ------------------------------------------------------------

disp(' ');
disp('========================================');
disp('TASK 28.3D.6A - MATLAB CAMERA RESULTS');
disp('========================================');

disp(results);

fprintf('\nTOTAL FULL BOXES: %d\n', fullBoxes);
fprintf('TOTAL ROI BOXES: %d\n', roiBoxes);
fprintf('MATCHED BOXES: %d/%d\n', matchedBoxes, insideBoxes);

fprintf('MEAN FULL LATENCY: %.4f ms\n', overallFull);
fprintf('MEAN ROI LATENCY: %.4f ms\n', overallROI);
fprintf('MEAN PAIRED DELTA: %.4f ms\n', mean(allDelta));

fprintf('ROI FASTER IMAGES: %d/20\n', sum(allDelta < 0));
fprintf('ROI SLOWER IMAGES: %d/20\n', sum(allDelta > 0));

fprintf('\nFIGURES: 4 PNG + 4 FIG\n');
fprintf('STATISTICS CSV: %s\n', outCSV);
fprintf('RESEARCH FINDINGS: %s\n', outReport);

disp('STATUS: TASK 28.3D.6A SUCCESS');
