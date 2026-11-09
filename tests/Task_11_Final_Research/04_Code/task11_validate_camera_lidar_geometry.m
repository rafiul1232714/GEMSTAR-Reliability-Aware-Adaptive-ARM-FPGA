
%% TASK 11.8K - CAMERA / LIDAR GEOMETRY VALIDATION
% GEMSTAR MOR100 - Frame 150
% Evaluate whether projected LiDAR cluster resembles a car.
% Diagnostic only: no validated object-level fusion.

clc;
clear;
close all;

root = "E:\GEMSTAR_Project\sensor-health-monitor";
archive = fullfile(root, "tests", "Task_11_Final_Research");

dataDir = fullfile(archive, "02_CSV_Data");
graphDir = fullfile(archive, "01_Graphs");
findDir = fullfile(archive, "06_Research_Findings");
codeDir = fullfile(archive, "04_Code");

%% 1. LOAD RECORDED DATA

I = imread(fullfile(graphDir, ...
    "task11_mor100_frame0150_camera_0.ppm"));

L = readtable(fullfile(dataDir, ...
    "task11_lidar_frame150_geometry.csv"));

C = readtable(fullfile(dataDir, ...
    "task11_frame150_independent_cluster_labels.csv"));

R = readtable(fullfile(dataDir, ...
    "task11_frame150_radar_cluster_association.csv"));

D = readtable(fullfile(dataDir, ...
    "task11_yolo11s_frame150.csv"));

assert(all(L.frame == 150), "LiDAR frame mismatch");
assert(all(C.frame == 150), "Cluster frame mismatch");
assert(all(R.frame == 150), "Radar frame mismatch");

carMask = strcmpi(string(D.class_name), "car");
assert(any(carMask), "YOLO car detection missing");

car = D(find(carMask,1),:);

bbox = [car.x1, car.y1, car.x2, car.y2];

%% 2. SELECT THE CLUSTER

C = C(C.cluster_id > 0,:);

x = C.x_ego_m;
y = C.y_ego_m;
z = C.z_ego_m;

N = height(C);

xExtent = max(x)-min(x);
yExtent = max(y)-min(y);
zExtent = max(z)-min(z);

meanZ = mean(z);
minZ = min(z);
maxZ = max(z);

ids = unique(C.object_id_diagnostic);

% Height measurements are relative to the provisional
% ego coordinate plane, not a validated ground surface.
lowPoints = z < 0.5;
highPoints = z >= 0.5;

fprintf('\n===== TASK 11.8K GEOMETRY RESULTS =====\n');
fprintf('LiDAR cluster points: %d\n',N);

fprintf('X extent: %.3f m\n',xExtent);
fprintf('Y extent: %.3f m\n',yExtent);
fprintf('Z extent: %.3f m\n',zExtent);

fprintf('Minimum Z: %.3f m\n',minZ);
fprintf('Maximum Z: %.3f m\n',maxZ);
fprintf('Mean Z: %.3f m\n',meanZ);

fprintf('Points below Z=0.5 m: %d\n',sum(lowPoints));
fprintf('Points at/above Z=0.5 m: %d\n',sum(highPoints));

fprintf('Diagnostic object IDs:\n');
disp(ids');

%% 3. CAMERA PROJECTION TEST

W = size(I,2);
H = size(I,1);

fx = W/(2*tand(90/2));
fy = fx;

cx = W/2;
cy = H/2;

camX = 0.70;
camY = 0;
camZ = 1.60;

forward = x-camX;
vertical = z-camZ;

% Test both lateral conventions.
signs = [-1,1];

insideCount = zeros(2,1);
insideLow = zeros(2,1);
insideHigh = zeros(2,1);

figure('Color','w', ...
    'Position',[60 70 1450 760]);

tiledlayout(2,2, ...
    'TileSpacing','compact');

for k = 1:2

    signY = signs(k);

    u = cx + signY*fx.*(y-camY)./forward;
    v = cy - fy.*vertical./forward;

    valid = forward > 0.05 & ...
        isfinite(u) & isfinite(v) & ...
        u >= 0 & u < W & ...
        v >= 0 & v < H;

    inside = valid & ...
        u >= bbox(1) & u <= bbox(3) & ...
        v >= bbox(2) & v <= bbox(4);

    insideCount(k) = sum(inside);
    insideLow(k) = sum(inside & lowPoints);
    insideHigh(k) = sum(inside & highPoints);

    nexttile(k);

    image(I);
    axis image;
    hold on;

    rectangle('Position', ...
        [bbox(1),bbox(2), ...
        bbox(3)-bbox(1),bbox(4)-bbox(2)], ...
        'EdgeColor','g','LineWidth',2);

    scatter(u(valid),v(valid), ...
        16,z(valid),'filled');

    colormap(parula);
    colorbar;
    clim([minZ,maxZ+eps]);

    title(sprintf( ...
        'Y sign %+d | %d/%d cluster points in box', ...
        signY,insideCount(k),N));

    xlabel('Pixel U');
    ylabel('Pixel V');

end

%% 4. CLUSTER GEOMETRY

nexttile(3);

scatter3(x,y,z,18,z,'filled');

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');
zlabel('Z (m)');

title('LiDAR cluster in reconstructed 3D');
grid on;
axis equal;
view(35,25);

%% 5. HEIGHT DISTRIBUTION

nexttile(4);

histogram(z,20);

xlabel('Reconstructed Z (m)');
ylabel('Point count');

title('LiDAR cluster height distribution');
grid on;

sgtitle('Task 11.8K - Camera/LiDAR Geometry Validation');

%% 6. SAVE DATA AND GRAPH

summary = table( ...
    N,xExtent,yExtent,zExtent, ...
    minZ,maxZ,meanZ, ...
    sum(lowPoints),sum(highPoints), ...
    insideCount(1),insideCount(2), ...
    insideLow(1),insideLow(2), ...
    insideHigh(1),insideHigh(2), ...
    'VariableNames',{ ...
    'cluster_points', ...
    'x_extent_m','y_extent_m','z_extent_m', ...
    'min_z_m','max_z_m','mean_z_m', ...
    'below_05m','at_or_above_05m', ...
    'inside_bbox_sign_minus', ...
    'inside_bbox_sign_plus', ...
    'low_inside_minus','low_inside_plus', ...
    'high_inside_minus','high_inside_plus'});

csvFile = fullfile(dataDir, ...
    "task11_frame150_cluster_geometry_validation.csv");

writetable(summary,csvFile);

pngFile = fullfile(graphDir, ...
    "task11_frame150_cluster_geometry_validation.png");

figFile = fullfile(graphDir, ...
    "task11_frame150_cluster_geometry_validation.fig");

exportgraphics(gcf,pngFile,'Resolution',250);
savefig(gcf,figFile);

%% 7. SAVE RESEARCH REPORT

reportFile = fullfile(findDir, ...
    "task11_cluster_geometry_findings.txt");

fid = fopen(reportFile,'w');
assert(fid ~= -1,"Cannot open report");

fprintf(fid,'TASK 11.8K - CLUSTER VALIDATION\n');
fprintf(fid,'Frame: 150\n');
fprintf(fid,'LiDAR points: %d\n',N);
fprintf(fid,'X extent: %.4f m\n',xExtent);
fprintf(fid,'Y extent: %.4f m\n',yExtent);
fprintf(fid,'Z extent: %.4f m\n',zExtent);
fprintf(fid,'Mean Z: %.4f m\n',meanZ);
fprintf(fid,'Points below Z 0.5m: %d\n',sum(lowPoints));

fprintf(fid,'Negative Y sign box overlap: %d\n', ...
    insideCount(1));

fprintf(fid,'Positive Y sign box overlap: %d\n', ...
    insideCount(2));

fprintf(fid,'\nImportant limitations:\n');
fprintf(fid,'Z is provisional ego-frame height.\n');
fprintf(fid,'Object IDs identify simulator diagnostic surfaces.\n');
fprintf(fid,'2D box overlap does not prove object identity.\n');
fprintf(fid,'Sensor extrinsic alignment remains unvalidated.\n');
fprintf(fid,'Car association status: NOT CONFIRMED.\n');

fclose(fid);

%% 8. ARCHIVE MATLAB SCRIPT

source = fullfile(root,"matlab", ...
    "task11_validate_camera_lidar_geometry.m");

if isfile(source)
    copyfile(source,codeDir,'f');
end

%% 9. PRINT SUMMARY

disp(summary);

fprintf('\nSaved CSV: %s\n',csvFile);
fprintf('Saved graph: %s\n',pngFile);

fprintf('\nTASK 11.8K COMPLETED\n');
