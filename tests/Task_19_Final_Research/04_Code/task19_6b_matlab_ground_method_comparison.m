%% TASK 19.6B - Compare Ground Filtering Methods
clear; clc; close all;

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
graphDir = fullfile(base,"01_Graphs");
dataDir = fullfile(base,"02_CSV_Data");

T = readtable(fullfile(cloudDir, ...
    "task19_4a_frame150_roi_xyz.csv"));

R = readtable(fullfile(cloudDir, ...
    "task19_6a_frame150_ransac_ground.csv"));

%% 1. Match RANSAC ground points by original ray index

ransacGround = ismember(T.RayIndex,R.RayIndex);

%% 2. Recreate simple height-band classification

heightGround = T.Z >= -0.80 & T.Z <= -0.60;

%% 3. Compare classifications

bothGround = heightGround & ransacGround;
heightOnly = heightGround & ~ransacGround;
ransacOnly = ~heightGround & ransacGround;
neitherGround = ~heightGround & ~ransacGround;

n = height(T);

agreement = 100 * ...
    (sum(bothGround)+sum(neitherGround))/n;

fprintf("\n=== TASK 19.6B METHOD COMPARISON ===\n");
fprintf("Total ROI points: %d\n",n);
fprintf("Both classified as ground: %d\n",sum(bothGround));
fprintf("Height-band ground only: %d\n",sum(heightOnly));
fprintf("RANSAC ground only: %d\n",sum(ransacOnly));
fprintf("Both classified as non-ground: %d\n",sum(neitherGround));
fprintf("Classification agreement: %.2f%%\n",agreement);

%% 4. Visualization

fig = figure("Color","w","Position",[100 100 1050 500]);

scatter(T.X(bothGround),T.Y(bothGround),8, ...
    [0.6 0.6 0.6],"filled");
hold on;

scatter(T.X(heightOnly),T.Y(heightOnly),16, ...
    [0.9 0.2 0.2],"filled");

scatter(T.X(ransacOnly),T.Y(ransacOnly),16, ...
    [0.2 0.3 0.9],"filled");

scatter(T.X(neitherGround),T.Y(neitherGround),16, ...
    [0.1 0.7 0.3],"filled");

xlabel("Forward X (m)");
ylabel("Lateral Y (m)");
title("Task 19 - Ground Classification Agreement");

legend( ...
    "Both ground", ...
    "Height only", ...
    "RANSAC only", ...
    "Both non-ground", ...
    "Location","bestoutside");

axis equal;
grid on;

graphFile = fullfile(graphDir, ...
    "task19_6b_ground_method_comparison.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 5. Save comparison for reproducibility

comparison = T(:,["RayIndex","X","Y","Z"]);
comparison.HeightBandGround = heightGround;
comparison.RANSACGround = ransacGround;
comparison.Agree = heightGround == ransacGround;

comparisonFile = fullfile(dataDir, ...
    "task19_6b_per_point_ground_comparison.csv");

writetable(comparison,comparisonFile);

summary = table( ...
    n,sum(bothGround),sum(heightOnly), ...
    sum(ransacOnly),sum(neitherGround),agreement, ...
    'VariableNames', { ...
    'TotalPoints','BothGround','HeightOnly', ...
    'RANSACOnly','BothNonGround','AgreementPercent'});

summaryFile = fullfile(dataDir, ...
    "task19_6b_ground_method_summary.csv");

writetable(summary,summaryFile);

fprintf("\n=== TASK 19.6B COMPLETE ===\n");
fprintf("Graph saved: %d\n",isfile(graphFile));
fprintf("Per-point CSV saved: %d\n",isfile(comparisonFile));
fprintf("Summary CSV saved: %d\n",isfile(summaryFile));