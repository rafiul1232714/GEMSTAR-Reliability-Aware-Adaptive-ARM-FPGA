%% TASK 24.10.5.3D.1 — TARGET-FOCUSED 3D VISUALIZATION
% Figure 25
% Uses measured GEMSTAR clean V2 LiDAR and Radar data.
% Sensor coordinates are already vehicle-relative.
% No Ground Truth is used for association.
% No original research data is modified.

clear; clc; close all;

%% PATHS

base = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget';

data = fullfile(base,'C02_V2_EKF_Input_53Frames_V1');

out = fullfile(base,'MATLAB_Task24_Analysis');

figdir = fullfile(out,'01_Graphs');

if ~isfolder(figdir)
    mkdir(figdir);
end

output = fullfile(figdir,'Task24_Figure_25.png');

assert(~isfile(output), ...
    'Figure 25 already exists. No overwrite.');

%% REQUIRED INPUTS

files = {
    'lidar_points.csv'
    'radar_returns.csv'
    'lidar_cluster_candidates_v1.csv'
    'lidar_temporal_tracks_v1.csv'
    'radar_track_matches_v1.csv'
};

for k = 1:numel(files)
    assert(isfile(fullfile(data,files{k})), ...
        'Missing input: %s',files{k});
end

%% LOAD TABLES

L = readtable(fullfile(data,'lidar_points.csv'));

R = readtable(fullfile(data,'radar_returns.csv'));

C = readtable(fullfile(data, ...
    'lidar_cluster_candidates_v1.csv'));

T = readtable(fullfile(data, ...
    'lidar_temporal_tracks_v1.csv'));

M = readtable(fullfile(data, ...
    'radar_track_matches_v1.csv'));

%% SELECT THREE CONTROLLED FRAMES

frames = [245 530 816];

f = figure( ...
    'Color','w', ...
    'Position',[50 80 1700 650]);

tiledlayout(1,3, ...
    'TileSpacing','compact', ...
    'Padding','compact');

fprintf('\n=== TASK 24 FIGURE 25 ===\n');

for k = 1:numel(frames)

    frame = frames(k);

    lp = L(L.frame==frame,:);
    rp = R(R.frame==frame,:);
    tp = T(T.frame==frame & T.track_id==2,:);
    mp = M(M.frame==frame & M.track_id==2,:);

    assert(height(tp)==1, ...
        'Track 2 missing at frame %d',frame);

    cluster = C( ...
        C.frame==frame & ...
        C.local_cluster_id==tp.local_cluster_id(1),:);

    assert(height(cluster)==1, ...
        'Matching LiDAR cluster missing at frame %d',frame);

    tx = tp.x_m(1);
    ty = tp.y_m(1);
    tz = tp.z_m(1);

    % Focus on a 12 m by 12 m target neighborhood.
    margin = 6;

    nearbyL = ...
        abs(lp.x_vehicle_m-tx)<=margin & ...
        abs(lp.y_vehicle_m-ty)<=margin & ...
        lp.z_vehicle_m>=-1 & ...
        lp.z_vehicle_m<=5;

    nearbyR = ...
        abs(rp.x_vehicle_m-tx)<=margin & ...
        abs(rp.y_vehicle_m-ty)<=margin & ...
        rp.z_vehicle_m>=-1 & ...
        rp.z_vehicle_m<=5;

    ls = lp(nearbyL,:);
    rs = rp(nearbyR,:);

    nexttile;

    hold on;

    %% LIDAR POINTS

    scatter3( ...
        ls.x_vehicle_m, ...
        ls.y_vehicle_m, ...
        ls.z_vehicle_m, ...
        16,ls.z_vehicle_m,'filled', ...
        'DisplayName','LiDAR points');

    %% NEARBY RADAR RETURNS

    scatter3( ...
        rs.x_vehicle_m, ...
        rs.y_vehicle_m, ...
        rs.z_vehicle_m, ...
        70,[0.9 0.4 0.1],'filled', ...
        'DisplayName','Nearby Radar');

    %% PROVISIONAL RADAR MATCHES TO TRACK 2

    if ~isempty(mp)

        scatter3( ...
            mp.radar_x_m, ...
            mp.radar_y_m, ...
            mp.radar_z_m, ...
            110,'m','filled', ...
            'MarkerEdgeColor','k', ...
            'DisplayName','Radar matched to Track 2');

    end

    %% TRACK CENTER

    scatter3(tx,ty,tz,180,'r','filled', ...
        'MarkerEdgeColor','k', ...
        'DisplayName','Track 2 LiDAR centroid');

    %% LIDAR CLUSTER BOUNDING BOX

    xmin = cluster.min_x_m(1);
    xmax = cluster.max_x_m(1);

    ymin = cluster.min_y_m(1);
    ymax = cluster.max_y_m(1);

    zmin = cluster.min_z_m(1);
    zmax = cluster.max_z_m(1);

    vertices = [
        xmin ymin zmin
        xmax ymin zmin
        xmax ymax zmin
        xmin ymax zmin
        xmin ymin zmax
        xmax ymin zmax
        xmax ymax zmax
        xmin ymax zmax
    ];

    edges = [
        1 2
        2 3
        3 4
        4 1
        5 6
        6 7
        7 8
        8 5
        1 5
        2 6
        3 7
        4 8
    ];

    for e = 1:size(edges,1)

        p1 = vertices(edges(e,1),:);
        p2 = vertices(edges(e,2),:);

        plot3( ...
            [p1(1) p2(1)], ...
            [p1(2) p2(2)], ...
            [p1(3) p2(3)], ...
            'g-','LineWidth',1.8);

    end

    %% LABELS

    xlabel('Vehicle X (m)');
    ylabel('Vehicle Y (m)');
    zlabel('Vehicle Z (m)');

    title(sprintf( ...
        'Frame %d | Radar matches: %d', ...
        frame,height(mp)));

    xlim([tx-margin tx+margin]);
    ylim([ty-margin ty+margin]);
    zlim([-1 5]);

    grid on;
    view(40,25);

    if k == 1
        legend('Location','best');
    end

    %% TERMINAL OUTPUT

    fprintf('\nFRAME=%d\n',frame);

    fprintf('TRACK2_CENTER=(%.4f, %.4f, %.4f)\n', ...
        tx,ty,tz);

    fprintf('LIDAR_POINTS_NEAR_TARGET=%d\n',height(ls));

    fprintf('RADAR_RETURNS_NEAR_TARGET=%d\n',height(rs));

    fprintf('RADAR_TRACK2_ASSOCIATIONS=%d\n',height(mp));

    fprintf('TRACK2_CLUSTER_POINT_COUNT=%d\n', ...
        cluster.point_count(1));

end

sgtitle( ...
    'Figure 25 — Track 2: Local 3D LiDAR and Radar association');

%% SAVE

exportgraphics(f,output,'Resolution',220);

close(f);

fprintf('\n=== FIGURE 25 RESULTS ===\n');

fprintf('OUTPUT=%s\n',output);

fprintf('FRAMES_ANALYZED=3\n');

fprintf('ASSOCIATION_STATUS=PROVISIONAL\n');

fprintf('GROUND_TRUTH_USED_FOR_ASSOCIATION=NO\n');

fprintf('ORIGINAL_FILES_MODIFIED=NO\n');

fprintf('TASK24_MATLAB_FIGURE25_COMPLETE\n');