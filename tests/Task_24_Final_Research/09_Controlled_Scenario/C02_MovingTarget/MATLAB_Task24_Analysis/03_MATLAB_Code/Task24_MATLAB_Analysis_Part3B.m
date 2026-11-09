%% TASK 24.10.5.3B - 3D SENSOR VISUALIZATION
% Clean V2 recording - real measured data only.
% All spatial CSV coordinates are already vehicle-relative.
% Association labels remain provisional.
% No original files or estimator states are changed.

clear; clc; close all;

base = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget';
data = fullfile(base, 'C02_V2_EKF_Input_53Frames_V1');
out = fullfile(base, 'MATLAB_Task24_Analysis');
figdir = fullfile(out, '01_Graphs');

if ~isfolder(figdir)
    mkdir(figdir);
end

%% INPUTS

inputNames = {
    'lidar_points.csv'
    'radar_returns.csv'
    'lidar_cluster_candidates_v1.csv'
    'lidar_temporal_tracks_v1.csv'
    'radar_track_matches_v1.csv'
};

for k = 1:numel(inputNames)
    assert(isfile(fullfile(data,inputNames{k})), ...
        'Missing input: %s', inputNames{k});
end

imagePath = fullfile(base, ...
    'Camera_NoVisualizer_V2_2122', ...
    'clean_camera_02_frame00530.png');

detectionPath = fullfile(base, ...
    'C02_V2_Frame0530_Deduplicated_Detections.csv');

assert(isfile(imagePath), 'Missing camera image');
assert(isfile(detectionPath), 'Missing detection CSV');

% Prevent replacement of existing figures.
for k = 13:18
    p = fullfile(figdir, ...
        sprintf('Task24_Figure_%02d.png',k));
    assert(~isfile(p), ...
        'Existing plot; no overwrite: %s',p);
end

%% READ DATA

L = readtable(fullfile(data, ...
    'lidar_points.csv'));

R = readtable(fullfile(data, ...
    'radar_returns.csv'));

C = readtable(fullfile(data, ...
    'lidar_cluster_candidates_v1.csv'));

T = readtable(fullfile(data, ...
    'lidar_temporal_tracks_v1.csv'));

M = readtable(fullfile(data, ...
    'radar_track_matches_v1.csv'));

D = readtable(detectionPath, ...
    'VariableNamingRule','preserve');

I = imread(imagePath);

assert(height(L)==172839,'Unexpected LiDAR row count');
assert(height(R)==3348,'Unexpected Radar row count');
assert(height(M)==670,'Unexpected Radar association count');

fprintf('\n=== TASK 24 MATLAB 3D VISUALIZATION ===\n');

%% FRAME 530 DATA

frame = 530;

lf = L(L.frame==frame,:);
rf = R(R.frame==frame,:);
cf = C(C.frame==frame,:);
mf = M(M.frame==frame,:);

track = T(T.frame==frame & T.track_id==2,:);

assert(height(track)==1, ...
    'Expected one Track 2 observation at frame 530');

tx = track.x_m(1);
ty = track.y_m(1);
tz = track.z_m(1);

fprintf('FRAME530_LIDAR_POINTS=%d\n',height(lf));
fprintf('FRAME530_RADAR_RETURNS=%d\n',height(rf));
fprintf('FRAME530_LIDAR_CLUSTERS=%d\n',height(cf));

fprintf('FRAME530_TRACK2_CENTER=(%.4f,%.4f,%.4f)\n', ...
    tx,ty,tz);

%% FIGURE 13 - 3D LIDAR POINT CLOUD

f = figure('Color','w','Position',[80 80 1200 760]);

scatter3( ...
    lf.x_vehicle_m, ...
    lf.y_vehicle_m, ...
    lf.z_vehicle_m, ...
    7,lf.z_vehicle_m,'filled');

hold on;

scatter3(tx,ty,tz,150,'r','filled', ...
    'MarkerEdgeColor','k');

text(tx,ty,tz+0.8,'Track 2 candidate', ...
    'FontWeight','bold');

scatter3(0,0,0,160,'k','filled');

xlabel('Vehicle X (m)');
ylabel('Vehicle Y (m)');
zlabel('Vehicle Z (m)');

title('Figure 13 - Real 3D LiDAR points, frame 530');

grid on;
axis equal;
view(35,24);
colorbar;

saveas(f,fullfile(figdir,'Task24_Figure_13.png'));
close(f);

%% FIGURE 14 - 3D RADAR RETURNS

f = figure('Color','w','Position',[80 80 1200 760]);

nonzero = abs(rf.doppler_shift_raw)>1e-12;

if any(~nonzero)
    scatter3( ...
        rf.x_vehicle_m(~nonzero), ...
        rf.y_vehicle_m(~nonzero), ...
        rf.z_vehicle_m(~nonzero), ...
        35,[0.5 0.5 0.5],'filled', ...
        'DisplayName','Zero reported Doppler');
    hold on;
end

if any(nonzero)
    scatter3( ...
        rf.x_vehicle_m(nonzero), ...
        rf.y_vehicle_m(nonzero), ...
        rf.z_vehicle_m(nonzero), ...
        70,rf.doppler_shift_raw(nonzero),'filled', ...
        'DisplayName','Nonzero Doppler');
    hold on;
end

scatter3(tx,ty,tz,140,'r','filled', ...
    'DisplayName','LiDAR Track 2 reference');

xlabel('Vehicle X (m)');
ylabel('Vehicle Y (m)');
zlabel('Vehicle Z (m)');

title('Figure 14 - Radar return geometry, frame 530');

legend('Location','best');
grid on;
view(35,22);

saveas(f,fullfile(figdir,'Task24_Figure_14.png'));
close(f);

%% FIGURE 15 - CAMERA + PROJECTED LIDAR

% NOMINAL camera geometry only.
% Camera position was configured approximately as:
% vehicle X=0.7, Y=0, Z=1.6 metres.
%
% This is a geometric diagnostic, not calibrated
% extrinsic or intrinsic sensor fusion.

cameraX = 0.7;
cameraY = 0.0;
cameraZ = 1.6;

[h,w,~] = size(I);

fx = w/2;
fy = w/2;
cx = w/2;
cy = h/2;

X = lf.x_vehicle_m-cameraX;
Y = lf.y_vehicle_m-cameraY;
Z = lf.z_vehicle_m-cameraZ;

valid = isfinite(X) & isfinite(Y) & ...
        isfinite(Z) & X>1;

X = X(valid);
Y = Y(valid);
Z = Z(valid);

u = cx - fx.*Y./X;
v = cy - fy.*Z./X;

inside = u>=1 & u<=w & v>=1 & v<=h;

u = u(inside);
v = v(inside);
depth = X(inside);

f = figure('Color','w','Position',[80 80 1200 760]);

image(I);
axis image;
set(gca,'YDir','reverse');

hold on;

scatter(u,v,9,depth,'filled', ...
    'MarkerFaceAlpha',0.55);

for k = 1:height(D)
    x1 = D.X1(k);
    y1 = D.Y1(k);
    x2 = D.X2(k);
    y2 = D.Y2(k);

    rectangle('Position', ...
        [x1 y1 x2-x1 y2-y1], ...
        'EdgeColor','y','LineWidth',1.8);

    text(x1,max(1,y1-7), ...
        sprintf('%s %.2f', ...
        string(D.RepresentativeClass(k)), ...
        D.Confidence(k)), ...
        'Color','y','FontWeight','bold', ...
        'BackgroundColor','k');
end

title(['Figure 15 - Nominal Camera-LiDAR projection ', ...
       '(uncalibrated), frame 530']);

xlabel('Image X (pixels)');
ylabel('Image Y (pixels)');
colorbar;

saveas(f,fullfile(figdir,'Task24_Figure_15.png'));
close(f);

%% FIGURE 16 - COMBINED 3D SENSOR SCENE

f = figure('Color','w','Position',[80 80 1200 760]);

scatter3( ...
    lf.x_vehicle_m, ...
    lf.y_vehicle_m, ...
    lf.z_vehicle_m, ...
    6,[0.55 0.65 0.8],'filled', ...
    'DisplayName','LiDAR points');

hold on;

scatter3( ...
    rf.x_vehicle_m, ...
    rf.y_vehicle_m, ...
    rf.z_vehicle_m, ...
    45,[0.9 0.35 0.15],'filled', ...
    'DisplayName','All Radar returns');

scatter3(tx,ty,tz,180,'g','filled', ...
    'MarkerEdgeColor','k', ...
    'DisplayName','LiDAR Track 2 candidate');

% Display only truly recorded provisional matches.
m2 = mf(mf.track_id==2,:);
m7 = mf(mf.track_id==7,:);

if ~isempty(m2)
    scatter3( ...
        m2.radar_x_m,m2.radar_y_m,m2.radar_z_m, ...
        100,'m','filled', ...
        'DisplayName','Radar matched to Track 2');
end

if ~isempty(m7)
    scatter3( ...
        m7.radar_x_m,m7.radar_y_m,m7.radar_z_m, ...
        75,'c','filled', ...
        'DisplayName','Radar matched to Track 7');
end

xlabel('Vehicle X (m)');
ylabel('Vehicle Y (m)');
zlabel('Vehicle Z (m)');

title(['Figure 16 - Provisional LiDAR-Radar scene, ', ...
       'frame 530']);

legend('Location','best');
grid on;
axis equal;
view(40,25);

saveas(f,fullfile(figdir,'Task24_Figure_16.png'));
close(f);

%% FIGURE 17 - SPACE-TIME TRACK VISUALIZATION

t2 = T(T.track_id==2,:);
r2 = M(M.track_id==2,:);

[~,order] = sort(t2.time_s);
t2 = t2(order,:);

f = figure('Color','w','Position',[80 80 1200 760]);

plot3( ...
    t2.x_m,t2.y_m,t2.time_s, ...
    '-o','LineWidth',2,'MarkerSize',5, ...
    'DisplayName','LiDAR Track 2');

hold on;

if ~isempty(r2)
    scatter3( ...
        r2.radar_x_m, ...
        r2.radar_y_m, ...
        r2.time_s, ...
        30,'r','filled', ...
        'DisplayName','Provisional Radar matches');
end

xlabel('Vehicle X (m)');
ylabel('Vehicle Y (m)');
zlabel('Recording time (s)');

title('Figure 17 - Track 2 movement through space and time');

legend('Location','best');
grid on;
view(40,25);

saveas(f,fullfile(figdir,'Task24_Figure_17.png'));
close(f);

%% FIGURE 18 - THREE 3D SCENE SNAPSHOTS

frames = [245 530 816];

f = figure('Color','w','Position',[30 80 1600 600]);

tiledlayout(1,3);

for k = 1:numel(frames)
    frameNow = frames(k);

    lp = L(L.frame==frameNow,:);
    rp = R(R.frame==frameNow,:);
    tp = T(T.frame==frameNow & T.track_id==2,:);

    nexttile;

    scatter3( ...
        lp.x_vehicle_m, ...
        lp.y_vehicle_m, ...
        lp.z_vehicle_m, ...
        5,[0.3 0.55 0.8],'filled');

    hold on;

    scatter3( ...
        rp.x_vehicle_m, ...
        rp.y_vehicle_m, ...
        rp.z_vehicle_m, ...
        22,[0.95 0.35 0.15],'filled');

    if height(tp)==1
        scatter3(tp.x_m,tp.y_m,tp.z_m, ...
            110,'g','filled');
    end

    title(sprintf('Frame %d',frameNow));

    xlabel('X (m)');
    ylabel('Y (m)');
    zlabel('Z (m)');

    grid on;
    view(40,22);
end

sgtitle('Figure 18 - LiDAR-Radar 3D scene progression');

saveas(f,fullfile(figdir,'Task24_Figure_18.png'));
close(f);

%% SUMMARY

fprintf('\n=== TASK 24.10.5.3B RESULTS ===\n');

fprintf('TOTAL_LIDAR_POINTS=%d\n',height(L));
fprintf('TOTAL_RADAR_RETURNS=%d\n',height(R));

fprintf('FRAME530_RADAR_TRACK2_MATCHES=%d\n', ...
    height(m2));

fprintf('FRAME530_RADAR_TRACK7_MATCHES=%d\n', ...
    height(m7));

fprintf('FRAME530_PROJECTED_LIDAR_POINTS=%d\n', ...
    numel(u));

fprintf('TRACK2_LIDAR_OBSERVATIONS=%d\n', ...
    height(t2));

fprintf('TRACK2_RADAR_MATCHED_RETURNS=%d\n', ...
    height(r2));

fprintf('NEW_3D_AND_PROJECTION_FIGURES=6\n');

fprintf('CAMERA_CALIBRATED=NO\n');
fprintf('THREE_SENSOR_ASSOCIATION_CONFIRMED=NO\n');
fprintf('GROUND_TRUTH_USED_FOR_FUSION=NO\n');
fprintf('ORIGINAL_DATA_MODIFIED=NO\n');

fprintf('TASK24_MATLAB_PART3B_COMPLETE\n');