
%% TASK 19.8B - Track LiDAR Object IDs Through Processing
% GEMSTAR LiDAR - Frame 150
% Compare original, ROI, RANSAC and DBSCAN object IDs
% No additional toolbox required

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base, "08_Extracted_PointClouds");
dataDir = fullfile(base, "02_CSV_Data");
graphDir = fullfile(base, "01_Graphs");

%% 2. Load processing-stage data

original = readtable(fullfile(cloudDir, ...
    "task19_2a_frame150_candidate_xyz.csv"));

roi = readtable(fullfile(cloudDir, ...
    "task19_4a_frame150_roi_xyz.csv"));

nonplane = readtable(fullfile(cloudDir, ...
    "task19_6a_frame150_ransac_nonplane.csv"));

clustered = readtable(fullfile(cloudDir, ...
    "task19_7a_frame150_clustered_points.csv"));

assert(height(nonplane) == height(clustered), ...
    "Non-plane and clustered counts do not match.");

%% 3. Identify all object IDs

objectIDs = unique(original.ObjectID);
nIDs = numel(objectIDs);

originalCounts = zeros(nIDs,1);
roiCounts = zeros(nIDs,1);
nonplaneCounts = zeros(nIDs,1);
clusteredCounts = zeros(nIDs,1);
noiseCounts = zeros(nIDs,1);

%% 4. Count points for each object ID

for k = 1:nIDs

    id = objectIDs(k);

    originalCounts(k) = sum(original.ObjectID == id);
    roiCounts(k) = sum(roi.ObjectID == id);
    nonplaneCounts(k) = sum(nonplane.ObjectID == id);

    clusteredCounts(k) = sum( ...
        clustered.ObjectID == id & clustered.ClusterID > 0);

    noiseCounts(k) = sum( ...
        clustered.ObjectID == id & clustered.ClusterID == -1);
end

%% 5. Create summary table safely

summary = table();

summary.ObjectID = objectIDs(:);
summary.OriginalPoints = originalCounts;
summary.ROIPoints = roiCounts;
summary.AfterRANSAC = nonplaneCounts;
summary.DBSCANClustered = clusteredCounts;
summary.DBSCANNoise = noiseCounts;

summary.RetentionAfterRANSACPercent = ...
    100 * nonplaneCounts ./ max(originalCounts,1);

%% 6. Show results

fprintf("\n=== TASK 19.8B OBJECT ID TRACKING ===\n");

disp(summary);

fprintf("Original candidate points: %d\n",height(original));
fprintf("ROI points: %d\n",height(roi));
fprintf("RANSAC non-plane points: %d\n",height(nonplane));
fprintf("Clustered points: %d\n",sum(clustered.ClusterID > 0));
fprintf("Noise points: %d\n",sum(clustered.ClusterID == -1));

assert(sum(originalCounts) == height(original));
assert(sum(roiCounts) == height(roi));
assert(sum(nonplaneCounts) == height(nonplane));
assert(all(clusteredCounts + noiseCounts == nonplaneCounts));

%% 7. Save object ID tracking

summaryFile = fullfile(dataDir, ...
    "task19_8b_object_id_processing_tracking.csv");

writetable(summary,summaryFile);

%% 8. Generate comparison graph

fig = figure("Color","w", ...
    "Position",[100 100 1100 550]);

counts = [originalCounts, roiCounts, ...
          nonplaneCounts, clusteredCounts];

bar(counts,"grouped");

xlabel("Simulator object ID");
ylabel("Number of LiDAR points");

title("GEMSTAR LiDAR - Object ID Retention Across Processing");

xticks(1:nIDs);
xticklabels(string(objectIDs));

legend( ...
    "Original candidate", ...
    "After ROI", ...
    "After RANSAC", ...
    "After DBSCAN", ...
    "Location","best");

grid on;

graphFile = fullfile(graphDir, ...
    "task19_8b_object_id_retention.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 9. Detailed cluster-by-object table

clusterIDs = unique(clustered.ClusterID);
clusterIDs = clusterIDs(clusterIDs > 0);

rows = [];

for k = 1:numel(clusterIDs)

    cid = clusterIDs(k);

    for j = 1:nIDs

        id = objectIDs(j);

        count = sum( ...
            clustered.ClusterID == cid & ...
            clustered.ObjectID == id);

        if count > 0
            rows = [rows; cid, id, count];
        end

    end
end

clusterObjectTable = table();

if ~isempty(rows)
    clusterObjectTable.ClusterID = rows(:,1);
    clusterObjectTable.ObjectID = rows(:,2);
    clusterObjectTable.PointCount = rows(:,3);
else
    clusterObjectTable.ClusterID = zeros(0,1);
    clusterObjectTable.ObjectID = zeros(0,1);
    clusterObjectTable.PointCount = zeros(0,1);
end

crossFile = fullfile(dataDir, ...
    "task19_8b_cluster_object_id_breakdown.csv");

writetable(clusterObjectTable,crossFile);

fprintf("\n=== CLUSTER OBJECT ID BREAKDOWN ===\n");
disp(clusterObjectTable);

%% 10. Verify saved outputs

fprintf("\n=== TASK 19.8B COMPLETE ===\n");

fprintf("Tracking CSV saved: %d\n",isfile(summaryFile));
fprintf("Cluster breakdown CSV saved: %d\n",isfile(crossFile));
fprintf("Retention graph saved: %d\n",isfile(graphFile));

fprintf("\nNote: Object IDs identify simulator actors,");
fprintf(" not semantic object classes.\n");
