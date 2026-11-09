
%% TASK 19.8K - Diagnose LiDAR Actor Geometry
% GEMSTAR - frame 150
% Compare simulator IDs 83185 (ground-like)
% and 83265 (dominant DBSCAN cluster).
% No additional toolbox required.

clear;
clc;
close all;

%% 1. Paths
base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

worldFile = fullfile(cloudDir, ...
    "task19_8h_frame150_world_xyz.csv");

clusterFile = fullfile(cloudDir, ...
    "task19_7a_frame150_clustered_points.csv");

assert(isfile(worldFile),"World LiDAR CSV missing.");
assert(isfile(clusterFile),"DBSCAN CSV missing.");

T = readtable(worldFile);
C = readtable(clusterFile);

%% 2. Objects to investigate

targetIDs = [83185;83265];

stats = table();

fprintf("\n=== TASK 19.8K ACTOR GEOMETRY ===\n");

for k = 1:numel(targetIDs)

    id = targetIDs(k);

    A = T(T.ObjectID == id,:);

    assert(height(A)>0, ...
        "Target ID not found in world cloud.");

    z = A.WorldZ;

    row = table();

    row.ObjectID = id;
    row.PointCount = height(A);

    row.MinX = min(A.WorldX);
    row.MaxX = max(A.WorldX);
    row.MinY = min(A.WorldY);
    row.MaxY = max(A.WorldY);

    row.MinZ = min(z);
    row.MedianZ = median(z);
    row.MaxZ = max(z);

    row.XSpan = max(A.WorldX)-min(A.WorldX);
    row.YSpan = max(A.WorldY)-min(A.WorldY);
    row.ZSpan = max(z)-min(z);

    row.BelowOrAt02m = sum(z<=0.2);
    row.Above02m = sum(z>0.2);
    row.Above05m = sum(z>0.5);

    row.InDBSCANClusters = sum( ...
        C.ObjectID == id & C.ClusterID > 0);

    row.DBSCANNoise = sum( ...
        C.ObjectID == id & C.ClusterID == -1);

    stats = [stats;row];

    fprintf("\nObject ID %.0f\n",id);
    fprintf("Candidate points: %d\n",height(A));
    fprintf("World height: %.3f to %.3f m\n", ...
        row.MinZ,row.MaxZ);
    fprintf("World Z median: %.3f m\n",row.MedianZ);
    fprintf("Horizontal span X: %.3f m\n",row.XSpan);
    fprintf("Horizontal span Y: %.3f m\n",row.YSpan);
    fprintf("Points above 0.2 m: %d\n",row.Above02m);
    fprintf("Points above 0.5 m: %d\n",row.Above05m);
    fprintf("DBSCAN cluster points: %d\n", ...
        row.InDBSCANClusters);

end

%% 3. Export statistics

statsFile = fullfile(dataDir, ...
    "task19_8k_actor_geometry_summary.csv");

writetable(stats,statsFile);

%% 4. Visualization

fig = figure("Color","w", ...
    "Position",[100 100 1200 780]);

for k = 1:numel(targetIDs)

    id = targetIDs(k);
    A = T(T.ObjectID == id,:);

    % Top view
    subplot(2,2,k);

    scatter(A.WorldX,A.WorldY, ...
        9,A.WorldZ,"filled");

    axis equal;
    grid on;
    colorbar;

    xlabel("World X (m)");
    ylabel("World Y (m)");
    title(sprintf("Object %.0f: Top View",id));

    % Side view
    subplot(2,2,k+2);

    scatter(A.WorldX,A.WorldZ, ...
        10,A.WorldY,"filled");

    hold on;
    yline(0.2,"r--","0.2 m");
    yline(0.5,"k--","0.5 m");

    grid on;
    colorbar;

    xlabel("World X (m)");
    ylabel("World Z (m)");
    title(sprintf("Object %.0f: Vertical Profile",id));

end

sgtitle("GEMSTAR LiDAR Actor Geometry Diagnosis");

graphFile = fullfile(graphDir, ...
    "task19_8k_actor_geometry_comparison.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 5. Export elevated points of ID 83265

elevated = T( ...
    T.ObjectID == 83265 & T.WorldZ > 0.2,:);

elevatedFile = fullfile(cloudDir, ...
    "task19_8k_id83265_elevated_points.csv");

writetable(elevated,elevatedFile);

%% 6. Finish

fprintf("\n=== TASK 19.8K COMPLETE ===\n");

fprintf("Statistics CSV saved: %d\n",isfile(statsFile));
fprintf("Comparison graph saved: %d\n",isfile(graphFile));
fprintf("Elevated-point CSV saved: %d\n",isfile(elevatedFile));

fprintf("Elevated points of ID 83265: %d\n", ...
    height(elevated));

disp(stats);
