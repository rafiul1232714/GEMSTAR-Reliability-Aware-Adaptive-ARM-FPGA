
%% TASK 19.7A - LiDAR DBSCAN Obstacle-Candidate Clustering
% GEMSTAR Camera-LiDAR-Radar Research
% Input: RANSAC non-plane point cloud, frame 150
% Algorithm: DBSCAN-style Euclidean clustering
% No additional toolbox required

clear;
clc;
close all;

%% 1. Project directories

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base, "08_Extracted_PointClouds");
graphDir = fullfile(base, "01_Graphs");
dataDir  = fullfile(base, "02_CSV_Data");

inputFile = fullfile(cloudDir, ...
    "task19_6a_frame150_ransac_nonplane.csv");

assert(isfile(inputFile), ...
    "Input point cloud does not exist: %s", inputFile);

%% 2. Import LiDAR points

T = readtable(inputFile);

P = [T.X, T.Y, T.Z];
N = size(P, 1);

assert(N > 0, "No LiDAR points available.");

fprintf("\n=== TASK 19.7A DBSCAN CLUSTERING ===\n");
fprintf("Input non-plane points: %d\n", N);

%% 3. DBSCAN parameters

epsRadius = 0.60;   % Neighborhood radius in metres
minPts = 5;         % Minimum points, including the center point

fprintf("Neighborhood radius: %.2f m\n", epsRadius);
fprintf("Minimum points: %d\n", minPts);

%% 4. Calculate Euclidean distance matrix

D = zeros(N, N);

for i = 1:N
    delta = P - P(i, :);
    D(i, :) = sqrt(sum(delta.^2, 2))';
end

%% 5. Build neighbor lists

neighbors = cell(N, 1);

for i = 1:N
    neighbors{i} = find(D(i, :) <= epsRadius);
end

%% 6. DBSCAN clustering

labels = zeros(N, 1);
visited = false(N, 1);
clusterID = 0;

for i = 1:N

    if visited(i)
        continue;
    end

    visited(i) = true;
    seeds = neighbors{i};

    if numel(seeds) < minPts
        labels(i) = -1;
        continue;
    end

    clusterID = clusterID + 1;
    labels(i) = clusterID;

    queue = seeds(:);

    inQueue = false(N, 1);
    inQueue(queue) = true;

    head = 1;

    while head <= numel(queue)

        j = queue(head);
        head = head + 1;

        if ~visited(j)

            visited(j) = true;
            newNeighbors = neighbors{j};

            if numel(newNeighbors) >= minPts

                extra = newNeighbors(~inQueue(newNeighbors));

                queue = [queue; extra(:)];
                inQueue(extra) = true;

            end
        end

        % Include reachable border points.
        % A previously marked noise point may become a cluster member.
        if labels(j) <= 0
            labels(j) = clusterID;
        end

    end
end

%% 7. Calculate clustering statistics

noiseCount = sum(labels == -1);
clusteredCount = sum(labels > 0);

clusteredPercent = 100 * clusteredCount / N;
noisePercent = 100 * noiseCount / N;

fprintf("\n=== CLUSTERING RESULTS ===\n");
fprintf("Clusters found: %d\n", clusterID);
fprintf("Clustered points: %d\n", clusteredCount);
fprintf("Noise points: %d\n", noiseCount);
fprintf("Clustered percentage: %.2f%%\n", clusteredPercent);
fprintf("Noise percentage: %.2f%%\n", noisePercent);

assert(clusteredCount + noiseCount == N, ...
    "Clustering labels do not account for all points.");

%% 8. Save labeled points

T.ClusterID = labels;

labeledFile = fullfile(cloudDir, ...
    "task19_7a_frame150_clustered_points.csv");

writetable(T, labeledFile);

%% 9. Calculate cluster centroid statistics

ids = (1:clusterID)';

counts = zeros(clusterID, 1);
centerX = zeros(clusterID, 1);
centerY = zeros(clusterID, 1);
centerZ = zeros(clusterID, 1);

for k = 1:clusterID

    mask = labels == k;

    counts(k) = sum(mask);

    centerX(k) = mean(P(mask, 1));
    centerY(k) = mean(P(mask, 2));
    centerZ(k) = mean(P(mask, 3));

end

%% 10. FIXED: Create cluster summary table
% Assign columns individually to avoid table constructor errors.

clusterSummary = table();

clusterSummary.ClusterID = ids(:);
clusterSummary.PointCount = counts(:);
clusterSummary.CenterX = centerX(:);
clusterSummary.CenterY = centerY(:);
clusterSummary.CenterZ = centerZ(:);

summaryFile = fullfile(dataDir, ...
    "task19_7a_cluster_summary.csv");

writetable(clusterSummary, summaryFile);

%% 11. Create 3D and top-view cluster plots

fig = figure( ...
    "Color", "w", ...
    "Position", [100 100 1150 500], ...
    "Name", "GEMSTAR LiDAR DBSCAN Clustering");

colors = lines(max(clusterID, 1));

% 3D plot
subplot(1, 2, 1);
hold on;

for k = 1:clusterID

    mask = labels == k;

    scatter3( ...
        P(mask, 1), ...
        P(mask, 2), ...
        P(mask, 3), ...
        18, colors(k, :), "filled");

end

maskNoise = labels == -1;

if any(maskNoise)
    scatter3( ...
        P(maskNoise, 1), ...
        P(maskNoise, 2), ...
        P(maskNoise, 3), ...
        22, [0.5 0.5 0.5], "x");
end

xlabel("X - Forward (m)");
ylabel("Y - Lateral (m)");
zlabel("Z - Sensor-local (m)");

title(sprintf("3D Clusters: %d groups", clusterID));

axis equal;
grid on;
view(40, 25);

% Top-view plot
subplot(1, 2, 2);
hold on;

for k = 1:clusterID

    mask = labels == k;

    scatter( ...
        P(mask, 1), ...
        P(mask, 2), ...
        18, colors(k, :), "filled");

end

if any(maskNoise)
    scatter( ...
        P(maskNoise, 1), ...
        P(maskNoise, 2), ...
        22, [0.5 0.5 0.5], "x");
end

xlabel("X - Forward (m)");
ylabel("Y - Lateral (m)");

title("Top View - DBSCAN Cluster Candidates");

axis equal;
grid on;

graphFile = fullfile(graphDir, ...
    "task19_7a_dbscan_clustering.png");

exportgraphics(fig, graphFile, "Resolution", 200);

%% 12. Save overall clustering statistics

overallSummary = table();

overallSummary.Frame = 150;
overallSummary.InputPoints = N;
overallSummary.EpsRadiusM = epsRadius;
overallSummary.MinPts = minPts;
overallSummary.ClusterCount = clusterID;
overallSummary.ClusteredPoints = clusteredCount;
overallSummary.NoisePoints = noiseCount;
overallSummary.ClusteredPercent = clusteredPercent;
overallSummary.NoisePercent = noisePercent;

overallFile = fullfile(dataDir, ...
    "task19_7a_overall_clustering_summary.csv");

writetable(overallSummary, overallFile);

%% 13. Final verification

fprintf("\n=== TASK 19.7A COMPLETE ===\n");

fprintf("Labeled CSV saved: %d\n", isfile(labeledFile));
fprintf("Cluster summary saved: %d\n", isfile(summaryFile));
fprintf("Overall summary saved: %d\n", isfile(overallFile));
fprintf("Graph saved: %d\n", isfile(graphFile));

fprintf("\n=== CLUSTER CENTROIDS ===\n");
disp(clusterSummary);

fprintf("\nResearch outputs saved successfully.\n");
