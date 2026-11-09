
%% TASK 11.6A - INDEPENDENT LIDAR OBSTACLE CLUSTERING
% GEMSTAR MOR100 - Frame 150
% No Statistics Toolbox needed.
% No GT or simulator object IDs used for detection.

clc;
clear;
close all;

%% PATHS
root = "E:\GEMSTAR_Project\sensor-health-monitor";
archive = fullfile(root, "tests", "Task_11_Final_Research");

dataDir = fullfile(archive, "02_CSV_Data");
graphDir = fullfile(archive, "01_Graphs");
codeDir = fullfile(archive, "04_Code");
configDir = fullfile(archive, "03_Configurations");

%% LOAD POINTS
L = readtable(fullfile(dataDir, ...
    "task11_lidar_frame150_geometry.csv"));

xyz = [L.x_ego_m, L.y_ego_m, L.z_ego_m];

%% EXPERIMENTAL GROUND REMOVAL
% Keep points more than 15 cm above ego-origin height.
heightThreshold = 0.15;

valid = all(isfinite(xyz), 2);
aboveGround = valid & xyz(:,3) > heightThreshold;

C = L(aboveGround, :);
P = xyz(aboveGround, :);

fprintf('\nTASK 11.6A - INDEPENDENT CLUSTERING\n');
fprintf('All points: %d\n', height(L));
fprintf('Above-height-threshold points: %d\n', height(C));

%% 3D DBSCAN
epsilon = 0.60;
minPoints = 6;

if isempty(P)
    labels = zeros(0,1);
else
    labels = localDBSCAN(P, epsilon, minPoints);
end

C.cluster_id = labels;

ids = unique(labels(labels > 0));

fprintf('Clusters: %d\n', numel(ids));
fprintf('Noise points: %d\n', sum(labels == -1));

%% CLUSTER SUMMARY
cluster_id = [];
point_count = [];
center_x = [];
center_y = [];
center_z = [];
extent_x = [];
extent_y = [];
extent_z = [];

for k = 1:numel(ids)
    id = ids(k);
    Q = P(labels == id, :);

    cluster_id(end+1,1) = id;
    point_count(end+1,1) = size(Q,1);

    center = mean(Q,1);
    extent = max(Q,[],1) - min(Q,[],1);

    center_x(end+1,1) = center(1);
    center_y(end+1,1) = center(2);
    center_z(end+1,1) = center(3);

    extent_x(end+1,1) = extent(1);
    extent_y(end+1,1) = extent(2);
    extent_z(end+1,1) = extent(3);
end

S = table(cluster_id, point_count, ...
    center_x, center_y, center_z, ...
    extent_x, extent_y, extent_z);

disp('===== CLUSTER SUMMARY =====');
disp(S);

%% TOP VIEW
fig1 = figure('Color','w');
hold on;

scatter(L.x_ego_m, L.y_ego_m, ...
    5, [0.8 0.8 0.8], 'filled', ...
    'DisplayName','All LiDAR points');

colors = lines(max(numel(ids),1));

for k = 1:numel(ids)
    idx = labels == ids(k);
    scatter(P(idx,1), P(idx,2), 25, ...
        colors(k,:), 'filled', ...
        'DisplayName',sprintf('Cluster %d',ids(k)));
end

noise = labels == -1;
if any(noise)
    scatter(P(noise,1), P(noise,2), 12, ...
        [0.4 0.4 0.4], 'filled', ...
        'DisplayName','Unclustered candidates');
end

plot(0,0,'ks','MarkerSize',10, ...
    'LineWidth',2,'DisplayName','Ego origin');

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');
title('Frame 150 - Geometry-only LiDAR Clustering');
axis equal;
grid on;
legend('Location','bestoutside');

exportgraphics(fig1, fullfile(graphDir, ...
    'task11_frame150_independent_clusters_top.png'), ...
    'Resolution',300);

savefig(fig1, fullfile(graphDir, ...
    'task11_frame150_independent_clusters_top.fig'));

%% 3D VIEW
fig2 = figure('Color','w');
hold on;

scatter3(xyz(:,1), xyz(:,2), xyz(:,3), ...
    5, [0.8 0.8 0.8], 'filled');

for k = 1:numel(ids)
    idx = labels == ids(k);
    scatter3(P(idx,1),P(idx,2),P(idx,3), ...
        25,colors(k,:),'filled');
end

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');
zlabel('Height Z (m)');
title('Frame 150 - 3D LiDAR Clusters');
grid on;
axis equal;
view(45,25);

exportgraphics(fig2, fullfile(graphDir, ...
    'task11_frame150_independent_clusters_3d.png'), ...
    'Resolution',300);

savefig(fig2, fullfile(graphDir, ...
    'task11_frame150_independent_clusters_3d.fig'));

%% SAVE RESEARCH DATA
writetable(C, fullfile(dataDir, ...
    'task11_frame150_independent_cluster_labels.csv'));

writetable(S, fullfile(dataDir, ...
    'task11_frame150_independent_cluster_summary.csv'));

fid = fopen(fullfile(configDir, ...
    'task11_frame150_independent_clustering_config.txt'),'w');

assert(fid ~= -1, 'Unable to write config file');

fprintf(fid,'Frame=150\n');
fprintf(fid,'HeightThreshold=%.3f\n',heightThreshold);
fprintf(fid,'DBSCAN_Epsilon=%.3f\n',epsilon);
fprintf(fid,'DBSCAN_MinPoints=%d\n',minPoints);
fprintf(fid,'DetectedClusters=%d\n',numel(ids));
fprintf(fid,'GroundRemoval=Height-based, provisional\n');
fprintf(fid,'Coordinates=Provisional ego-local\n');
fprintf(fid,'GroundTruthUsedForDetection=No\n');

fclose(fid);

sourceFile = fullfile(root,'matlab', ...
    'task11_independent_obstacle_clustering.m');

if isfile(sourceFile)
    copyfile(sourceFile,codeDir);
end

fprintf('\nTASK 11.6A COMPLETED\n');

%% CUSTOM 3D DBSCAN
function labels = localDBSCAN(X, eps, minPts)

    n = size(X,1);
    labels = zeros(n,1);
    visited = false(n,1);

    neighbors = cell(n,1);

    for i = 1:n
        d2 = sum((X-X(i,:)).^2,2);
        neighbors{i} = find(d2 <= eps^2);
    end

    clusterNum = 0;

    for i = 1:n
        if visited(i)
            continue;
        end

        visited(i) = true;
        nbr = neighbors{i};

        if numel(nbr) < minPts
            labels(i) = -1;
            continue;
        end

        clusterNum = clusterNum + 1;
        labels(i) = clusterNum;

        queue = nbr(:);
        queued = false(n,1);
        queued(queue) = true;

        head = 1;

        while head <= numel(queue)
            j = queue(head);
            head = head + 1;

            if ~visited(j)
                visited(j) = true;
                nj = neighbors{j};

                if numel(nj) >= minPts
                    add = nj(~queued(nj));
                    queue = [queue; add(:)];
                    queued(add) = true;
                end
            end

            if labels(j) <= 0
                labels(j) = clusterNum;
            end
        end
    end

    labels(labels == 0) = -1;
end
