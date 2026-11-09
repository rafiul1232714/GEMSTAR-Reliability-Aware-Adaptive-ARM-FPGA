%% TASK 19.6A - Ground Plane Estimation with RANSAC
clear; clc; close all;

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
graphDir = fullfile(base,"01_Graphs");
dataDir = fullfile(base,"02_CSV_Data");

T = readtable(fullfile(cloudDir, ...
    "task19_4a_frame150_roi_xyz.csv"));

P = [T.X,T.Y,T.Z];
N = size(P,1);

%% 1. RANSAC settings

rng(19);

iterations = 1000;
distanceThreshold = 0.08;
maxGroundTiltDeg = 15;
minInliers = 50;

bestCount = 0;
bestPlane = [0 0 1 0];

%% 2. Search for ground plane

for k = 1:iterations

    idx = randperm(N,3);
    A = P(idx(1),:);
    B = P(idx(2),:);
    C = P(idx(3),:);

    normal = cross(B-A,C-A);
    normalMagnitude = norm(normal);

    if normalMagnitude < 1e-9
        continue;
    end

    normal = normal / normalMagnitude;

    % Make Z component positive
    if normal(3) < 0
        normal = -normal;
    end

    tilt = acosd(max(-1,min(1,normal(3))));

    if tilt > maxGroundTiltDeg
        continue;
    end

    d = -dot(normal,A);

    distances = abs(P*normal' + d);
    inliers = distances <= distanceThreshold;

    count = sum(inliers);

    if count > bestCount
        bestCount = count;
        bestPlane = [normal,d];
    end
end

assert(bestCount >= minInliers, ...
    "RANSAC could not identify a sufficiently supported plane.");

%% 3. Calculate final inliers

normal = bestPlane(1:3);
d = bestPlane(4);

distances = abs(P*normal' + d);
groundMask = distances <= distanceThreshold;

T_Ground = T(groundMask,:);
T_ObstacleCandidate = T(~groundMask,:);

groundCount = height(T_Ground);
remainingCount = height(T_ObstacleCandidate);

%% 4. Print results

fprintf("\n=== TASK 19.6A RANSAC GROUND PLANE ===\n");
fprintf("Original ROI points: %d\n",N);
fprintf("Ground-plane inliers: %d\n",groundCount);
fprintf("Non-plane candidate points: %d\n",remainingCount);
fprintf("Ground-plane fraction: %.2f%%\n",100*groundCount/N);

fprintf("Estimated plane: %.6fx + %.6fy + %.6fz + %.6f = 0\n", ...
    bestPlane(1),bestPlane(2),bestPlane(3),bestPlane(4));

fprintf("Estimated ground Z at sensor origin: %.4f m\n", ...
    -d/normal(3));

%% 5. Visual comparison

fig = figure("Color","w","Position",[100 100 1100 450]);

subplot(1,2,1);
scatter3(T_Ground.X,T_Ground.Y,T_Ground.Z,8, ...
    [0.2 0.6 0.9],"filled");
hold on;
scatter3(T_ObstacleCandidate.X,T_ObstacleCandidate.Y, ...
    T_ObstacleCandidate.Z,12,[0.9 0.3 0.2],"filled");

xlabel("X (m)");
ylabel("Y (m)");
zlabel("Z (m)");

title("RANSAC Ground vs Non-plane Points");
legend("Plane inliers","Non-plane candidates");
axis equal; grid on; view(40,20);

subplot(1,2,2);
scatter(T_ObstacleCandidate.X,T_ObstacleCandidate.Y, ...
    12,T_ObstacleCandidate.Z,"filled");

xlabel("X - Forward (m)");
ylabel("Y - Lateral (m)");
title(sprintf("After RANSAC: %d points",remainingCount));

axis equal; grid on;
colorbar;

graphFile = fullfile(graphDir, ...
    "task19_6a_ransac_ground_segmentation.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 6. Save data

groundFile = fullfile(cloudDir, ...
    "task19_6a_frame150_ransac_ground.csv");

remainingFile = fullfile(cloudDir, ...
    "task19_6a_frame150_ransac_nonplane.csv");

writetable(T_Ground,groundFile);
writetable(T_ObstacleCandidate,remainingFile);

summary = table(N,groundCount,remainingCount, ...
    100*groundCount/N, ...
    bestPlane(1),bestPlane(2),bestPlane(3),bestPlane(4), ...
    'VariableNames', ...
    {'OriginalPoints','GroundInliers','NonPlanePoints', ...
     'GroundPercent','PlaneA','PlaneB','PlaneC','PlaneD'});

summaryFile = fullfile(dataDir, ...
    "task19_6a_ransac_ground_summary.csv");

writetable(summary,summaryFile);

fprintf("\n=== TASK 19.6A COMPLETE ===\n");
fprintf("Ground CSV saved: %d\n",isfile(groundFile));
fprintf("Non-plane CSV saved: %d\n",isfile(remainingFile));
fprintf("Summary CSV saved: %d\n",isfile(summaryFile));
fprintf("Graph saved: %d\n",isfile(graphFile));