
%% TASK 19.8J - Ground Height and Object Proximity Validation
% GEMSTAR - Frame 150
% Uses world-coordinate LiDAR data from Task 19.8H.
% Height thresholds are diagnostic, not ground-truth labels.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

inputFile = fullfile(cloudDir, ...
    "task19_8h_frame150_world_xyz.csv");

gtFile = fullfile(dataDir, ...
    "task19_8e_gt_frame150_objects.csv");

assert(isfile(inputFile),"World-coordinate CSV missing.");
assert(isfile(gtFile),"Ground-truth CSV missing.");

T = readtable(inputFile);
GT = readtable(gtFile);

%% 2. Ground-truth vehicle center

targetID = 76865;
idx = find(GT.ObjectID == targetID,1);

assert(~isempty(idx),"GT object not found.");

cx = GT.X(idx);
cy = GT.Y(idx);
cz = GT.Z(idx);

%% 3. Horizontal distance from ground-truth center

distanceXY = hypot(T.WorldX-cx,T.WorldY-cy);

nearMask = distanceXY <= 3;

near = T(nearMask,:);

fprintf("\n=== TASK 19.8J HEIGHT VALIDATION ===\n");

fprintf("GT Object ID: %d\n",targetID);
fprintf("GT center height: %.4f m\n",cz);
fprintf("Points within 3 m XY: %d\n",height(near));

%% 4. Height statistics per simulator object ID

ids = unique(T.ObjectID);

objectStats = table();

for k = 1:numel(ids)

    mask = T.ObjectID == ids(k);
    z = T.WorldZ(mask);

    row = table();
    row.ObjectID = ids(k);
    row.PointCount = numel(z);
    row.MinZ = min(z);
    row.MedianZ = median(z);
    row.MaxZ = max(z);
    row.StdZ = std(z);
    row.PointsAbove02m = sum(z > 0.2);
    row.PointsAbove05m = sum(z > 0.5);

    objectStats = [objectStats;row];

end

fprintf("\n=== HEIGHT BY SIMULATOR OBJECT ID ===\n");
disp(objectStats);

%% 5. Nearby height-threshold comparison

thresholds = [-0.1;0.1;0.2;0.5;1.0];

allCounts = zeros(numel(thresholds),1);
nearCounts = zeros(numel(thresholds),1);

for k = 1:numel(thresholds)

    allCounts(k) = sum(T.WorldZ > thresholds(k));

    nearCounts(k) = sum(near.WorldZ > thresholds(k));

end

thresholdStats = table();

thresholdStats.MinWorldZ = thresholds;
thresholdStats.AllPointsRemaining = allCounts;
thresholdStats.NearGTWithin3m = nearCounts;

fprintf("\n=== HEIGHT THRESHOLD COMPARISON ===\n");
disp(thresholdStats);

%% 6. Determine nearest elevated points

fprintf("\n=== NEAREST ELEVATED POINTS ===\n");

for threshold = [0.2 0.5]

    valid = T.WorldZ > threshold;

    if any(valid)

        distances = distanceXY(valid);
        [nearestDistance,localIndex] = min(distances);

        validRows = find(valid);
        pointIndex = validRows(localIndex);

        fprintf( ...
            "Z > %.1f m: nearest XY distance %.3f m, ID %.0f\n", ...
            threshold,nearestDistance,T.ObjectID(pointIndex));

    else

        fprintf("Z > %.1f m: no points\n",threshold);

    end

end

%% 7. Save CSV results

statsFile = fullfile(dataDir, ...
    "task19_8j_object_height_statistics.csv");

thresholdFile = fullfile(dataDir, ...
    "task19_8j_height_threshold_comparison.csv");

nearFile = fullfile(cloudDir, ...
    "task19_8j_gt76865_nearby_world_points.csv");

writetable(objectStats,statsFile);
writetable(thresholdStats,thresholdFile);
writetable(near,nearFile);

%% 8. Generate analysis graphs

fig = figure("Color","w", ...
    "Position",[100 100 1150 500]);

subplot(1,2,1);

scatter(T.WorldX,T.WorldZ, ...
    9,T.ObjectID,"filled");

hold on;

yline(0.2,"r--","Z = 0.2 m");
yline(0.5,"k--","Z = 0.5 m");

xlabel("World X (m)");
ylabel("World Z (m)");
title("All LiDAR Points - Height by Simulator ID");

grid on;
colorbar;

subplot(1,2,2);

scatter(near.WorldX,near.WorldZ, ...
    15,near.ObjectID,"filled");

hold on;

plot(cx,cz,"rx","MarkerSize",12,"LineWidth",2);

yline(0.2,"r--","Z = 0.2 m");
yline(0.5,"k--","Z = 0.5 m");

xlabel("World X (m)");
ylabel("World Z (m)");
title("Points Within 3 m XY of GT 76865");

grid on;
colorbar;

graphFile = fullfile(graphDir, ...
    "task19_8j_ground_height_validation.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 9. Completion

fprintf("\n=== TASK 19.8J COMPLETE ===\n");

fprintf("Object-height CSV saved: %d\n",isfile(statsFile));
fprintf("Threshold CSV saved: %d\n",isfile(thresholdFile));
fprintf("Nearby-points CSV saved: %d\n",isfile(nearFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

fprintf("\nHeight filtering is exploratory.");
fprintf("\nWorld frame and object geometry still require validation.\n");
