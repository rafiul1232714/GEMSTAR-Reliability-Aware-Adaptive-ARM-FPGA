
%% TASK 11.7B - RADAR TO LIDAR CLUSTER ASSOCIATION
% Run after task11_lidar_radar_frame150.m

root = "E:\GEMSTAR_Project\sensor-health-monitor";

csvDir = fullfile(root, "tests", ...
    "Task_11_Final_Research", "02_CSV_Data");

% Select only successfully clustered LiDAR points
Q = L(L.cluster_id > 0, :);

assert(height(Q) > 0, "No LiDAR clusters available.");
assert(height(R) > 0, "No Radar points available.");

% Radar coordinates were calculated in Task 11.7A
radarXY = [R.x_ego_m, R.y_ego_m];
lidarXY = [Q.x_ego_m, Q.y_ego_m];

nearestXY = zeros(height(R), 1);

for i = 1:height(R)

    difference = lidarXY - radarXY(i,:);

    distances = sqrt(sum(difference.^2, 2));

    nearestXY(i) = min(distances);

end

% Provisional association radius: 1 meter
threshold = 1.0;
associated = nearestXY <= threshold;

fprintf('\nTASK 11.7B - ASSOCIATION DIAGNOSTIC\n');

fprintf('LiDAR clustered points: %d\n', height(Q));
fprintf('Radar reflections: %d\n', height(R));

fprintf('Mean nearest XY distance: %.3f m\n', ...
    mean(nearestXY));

fprintf('Minimum nearest XY distance: %.3f m\n', ...
    min(nearestXY));

fprintf('Radar points within 0.5 m: %d\n', ...
    sum(nearestXY <= 0.5));

fprintf('Radar points within 1.0 m: %d\n', ...
    sum(nearestXY <= 1.0));

fprintf('Radar points within 2.0 m: %d\n', ...
    sum(nearestXY <= 2.0));

fprintf('Radar points beyond 2.0 m: %d\n', ...
    sum(nearestXY > 2.0));

% Save for research
R.nearest_cluster_xy_m = nearestXY;
R.provisional_association = associated;

outputFile = fullfile(csvDir, ...
    "task11_frame150_radar_cluster_association.csv");

writetable(R, outputFile);

fprintf('\nSaved: %s\n', outputFile);
fprintf('TASK 11.7B COMPLETED\n');
