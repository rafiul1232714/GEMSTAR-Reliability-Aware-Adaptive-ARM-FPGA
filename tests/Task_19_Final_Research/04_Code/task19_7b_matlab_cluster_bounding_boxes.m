
%% TASK 19.7B - LiDAR Cluster Bounding Boxes and Features
% GEMSTAR research - frame 150
% Input: Task 19.7A DBSCAN labeled points
% No additional toolbox required

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base, "08_Extracted_PointClouds");
graphDir = fullfile(base, "01_Graphs");
dataDir  = fullfile(base, "02_CSV_Data");

inputFile = fullfile(cloudDir, ...
    "task19_7a_frame150_clustered_points.csv");

assert(isfile(inputFile), "Clustered CSV not found.");

%% 2. Load clustered points

T = readtable(inputFile);

clusterIDs = unique(T.ClusterID);
clusterIDs = clusterIDs(clusterIDs > 0);

nClusters = numel(clusterIDs);

fprintf("\n=== TASK 19.7B CLUSTER GEOMETRY ===\n");
fprintf("Input points: %d\n", height(T));
fprintf("Clusters: %d\n", nClusters);

%% 3. Initialize results

features = table();

features.ClusterID = clusterIDs(:);
features.PointCount = zeros(nClusters,1);

features.CenterX = zeros(nClusters,1);
features.CenterY = zeros(nClusters,1);
features.CenterZ = zeros(nClusters,1);

features.MinX = zeros(nClusters,1);
features.MaxX = zeros(nClusters,1);
features.MinY = zeros(nClusters,1);
features.MaxY = zeros(nClusters,1);
features.MinZ = zeros(nClusters,1);
features.MaxZ = zeros(nClusters,1);

features.LengthX = zeros(nClusters,1);
features.WidthY = zeros(nClusters,1);
features.HeightZ = zeros(nClusters,1);

features.DistanceToCenterM = zeros(nClusters,1);
features.BoundingBoxVolumeM3 = zeros(nClusters,1);
features.PointsPerM3 = zeros(nClusters,1);

%% 4. Compute bounding boxes and features

for k = 1:nClusters

    id = clusterIDs(k);
    mask = T.ClusterID == id;

    P = [T.X(mask), T.Y(mask), T.Z(mask)];

    pMin = min(P,[],1);
    pMax = max(P,[],1);
    center = mean(P,1);

    dimensions = pMax - pMin;
    volume = prod(dimensions);

    features.PointCount(k) = size(P,1);

    features.CenterX(k) = center(1);
    features.CenterY(k) = center(2);
    features.CenterZ(k) = center(3);

    features.MinX(k) = pMin(1);
    features.MaxX(k) = pMax(1);
    features.MinY(k) = pMin(2);
    features.MaxY(k) = pMax(2);
    features.MinZ(k) = pMin(3);
    features.MaxZ(k) = pMax(3);

    features.LengthX(k) = dimensions(1);
    features.WidthY(k) = dimensions(2);
    features.HeightZ(k) = dimensions(3);

    features.DistanceToCenterM(k) = norm(center);

    features.BoundingBoxVolumeM3(k) = volume;

    if volume > 1e-9
        features.PointsPerM3(k) = size(P,1)/volume;
    else
        features.PointsPerM3(k) = NaN;
    end
end

%% 5. Display numerical features

disp(features(:, { ...
    'ClusterID', ...
    'PointCount', ...
    'LengthX', ...
    'WidthY', ...
    'HeightZ', ...
    'DistanceToCenterM'}));

%% 6. Save features CSV

featureFile = fullfile(dataDir, ...
    "task19_7b_cluster_geometric_features.csv");

writetable(features, featureFile);

%% 7. Visualize 3D bounding boxes

fig = figure("Color","w", ...
    "Position",[100 100 1050 650], ...
    "Name","GEMSTAR LiDAR Bounding Boxes");

hold on;

colors = lines(max(nClusters,1));

for k = 1:nClusters

    id = clusterIDs(k);
    mask = T.ClusterID == id;

    scatter3(T.X(mask),T.Y(mask),T.Z(mask), ...
        20,colors(k,:),"filled");

    xmin = features.MinX(k);
    xmax = features.MaxX(k);
    ymin = features.MinY(k);
    ymax = features.MaxY(k);
    zmin = features.MinZ(k);
    zmax = features.MaxZ(k);

    corners = [
        xmin ymin zmin;
        xmax ymin zmin;
        xmax ymax zmin;
        xmin ymax zmin;
        xmin ymin zmax;
        xmax ymin zmax;
        xmax ymax zmax;
        xmin ymax zmax
    ];

    edges = [
        1 2; 2 3; 3 4; 4 1;
        5 6; 6 7; 7 8; 8 5;
        1 5; 2 6; 3 7; 4 8
    ];

    for e = 1:size(edges,1)
        a = corners(edges(e,1),:);
        b = corners(edges(e,2),:);

        plot3([a(1),b(1)], ...
              [a(2),b(2)], ...
              [a(3),b(3)], ...
              "k-","LineWidth",1.5);
    end

    text(features.CenterX(k), ...
         features.CenterY(k), ...
         features.CenterZ(k), ...
         sprintf("Cluster %d",id), ...
         "FontWeight","bold");
end

xlabel("X - Forward (m)");
ylabel("Y - Lateral (m)");
zlabel("Z - Sensor-local (m)");

title("GEMSTAR LiDAR - Cluster Bounding Boxes");

axis equal;
grid on;
view(40,25);

graphFile = fullfile(graphDir, ...
    "task19_7b_cluster_bounding_boxes.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 8. Save geometry summary

fprintf("\n=== TASK 19.7B COMPLETE ===\n");

fprintf("Feature CSV saved: %d\n",isfile(featureFile));
fprintf("Bounding-box graph saved: %d\n",isfile(graphFile));

for k = 1:nClusters
    fprintf("\nCluster %d:\n",features.ClusterID(k));
    fprintf("  Points: %d\n",features.PointCount(k));
    fprintf("  Length X: %.3f m\n",features.LengthX(k));
    fprintf("  Width Y: %.3f m\n",features.WidthY(k));
    fprintf("  Height Z: %.3f m\n",features.HeightZ(k));
    fprintf("  Center distance: %.3f m\n", ...
        features.DistanceToCenterM(k));
end
