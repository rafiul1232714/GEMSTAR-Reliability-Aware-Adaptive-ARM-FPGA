
%% TASK 19.8A - Cluster Object ID Validation
% GEMSTAR LiDAR research - frame 150
% Determine which simulator object IDs appear in each DBSCAN cluster.

clear;
clc;
close all;

%% 1. Paths
base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
graphDir = fullfile(base,"01_Graphs");
dataDir = fullfile(base,"02_CSV_Data");

inputFile = fullfile(cloudDir, ...
    "task19_7a_frame150_clustered_points.csv");

assert(isfile(inputFile), "Cluster CSV not found.");

%% 2. Load points

T = readtable(inputFile);

assert(ismember("ObjectID",string(T.Properties.VariableNames)), ...
    "ObjectID column missing.");

assert(ismember("ClusterID",string(T.Properties.VariableNames)), ...
    "ClusterID column missing.");

clusterIDs = unique(T.ClusterID);
clusterIDs = clusterIDs(clusterIDs > 0);

%% 3. Object ID statistics

result = table();

for k = 1:numel(clusterIDs)

    cid = clusterIDs(k);
    mask = T.ClusterID == cid;

    ids = T.ObjectID(mask);

    [uniqueIDs,~,group] = unique(ids);
    counts = accumarray(group,1);

    [maxCount,index] = max(counts);

    dominantID = uniqueIDs(index);
    purity = 100 * maxCount / numel(ids);

    fprintf("\n=== CLUSTER %d ===\n",cid);
    fprintf("Points: %d\n",numel(ids));
    fprintf("Unique simulator IDs: %d\n",numel(uniqueIDs));
    fprintf("Dominant object ID: %.0f\n",dominantID);
    fprintf("Dominant ID fraction: %.2f%%\n",purity);

    for j = 1:numel(uniqueIDs)
        fprintf("  ID %.0f: %d points\n", ...
            uniqueIDs(j),counts(j));
    end

    newRow = table();
    newRow.ClusterID = cid;
    newRow.PointCount = numel(ids);
    newRow.UniqueObjectIDs = numel(uniqueIDs);
    newRow.DominantObjectID = dominantID;
    newRow.DominantCount = maxCount;
    newRow.DominantFractionPercent = purity;

    result = [result;newRow];
end

%% 4. Save summary

summaryFile = fullfile(dataDir, ...
    "task19_8a_cluster_object_id_summary.csv");

writetable(result,summaryFile);

%% 5. Visualize cluster IDs versus simulator IDs

fig = figure("Color","w","Position",[100 100 1100 470]);

subplot(1,2,1);
scatter(T.X,T.Y,15,T.ClusterID,"filled");
xlabel("X (m)");
ylabel("Y (m)");
title("DBSCAN Cluster Labels");
axis equal;
grid on;
colorbar;

subplot(1,2,2);
scatter(T.X,T.Y,15,T.ObjectID,"filled");
xlabel("X (m)");
ylabel("Y (m)");
title("GEMSTAR Simulator Object IDs");
axis equal;
grid on;
colorbar;

graphFile = fullfile(graphDir, ...
    "task19_8a_cluster_vs_object_id.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 6. Finish

fprintf("\n=== TASK 19.8A COMPLETE ===\n");
fprintf("Summary CSV saved: %d\n",isfile(summaryFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

disp(result);
