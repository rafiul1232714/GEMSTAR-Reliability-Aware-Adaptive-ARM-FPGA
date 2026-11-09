
%% ============================================================
% TASK 12.6D - MULTI-FRAME YOLO PERFORMANCE ANALYSIS
% GEMSTAR MOR100 - Camera and Ground Truth
%
% Model: YOLO11s
% Device: CPU
%
% Input: 8 previously evaluated Camera frames
%
% Outputs:
% 1. Four-panel performance dashboard
% 2. Ground Truth distance timeline
% 3. Detection confidence vs distance
% 4. Numerical summary CSV
% 5. Frame-level analysis CSV
% 6. Research findings TXT
% 7. Archived MATLAB source code
%
% IMPORTANT:
% Camera-to-GT associations remain provisional.
% These results are not validated detector accuracy.
%% ============================================================

clc;
clear;
close all;

%% 1. DEFINE PROJECT PATHS

root = "E:\GEMSTAR_Project\sensor-health-monitor";

task = fullfile(root, ...
    "tests", "Task_12_Final_Research");

csvDir = fullfile(task, "02_CSV_Data");
graphDir = fullfile(task, "01_Graphs");
findDir = fullfile(task, "06_Research_Findings");
codeDir = fullfile(task, "04_Code");

folders = [csvDir, graphDir, findDir, codeDir];

for k = 1:numel(folders)

    if ~isfolder(folders(k))
        mkdir(folders(k));
    end

end

%% 2. LOAD MULTI-FRAME YOLO RESULTS

inputFile = fullfile(csvDir, ...
    "task12_6_multiframe_yolo_summary.csv");

assert(isfile(inputFile), ...
    "Multi-frame YOLO summary CSV is missing.");

T = readtable(inputFile, "TextType", "string");

T = sortrows(T, "frame");

assert(height(T) > 0, "Input CSV is empty.");

%% 3. EXTRACT NUMERICAL VARIABLES

frame = double(T.frame);
timeS = double(T.time_s);
distance = double(T.gt_distance_m);
latency = double(T.prediction_wall_ms);

status = string(T.candidate_status);

hasVehicle = double(T.vehicle_detection_count) > 0;

overlap = ...
    status == "PROVISIONAL_GT_CENTER_OVERLAP";

% Handle both numeric and string CSV import types.
confidence = toNumeric(T.candidate_confidence);
errorPx = toNumeric(T.center_error_px);

% Missing detections must not contribute numeric values.
confidence(~hasVehicle) = NaN;
errorPx(~hasVehicle) = NaN;

%% 4. CALCULATE RESEARCH STATISTICS

totalFrames = height(T);

detectedFrames = sum(hasVehicle);
overlapFrames = sum(overlap);

meanLatency = mean(latency, "omitnan");
minLatency = min(latency);
maxLatency = max(latency);

validConfidence = confidence(isfinite(confidence));
validError = errorPx(isfinite(errorPx));

if isempty(validConfidence)
    meanConfidence = NaN;
else
    meanConfidence = mean(validConfidence);
end

if isempty(validError)
    meanError = NaN;
else
    meanError = mean(validError);
end

% Separate analysis for the six provisional overlap frames.
overlapConfidence = confidence( ...
    overlap & isfinite(confidence));

overlapError = errorPx( ...
    overlap & isfinite(errorPx));

overlapLatency = latency( ...
    overlap & isfinite(latency));

if isempty(overlapConfidence)
    meanOverlapConfidence = NaN;
else
    meanOverlapConfidence = mean(overlapConfidence);
end

if isempty(overlapError)
    meanOverlapError = NaN;
else
    meanOverlapError = mean(overlapError);
end

if isempty(overlapLatency)
    meanOverlapLatency = NaN;
else
    meanOverlapLatency = mean(overlapLatency);
end

%% 5. PRINT RESULTS

fprintf('\n============================================\n');
fprintf('TASK 12.6D - MULTI-FRAME PERFORMANCE\n');
fprintf('============================================\n');

fprintf('Frames analyzed: %d\n', totalFrames);

fprintf('Frames with vehicle detections: %d\n', ...
    detectedFrames);

fprintf('Frames with provisional GT overlap: %d\n', ...
    overlapFrames);

fprintf('\n--- ALL EVALUATED FRAMES ---\n');

fprintf('Mean CPU prediction wall time: %.3f ms\n', ...
    meanLatency);

fprintf('Minimum CPU time: %.3f ms\n', minLatency);
fprintf('Maximum CPU time: %.3f ms\n', maxLatency);

fprintf('Mean selected confidence: %.4f\n', ...
    meanConfidence);

fprintf('Mean selected center difference: %.3f px\n', ...
    meanError);

fprintf('\n--- PROVISIONAL GT OVERLAP FRAMES ---\n');

fprintf('Number of overlap frames: %d\n', ...
    overlapFrames);

fprintf('Mean overlap confidence: %.4f\n', ...
    meanOverlapConfidence);

fprintf('Mean overlap center difference: %.3f px\n', ...
    meanOverlapError);

fprintf('Mean overlap CPU time: %.3f ms\n', ...
    meanOverlapLatency);

fprintf('\nProvisional overlap frames:\n');

disp(frame(overlap)');

%% 6. CREATE FOUR-PANEL DASHBOARD

fig = figure( ...
    'Color', 'w', ...
    'Position', [70 70 1450 850]);

t = tiledlayout(2, 2, ...
    'TileSpacing', 'compact', ...
    'Padding', 'compact');

%% PANEL 1 - CONFIDENCE VS DISTANCE

nexttile(t, 1);
hold on;

scatter( ...
    distance(hasVehicle), ...
    confidence(hasVehicle), ...
    85, [0.1 0.45 0.9], ...
    'filled');

scatter( ...
    distance(overlap), ...
    confidence(overlap), ...
    105, [0.1 0.65 0.2], ...
    'filled');

for k = 1:totalFrames

    if hasVehicle(k) && isfinite(confidence(k))

        text( ...
            distance(k), ...
            confidence(k), ...
            sprintf(' %d', frame(k)), ...
            'FontSize', 9);

    end

end

xlabel('Ground Truth distance (m)');
ylabel('Selected confidence');

title('YOLO11s Confidence vs GT Distance');

ylim([0 1]);
grid on;

legend( ...
    {'All detected frames', ...
     'Provisional GT overlap'}, ...
    'Location', 'best');

%% PANEL 2 - CPU PREDICTION TIME

nexttile(t, 2);

plot( ...
    frame, latency, '-o', ...
    'LineWidth', 1.8, ...
    'MarkerSize', 7);

hold on;

yline(meanLatency, '--', ...
    sprintf('Mean: %.1f ms', meanLatency));

xlabel('Recorded frame');
ylabel('Prediction wall time (ms)');

title('YOLO11s CPU Prediction Time');

grid on;

%% PANEL 3 - GT TO DETECTION CENTER DIFFERENCE

nexttile(t, 3);
hold on;

scatter( ...
    frame(hasVehicle), ...
    errorPx(hasVehicle), ...
    80, [0.3 0.45 0.9], ...
    'filled');

scatter( ...
    frame(overlap), ...
    errorPx(overlap), ...
    105, [0.1 0.65 0.2], ...
    'filled');

xlabel('Recorded frame');
ylabel('Center difference (pixels)');

title('GT Projection vs Selected Detection');

legend( ...
    {'Detected frames', ...
     'Provisional GT overlap'}, ...
    'Location', 'best');

grid on;

%% PANEL 4 - DETECTION OUTCOMES

nexttile(t, 4);

outcome = zeros(totalFrames, 1);

outcome(hasVehicle) = 1;
outcome(overlap) = 2;

bar(frame, outcome, 0.65);

yticks([0 1 2]);

yticklabels({ ...
    'No vehicle', ...
    'No GT overlap', ...
    'Provisional overlap'});

ylim([-0.2 2.4]);

xlabel('Recorded frame');
ylabel('Detection outcome');

title('Frame-Level Detection Status');

grid on;

sgtitle( ...
    'GEMSTAR MOR100 - Task 12.6D Performance Dashboard');

%% 7. SAVE DASHBOARD

dashboardPNG = fullfile(graphDir, ...
    "task12_6_multiframe_performance_dashboard.png");

dashboardFIG = fullfile(graphDir, ...
    "task12_6_multiframe_performance_dashboard.fig");

exportgraphics(fig, dashboardPNG, ...
    'Resolution', 250);

savefig(fig, dashboardFIG);

%% 8. FIGURE 2 - GROUND TRUTH DISTANCE TIMELINE

fig2 = figure( ...
    'Color', 'w', ...
    'Position', [120 120 1050 550]);

hold on;

plot( ...
    timeS, distance, '-o', ...
    'LineWidth', 1.8, ...
    'MarkerSize', 7);

scatter( ...
    timeS(overlap), ...
    distance(overlap), ...
    85, [0.9 0.35 0.1], ...
    'filled');

xlabel('Time (s)');
ylabel('Ground Truth distance (m)');

title('Ground Truth Distance Across Camera Frames');

legend( ...
    {'Evaluated candidate frames', ...
     'Provisional overlap frames'}, ...
    'Location', 'best');

grid on;

distancePNG = fullfile(graphDir, ...
    "task12_6_gt_distance_timeline.png");

distanceFIG = fullfile(graphDir, ...
    "task12_6_gt_distance_timeline.fig");

exportgraphics(fig2, distancePNG, ...
    'Resolution', 250);

savefig(fig2, distanceFIG);

%% 9. FIGURE 3 - CONFIDENCE VS DISTANCE

fig3 = figure( ...
    'Color', 'w', ...
    'Position', [160 160 1050 550]);

hold on;

scatter( ...
    distance(hasVehicle), ...
    confidence(hasVehicle), ...
    90, [0.1 0.45 0.9], ...
    'filled');

scatter( ...
    distance(overlap), ...
    confidence(overlap), ...
    115, [0.1 0.65 0.2], ...
    'filled');

for k = 1:totalFrames

    if hasVehicle(k) && isfinite(confidence(k))

        text( ...
            distance(k), ...
            confidence(k), ...
            sprintf(' Frame %d', frame(k)), ...
            'FontSize', 9);

    end

end

xlabel('Ground Truth distance (m)');
ylabel('Detection confidence');

title('YOLO11s Confidence vs Distance');

ylim([0 1]);
grid on;

legend( ...
    {'Vehicle detections', ...
     'Provisional GT overlaps'}, ...
    'Location', 'best');

confidencePNG = fullfile(graphDir, ...
    "task12_6_confidence_vs_distance.png");

confidenceFIG = fullfile(graphDir, ...
    "task12_6_confidence_vs_distance.fig");

exportgraphics(fig3, confidencePNG, ...
    'Resolution', 250);

savefig(fig3, confidenceFIG);

%% 10. CREATE COMPLETE NUMERICAL SUMMARY

% FIX:
% Use one explicit scalar per table column.
% Assign column names after table construction.

S = table( ...
    totalFrames, ...
    detectedFrames, ...
    overlapFrames, ...
    meanLatency, ...
    minLatency, ...
    maxLatency, ...
    meanConfidence, ...
    meanError, ...
    meanOverlapConfidence, ...
    meanOverlapError, ...
    meanOverlapLatency);

S.Properties.VariableNames = { ...
    'frames_analyzed', ...
    'frames_with_vehicle_detection', ...
    'frames_with_provisional_overlap', ...
    'mean_cpu_prediction_ms', ...
    'min_cpu_prediction_ms', ...
    'max_cpu_prediction_ms', ...
    'mean_selected_confidence', ...
    'mean_selected_center_error_px', ...
    'mean_overlap_confidence', ...
    'mean_overlap_center_error_px', ...
    'mean_overlap_cpu_ms'};

summaryFile = fullfile(csvDir, ...
    "task12_6_multiframe_performance_summary.csv");

writetable(S, summaryFile);

%% 11. SAVE FRAME-LEVEL ANALYSIS CSV

frameAnalysis = table( ...
    frame, ...
    timeS, ...
    distance, ...
    latency, ...
    hasVehicle, ...
    overlap, ...
    confidence, ...
    errorPx, ...
    status);

frameAnalysis.Properties.VariableNames = { ...
    'frame', ...
    'time_s', ...
    'gt_distance_m', ...
    'prediction_wall_ms', ...
    'vehicle_detected', ...
    'provisional_gt_overlap', ...
    'selected_confidence', ...
    'center_difference_px', ...
    'candidate_status'};

frameFile = fullfile(csvDir, ...
    "task12_6_frame_level_analysis.csv");

writetable(frameAnalysis, frameFile);

%% 12. SAVE RESEARCH FINDINGS

reportFile = fullfile(findDir, ...
    "task12_6_multiframe_performance_findings.txt");

fid = fopen(reportFile, 'w');

assert(fid ~= -1, ...
    'Unable to create research findings file.');

fprintf(fid, ...
    'TASK 12.6D - MULTI-FRAME PERFORMANCE ANALYSIS\n');

fprintf(fid, ...
    'Scenario: GEMSTAR MOR100\n');

fprintf(fid, ...
    'Model: YOLO11s\n');

fprintf(fid, ...
    'Device: CPU\n\n');

fprintf(fid, ...
    'TOTAL FRAMES ANALYZED: %d\n', totalFrames);

fprintf(fid, ...
    'FRAMES WITH VEHICLE DETECTIONS: %d\n', ...
    detectedFrames);

fprintf(fid, ...
    'PROVISIONAL GT OVERLAP FRAMES: %d\n', ...
    overlapFrames);

fprintf(fid, '\nOVERALL RESULTS\n');

fprintf(fid, ...
    'Mean prediction wall time: %.4f ms\n', ...
    meanLatency);

fprintf(fid, ...
    'Minimum prediction wall time: %.4f ms\n', ...
    minLatency);

fprintf(fid, ...
    'Maximum prediction wall time: %.4f ms\n', ...
    maxLatency);

fprintf(fid, ...
    'Mean selected confidence: %.4f\n', ...
    meanConfidence);

fprintf(fid, ...
    'Mean selected center difference: %.4f px\n', ...
    meanError);

fprintf(fid, '\nPROVISIONAL OVERLAP FRAMES\n');

fprintf(fid, ...
    'Mean confidence: %.4f\n', ...
    meanOverlapConfidence);

fprintf(fid, ...
    'Mean center difference: %.4f px\n', ...
    meanOverlapError);

fprintf(fid, ...
    'Mean prediction wall time: %.4f ms\n', ...
    meanOverlapLatency);

fprintf(fid, '\nRESEARCH INTERPRETATION\n');

fprintf(fid, ...
    'YOLO11s produced vehicle detections in 7 of 8 evaluated frames.\n');

fprintf(fid, ...
    'Six detections contain the projected Ground Truth center.\n');

fprintf(fid, ...
    'Frame 91 has no vehicle detection.\n');

fprintf(fid, ...
    'Frame 431 has a detected vehicle without GT-center overlap.\n');

fprintf(fid, ...
    'The approach sequence supports candidate geometric correspondence.\n');

fprintf(fid, '\nIMPORTANT LIMITATIONS\n');

fprintf(fid, ...
    'Ground Truth Camera calibration remains provisional.\n');

fprintf(fid, ...
    'GT-center overlap does not prove vehicle identity.\n');

fprintf(fid, ...
    'The evaluated frames were selected geometrically.\n');

fprintf(fid, ...
    'Selected detections are not independent annotations.\n');

fprintf(fid, ...
    'Detection counts are not verified recall or precision.\n');

fprintf(fid, ...
    'CPU wall-clock times are preliminary single-run measurements.\n');

fprintf(fid, ...
    'No FPGA speedup or energy reduction has been demonstrated.\n');

fprintf(fid, ...
    'Tri-sensor object-level fusion remains unverified.\n');

fclose(fid);

%% 13. ARCHIVE MATLAB SOURCE CODE

sourceFile = fullfile(root, ...
    "matlab", ...
    "task12_multiframe_performance_analysis.m");

if isfile(sourceFile)

    copyfile(sourceFile, codeDir, 'f');

else

    warning( ...
        'MATLAB source file not found for archiving.');

end

%% 14. PRINT FINAL SUMMARY

fprintf('\n============================================\n');
fprintf('TASK 12.6D - NUMERICAL SUMMARY\n');
fprintf('============================================\n');

disp(S);

fprintf('\nSaved research outputs:\n');

fprintf('Dashboard: %s\n', dashboardPNG);
fprintf('Distance timeline: %s\n', distancePNG);
fprintf('Confidence graph: %s\n', confidencePNG);

fprintf('Summary CSV: %s\n', summaryFile);
fprintf('Frame analysis CSV: %s\n', frameFile);
fprintf('Findings: %s\n', reportFile);

fprintf('\nTASK 12.6D COMPLETED SUCCESSFULLY\n');

%% ============================================================
% LOCAL HELPER FUNCTION
%% ============================================================

function values = toNumeric(input)

    if isnumeric(input)

        values = double(input);

    else

        values = str2double(string(input));

    end

    values = values(:);

end
