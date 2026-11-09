
%% TASK 11.5E - LIDAR DBSCAN CLUSTERING
% GEMSTAR - Frame 101
% Custom DBSCAN without Statistics Toolbox
% Input: LiDAR non-ground candidate points
% Output: Clusters, graphs and research CSV files

clc;
clear;
close all;

%% 1. DEFINE PROJECT PATHS

root = "E:\GEMSTAR_Project\sensor-health-monitor";

archive = fullfile(root, ...
    "tests", "Task_11_Final_Research");

csvFolder = fullfile(archive, "02_CSV_Data");
graphFolder = fullfile(archive, "01_Graphs");
codeFolder = fullfile(archive, "04_Code");

if ~isfolder(graphFolder)
    mkdir(graphFolder);
end

if ~isfolder(codeFolder)
    mkdir(codeFolder);
end

%% 2. LOAD LIDAR DATA

inputFile = fullfile(csvFolder, ...
    "task11_lidar_normal_classification_frame101.csv");

assert(isfile(inputFile), ...
    "LiDAR classification CSV was not found.");

T = readtable(inputFile);

fprintf('\n====================================\n');
fprintf('TASK 11.5E - LIDAR DBSCAN CLUSTERING\n');
fprintf('====================================\n');

%% 3. SELECT NON-GROUND CANDIDATES

C = T(T.otherCandidate == 1, :);

fprintf('Total candidate points: %d\n', height(C));

assert(height(C) >= 10, ...
    'Not enough points for clustering.');

%% 4. PREPARE XY COORDINATES

XY = [
    C.x_ego_m, ...
    C.y_ego_m
];

% Initial exploratory DBSCAN settings
epsilon = 0.40;
minPoints = 8;

fprintf('DBSCAN epsilon: %.2f m\n', epsilon);
fprintf('DBSCAN minPoints: %d\n', minPoints);

%% 5. RUN OUR CUSTOM DBSCAN

labels = customDBSCAN(XY, epsilon, minPoints);

C.cluster_id = labels;

clusterIDs = unique(labels(labels > 0));

numberOfClusters = numel(clusterIDs);
numberOfNoise = sum(labels == -1);

fprintf('\nClusters detected: %d\n', numberOfClusters);
fprintf('Noise points: %d\n', numberOfNoise);

%% 6. CALCULATE CLUSTER STATISTICS

clusterID = zeros(numberOfClusters, 1);
pointCount = zeros(numberOfClusters, 1);
centerX = zeros(numberOfClusters, 1);
centerY = zeros(numberOfClusters, 1);
centerZ = zeros(numberOfClusters, 1);

xExtent = zeros(numberOfClusters, 1);
yExtent = zeros(numberOfClusters, 1);
zExtent = zeros(numberOfClusters, 1);

for k = 1:numberOfClusters

    id = clusterIDs(k);

    idx = labels == id;

    clusterID(k) = id;

    pointCount(k) = sum(idx);

    centerX(k) = mean(C.x_ego_m(idx));
    centerY(k) = mean(C.y_ego_m(idx));
    centerZ(k) = mean(C.z_ego_m(idx));

    xExtent(k) = ...
        max(C.x_ego_m(idx)) - min(C.x_ego_m(idx));

    yExtent(k) = ...
        max(C.y_ego_m(idx)) - min(C.y_ego_m(idx));

    zExtent(k) = ...
        max(C.z_ego_m(idx)) - min(C.z_ego_m(idx));

end

summary = table( ...
    clusterID, ...
    pointCount, ...
    centerX, ...
    centerY, ...
    centerZ, ...
    xExtent, ...
    yExtent, ...
    zExtent);

fprintf('\n===== CLUSTER SUMMARY =====\n');
disp(summary);

%% 7. GRAPH 1 - TOP-DOWN CLUSTERS

fig1 = figure('Color', 'w', ...
    'Position', [100 100 1050 650]);

hold on;

allLabels = unique(labels);

colors = lines(max(1, numel(allLabels)));

for k = 1:numel(allLabels)

    id = allLabels(k);
    idx = labels == id;

    if id == -1

        scatter( ...
            C.x_ego_m(idx), ...
            C.y_ego_m(idx), ...
            10, [0.6 0.6 0.6], 'filled', ...
            'DisplayName', 'Noise');

    else

        scatter( ...
            C.x_ego_m(idx), ...
            C.y_ego_m(idx), ...
            20, colors(k,:), 'filled', ...
            'DisplayName', ...
            sprintf('Cluster %d', id));

    end

end

plot(0, 0, 'ks', ...
    'MarkerSize', 10, ...
    'LineWidth', 2, ...
    'DisplayName', 'Ego origin');

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');

title('LiDAR DBSCAN Clusters - Frame 101');

axis equal;
grid on;
legend('Location', 'bestoutside');

exportgraphics(fig1, ...
    fullfile(graphFolder, ...
    "task11_lidar_dbscan_clusters.png"), ...
    'Resolution', 300);

savefig(fig1, ...
    fullfile(graphFolder, ...
    "task11_lidar_dbscan_clusters.fig"));

%% 8. GRAPH 2 - 3D CLUSTERS

fig2 = figure('Color', 'w', ...
    'Position', [100 100 1100 750]);

hold on;

for k = 1:numel(allLabels)

    id = allLabels(k);
    idx = labels == id;

    if id == -1

        scatter3( ...
            C.x_ego_m(idx), ...
            C.y_ego_m(idx), ...
            C.z_ego_m(idx), ...
            10, [0.6 0.6 0.6], 'filled', ...
            'DisplayName', 'Noise');

    else

        scatter3( ...
            C.x_ego_m(idx), ...
            C.y_ego_m(idx), ...
            C.z_ego_m(idx), ...
            25, colors(k,:), 'filled', ...
            'DisplayName', ...
            sprintf('Cluster %d', id));

    end

end

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');
zlabel('Height Z (m)');

title('3D LiDAR DBSCAN Clusters - Frame 101');

axis equal;
grid on;
view(45, 25);

legend('Location', 'bestoutside');

exportgraphics(fig2, ...
    fullfile(graphFolder, ...
    "task11_lidar_dbscan_clusters_3d.png"), ...
    'Resolution', 300);

savefig(fig2, ...
    fullfile(graphFolder, ...
    "task11_lidar_dbscan_clusters_3d.fig"));

%% 9. SAVE RESEARCH CSV DATA

labelsFile = fullfile(csvFolder, ...
    "task11_lidar_cluster_labels_frame101.csv");

summaryFile = fullfile(csvFolder, ...
    "task11_lidar_cluster_summary_frame101.csv");

writetable(C, labelsFile);
writetable(summary, summaryFile);

%% 10. SAVE EXPERIMENT PARAMETERS

configFile = fullfile(archive, ...
    "03_Configurations", ...
    "task11_dbscan_parameters.txt");

fid = fopen(configFile, 'w');

assert(fid ~= -1, ...
    'Could not open DBSCAN configuration file.');

fprintf(fid, 'TASK 11.5E - DBSCAN PARAMETERS\n');
fprintf(fid, 'Frame: 101\n');
fprintf(fid, 'Clustering dimensions: XY\n');
fprintf(fid, 'Epsilon: %.2f m\n', epsilon);
fprintf(fid, 'Minimum points: %d\n', minPoints);
fprintf(fid, 'Candidate points: %d\n', height(C));
fprintf(fid, 'Clusters detected: %d\n', numberOfClusters);
fprintf(fid, 'Noise points: %d\n', numberOfNoise);
fprintf(fid, 'Implementation: Custom MATLAB DBSCAN\n');
fprintf(fid, 'Research status: Exploratory clustering\n');

fclose(fid);

%% 11. ARCHIVE MATLAB SOURCE CODE

sourceFile = fullfile(root, ...
    "matlab", "task11_dbscan_clustering.m");

if isfile(sourceFile)

    copyfile(sourceFile, codeFolder);

end

%% 12. FINAL OUTPUT

fprintf('\n====================================\n');
fprintf('TASK 11.5E COMPLETED SUCCESSFULLY\n');
fprintf('====================================\n');

fprintf('Clusters: %d\n', numberOfClusters);
fprintf('Noise points: %d\n', numberOfNoise);
fprintf('CSV files saved in: %s\n', csvFolder);
fprintf('Graphs saved in: %s\n', graphFolder);

%% LOCAL FUNCTION: CUSTOM DBSCAN
% Keep this function at the END of the script.

function labels = customDBSCAN(XY, epsilon, minPoints)

    n = size(XY, 1);

    labels = zeros(n, 1);
    visited = false(n, 1);

    clusterID = 0;

    % Calculate each point's neighboring points.
    neighbors = cell(n, 1);

    for i = 1:n

        dx = XY(:,1) - XY(i,1);
        dy = XY(:,2) - XY(i,2);

        distanceSquared = dx.^2 + dy.^2;

        neighbors{i} = find( ...
            distanceSquared <= epsilon^2);

    end

    % Identify and grow clusters.
    for i = 1:n

        if visited(i)
            continue;
        end

        visited(i) = true;

        nearby = neighbors{i};

        if numel(nearby) < minPoints

            labels(i) = -1;
            continue;

        end

        clusterID = clusterID + 1;
        labels(i) = clusterID;

        queue = nearby(:);

        inQueue = false(n, 1);
        inQueue(queue) = true;

        head = 1;

        while head <= numel(queue)

            j = queue(head);
            head = head + 1;

            if ~visited(j)

                visited(j) = true;

                nearbyJ = neighbors{j};

                if numel(nearbyJ) >= minPoints

                    newPoints = nearbyJ( ...
                        ~inQueue(nearbyJ));

                    queue = [queue; newPoints(:)];

                    inQueue(newPoints) = true;

                end

            end

            % A previously noisy point can become
            % part of a cluster.
            if labels(j) <= 0
                labels(j) = clusterID;
            end

        end

    end

    labels(labels == 0) = -1;

end
