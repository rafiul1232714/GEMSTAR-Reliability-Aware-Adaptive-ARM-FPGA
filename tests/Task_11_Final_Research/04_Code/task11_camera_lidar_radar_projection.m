
%% TASK 11.8J - CAMERA / LIDAR / RADAR PROJECTION
% GEMSTAR MOR100, frame 150
% Diagnostic projection with two lateral-axis conventions.
% No object-level fusion claimed.

clc;
clear;
close all;

root = "E:\GEMSTAR_Project\sensor-health-monitor";
archive = fullfile(root, "tests", "Task_11_Final_Research");

csvDir = fullfile(archive, "02_CSV_Data");
graphDir = fullfile(archive, "01_Graphs");
findDir = fullfile(archive, "06_Research_Findings");
codeDir = fullfile(archive, "04_Code");

%% 1 - Load recorded data

I = imread(fullfile(graphDir, ...
    "task11_mor100_frame0150_camera_0.ppm"));

L = readtable(fullfile(csvDir, ...
    "task11_lidar_frame150_geometry.csv"));

C = readtable(fullfile(csvDir, ...
    "task11_frame150_independent_cluster_labels.csv"));

R = readtable(fullfile(csvDir, ...
    "task11_frame150_radar_cluster_association.csv"));

D = readtable(fullfile(csvDir, ...
    "task11_yolo11s_frame150.csv"));

carRows = strcmpi(string(D.class_name), "car");
assert(any(carRows), "No YOLO car detection found.");

car = D(find(carRows,1),:);

bbox = [car.x1 car.y1 car.x2 car.y2];

%% 2 - Camera calibration

W = size(I,2);
H = size(I,1);

fovH = 90;

fx = W / (2*tand(fovH/2));
fy = fx;

cx = W/2;
cy = H/2;

% Camera mounting offset (metres)
camX = 0.70;
camY = 0.0;
camZ = 1.60;

%% 3 - Reconstructed ego-frame data

required = ["x_ego_m","y_ego_m","z_ego_m"];

assert(all(ismember(required, ...
    string(L.Properties.VariableNames))), ...
    "LiDAR geometry columns missing.");

assert(all(ismember(required, ...
    string(C.Properties.VariableNames))), ...
    "LiDAR cluster geometry columns missing.");

assert(all(ismember(required, ...
    string(R.Properties.VariableNames))), ...
    "Radar geometry columns missing.");

lidarXYZ = [L.x_ego_m, L.y_ego_m, L.z_ego_m];

clusterMask = C.cluster_id > 0;

clusterXYZ = [
    C.x_ego_m(clusterMask), ...
    C.y_ego_m(clusterMask), ...
    C.z_ego_m(clusterMask)
];

radarXYZ = [R.x_ego_m, R.y_ego_m, R.z_ego_m];

%% 4 - Test both possible lateral signs

summary = table();

fig = figure('Color','w', ...
    'Position',[60 80 1450 650]);

t = tiledlayout(1,2, ...
    'TileSpacing','compact');

for k = 1:2

    if k == 1
        lateralSign = -1;
        testName = "Y-sign-negative";
    else
        lateralSign = 1;
        testName = "Y-sign-positive";
    end

    [uL,vL,validL] = projectPoints( ...
        lidarXYZ, lateralSign, ...
        camX,camY,camZ,fx,fy,cx,cy,W,H);

    [uC,vC,validC] = projectPoints( ...
        clusterXYZ, lateralSign, ...
        camX,camY,camZ,fx,fy,cx,cy,W,H);

    [uR,vR,validR] = projectPoints( ...
        radarXYZ, lateralSign, ...
        camX,camY,camZ,fx,fy,cx,cy,W,H);

    insideL = inBox(uL,vL,bbox) & validL;
    insideC = inBox(uC,vC,bbox) & validC;
    insideR = inBox(uR,vR,bbox) & validR;

    nexttile(t);

    image(I);
    axis image;
    hold on;

    rectangle('Position', ...
        [bbox(1),bbox(2), ...
        bbox(3)-bbox(1),bbox(4)-bbox(2)], ...
        'EdgeColor','g','LineWidth',2);

    scatter(uL(validL),vL(validL), ...
        7,[0 0.75 1],'filled');

    scatter(uC(validC),vC(validC), ...
        16,[0.1 0.35 1],'filled');

    scatter(uR(validR),vR(validR), ...
        35,[1 0.2 0.1],'filled');

    title(sprintf( ...
        '%s | LiDAR %d, Cluster %d, Radar %d in box', ...
        testName, sum(insideL), ...
        sum(insideC),sum(insideR)));

    xlabel('Image column (px)');
    ylabel('Image row (px)');

    row = table( ...
        string(testName), lateralSign, ...
        sum(validL),sum(validC),sum(validR), ...
        sum(insideL),sum(insideC),sum(insideR), ...
        'VariableNames', { ...
        'test_name','lateral_sign', ...
        'lidar_visible','cluster_visible','radar_visible', ...
        'lidar_in_box','cluster_in_box','radar_in_box'});

    summary = [summary;row];

end

sgtitle('GEMSTAR Frame 150 - Provisional Cross-Sensor Projection');

%% 5 - Save results

pngFile = fullfile(graphDir, ...
    "task11_frame150_projection_comparison.png");

figFile = fullfile(graphDir, ...
    "task11_frame150_projection_comparison.fig");

csvFile = fullfile(csvDir, ...
    "task11_frame150_projection_comparison.csv");

exportgraphics(fig,pngFile,'Resolution',200);
savefig(fig,figFile);
writetable(summary,csvFile);

%% 6 - Save limitations and source

report = fullfile(findDir, ...
    "task11_projection_limitations.txt");

fid = fopen(report,'w');

fprintf(fid,'TASK 11.8J - PROJECTION DIAGNOSTIC\n');
fprintf(fid,'Frame: 150\n');
fprintf(fid,'Camera FOV horizontal: 90 degrees\n');
fprintf(fid,'Assumed fx=fy=320 px\n');
fprintf(fid,'Camera mount: (0.7,0,1.6) metres\n');
fprintf(fid,'Testing both lateral-axis signs.\n');
fprintf(fid,'No lens distortion model applied.\n');
fprintf(fid,'No occlusion handling or per-ray visibility check.\n');
fprintf(fid,'3D geometry reconstruction remains provisional.\n');
fprintf(fid,'Bounding-box overlap is NOT object identification.\n');
fprintf(fid,'Actual camera extrinsic transform is not independently validated.\n');

fclose(fid);

source = fullfile(root,"matlab", ...
    "task11_camera_lidar_radar_projection.m");

if isfile(source)
    copyfile(source,codeDir,'f');
end

disp("===== TASK 11.8J RESULTS =====");
disp(summary);

fprintf("Saved image: %s\n",pngFile);
fprintf("Saved CSV: %s\n",csvFile);

%% LOCAL FUNCTIONS

function [u,v,valid] = projectPoints( ...
    xyz, lateralSign, ...
    camX,camY,camZ,fx,fy,cx,cy,W,H)

    forward = xyz(:,1)-camX;
    lateral = xyz(:,2)-camY;
    vertical = xyz(:,3)-camZ;

    u = cx + lateralSign*fx.*lateral./forward;
    v = cy - fy.*vertical./forward;

    valid = forward > 0.05 & ...
        isfinite(u) & isfinite(v) & ...
        u >= 0 & u < W & ...
        v >= 0 & v < H;
end

function mask = inBox(u,v,bbox)
    mask = u >= bbox(1) & ...
        u <= bbox(3) & ...
        v >= bbox(2) & ...
        v <= bbox(4);
end
