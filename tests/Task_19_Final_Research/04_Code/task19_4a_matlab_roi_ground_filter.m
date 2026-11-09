%% TASK 19.4A
% GEMSTAR LiDAR ROI and provisional ground filtering

clear;
clc;
close all;

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

inputFile = fullfile(base, ...
    "08_Extracted_PointClouds", ...
    "task19_2a_frame150_candidate_xyz.csv");

graphDir = fullfile(base, "01_Graphs");
dataDir = fullfile(base, "02_CSV_Data");
cloudDir = fullfile(base, "08_Extracted_PointClouds");

T = readtable(inputFile);

%% 1. ROI parameters
% These are experimental parameters, not sensor specifications.

xMin = 0;
xMax = 20;

yMin = -6;
yMax = 6;

roiMask = ...
    T.X >= xMin & T.X <= xMax & ...
    T.Y >= yMin & T.Y <= yMax;

T_ROI = T(roiMask, :);

%% 2. Provisional ground-band exclusion

groundLow = -0.80;
groundHigh = -0.60;

groundMaskROI = ...
    T_ROI.Z >= groundLow & T_ROI.Z <= groundHigh;

T_GroundCandidate = T_ROI(groundMaskROI, :);
T_Remaining = T_ROI(~groundMaskROI, :);

%% 3. Statistics

originalCount = height(T);
roiCount = height(T_ROI);
groundCandidateCount = height(T_GroundCandidate);
remainingCount = height(T_Remaining);

roiReduction = 100 * (1 - roiCount / originalCount);
totalReduction = 100 * (1 - remainingCount / originalCount);

fprintf("\n=== TASK 19.4A ROI AND GROUND FILTERING ===\n");

fprintf("Original candidate points: %d\n", originalCount);
fprintf("After ROI filtering: %d\n", roiCount);
fprintf("Points in ground band within ROI: %d\n", groundCandidateCount);
fprintf("Remaining points: %d\n", remainingCount);

fprintf("ROI reduction: %.2f%%\n", roiReduction);
fprintf("Total reduction: %.2f%%\n", totalReduction);

assert(originalCount == roiCount + sum(~roiMask));
assert(roiCount == groundCandidateCount + remainingCount);

%% 4. Plot cloud comparison

fig = figure("Color", "w", ...
    "Position", [100 100 1200 450]);

subplot(1, 3, 1);
scatter(T.X, T.Y, 8, T.RangeM, "filled");
axis equal; grid on;
xlabel("Forward X (m)");
ylabel("Lateral Y (m)");
title(sprintf("Original: %d points", originalCount));

subplot(1, 3, 2);
scatter(T_ROI.X, T_ROI.Y, 8, T_ROI.RangeM, "filled");
axis equal; grid on;
xlabel("Forward X (m)");
ylabel("Lateral Y (m)");
title(sprintf("ROI: %d points", roiCount));

subplot(1, 3, 3);
scatter(T_Remaining.X, T_Remaining.Y, 8, T_Remaining.RangeM, "filled");
axis equal; grid on;
xlabel("Forward X (m)");
ylabel("Lateral Y (m)");
title(sprintf("After ground-band exclusion: %d", remainingCount));

exportgraphics(fig, ...
    fullfile(graphDir, ...
    "task19_4a_roi_ground_comparison.png"), ...
    "Resolution", 200);

%% 5. Save filtered point clouds

roiFile = fullfile(cloudDir, ...
    "task19_4a_frame150_roi_xyz.csv");

groundFile = fullfile(cloudDir, ...
    "task19_4a_frame150_ground_band_xyz.csv");

remainingFile = fullfile(cloudDir, ...
    "task19_4a_frame150_remaining_xyz.csv");

writetable(T_ROI, roiFile);
writetable(T_GroundCandidate, groundFile);
writetable(T_Remaining, remainingFile);

%% 6. Save numerical summary

summaryTable = table( ...
    originalCount, roiCount, ...
    groundCandidateCount, remainingCount, ...
    roiReduction, totalReduction);

summaryFile = fullfile(dataDir, ...
    "task19_4a_roi_ground_filter_summary.csv");

writetable(summaryTable, summaryFile);

%% 7. Verify

fprintf("\n=== TASK 19.4A COMPLETE ===\n");
fprintf("Comparison graph saved: %d\n", ...
    isfile(fullfile(graphDir, ...
    "task19_4a_roi_ground_comparison.png")));
fprintf("ROI CSV saved: %d\n", isfile(roiFile));
fprintf("Ground-band CSV saved: %d\n", isfile(groundFile));
fprintf("Remaining-point CSV saved: %d\n", isfile(remainingFile));
fprintf("Summary CSV saved: %d\n", isfile(summaryFile));