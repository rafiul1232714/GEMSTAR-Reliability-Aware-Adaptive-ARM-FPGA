%% TASK 24.3.8.D — LiDAR-Radar Geometric Visualization
% Recorded GEMSTAR sensor measurements.
% Coordinate convention: nominal vehicle OSI frame.
% Plane labels: provisional RANSAC classifications.
% No privileged object identities used.
% Spatial proximity does not establish object correspondence.

clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research';

inputFile = fullfile(root,'02_CSV_Data', ...
    'task24_03_08C_matlab_lidar_radar_geometry.csv');

graphDir = fullfile(root,'03_Graphs');

assert(isfile(inputFile),'Visualization CSV missing');
assert(isfolder(graphDir),'Graph directory missing');

T = readtable(inputFile,'TextType','string');

assert(height(T)==8434,'Unexpected total measurement count');

frames = [2 172 311 355];

expectedLidar = [2068 2044 2008 2045];
expectedRadar = [58 57 70 84];
expectedAbove = [151 218 0 0];

% Consistent category colors across all figures.
cPlane = [0.55 0.60 0.65];
cAbove = [0.95 0.35 0.15];
cBelow = [0.20 0.65 0.85];
cRadar = [0.55 0.20 0.85];

outputNames = strings(4,1);

for k = 1:numel(frames)

    frame = frames(k);

    S = T(T.Frame==frame,:);

    isLidar = S.Sensor=="LiDAR";
    isRadar = S.Sensor=="Radar";

    isPlane = isLidar & S.PlaneRegion=="PLANE_INLIER";
    isAbove = isLidar & S.PlaneRegion=="ABOVE_PLANE";
    isBelow = isLidar & S.PlaneRegion=="BELOW_PLANE";

    assert(sum(isLidar)==expectedLidar(k));
    assert(sum(isRadar)==expectedRadar(k));
    assert(sum(isAbove)==expectedAbove(k));

    assert(sum(isPlane | isAbove | isBelow)==sum(isLidar));

    masks = {isPlane,isBelow,isAbove,isRadar};
    colors = {cPlane,cBelow,cAbove,cRadar};
    labels = {'LiDAR plane inliers', ...
              'LiDAR below plane', ...
              'LiDAR above plane', ...
              'Radar candidates'};

    pointSizes = [8 18 24 40];

    filename = sprintf( ...
        'task24_03_08D_geometry_frame%03d.png',frame);

    destination = fullfile(graphDir,filename);

    assert(~isfile(destination), ...
        'Refusing to overwrite existing research figure');

    fig = figure('Color','w', ...
        'Position',[60 60 1450 1000], ...
        'Name',sprintf('GEMSTAR Frame %d',frame));

    layout = tiledlayout(fig,2,2, ...
        'TileSpacing','compact', ...
        'Padding','compact');

    % --------- Top view: X and Y ---------
    ax1 = nexttile(layout,1);
    hold(ax1,'on');

    handles = gobjects(4,1);

    for j=1:4
        mask = masks{j};

        handles(j) = scatter(ax1, ...
            S.X_m(mask),S.Y_m(mask), ...
            pointSizes(j),colors{j},'filled', ...
            'DisplayName',labels{j});
    end

    plot(ax1,0,0,'kp','MarkerSize',11, ...
        'MarkerFaceColor','k', ...
        'HandleVisibility','off');

    xlabel(ax1,'Forward X (m)');
    ylabel(ax1,'Lateral Y (m)');
    title(ax1,'Top view — XY');
    grid(ax1,'on');
    axis(ax1,'equal');
    xlim(ax1,[-2 52]);
    ylim(ax1,[-22 22]);

    legend(ax1,handles,labels, ...
        'Location','best','FontSize',8);

    % --------- Side view: X and Z ---------
    ax2 = nexttile(layout,2);
    hold(ax2,'on');

    for j=1:4
        mask = masks{j};

        scatter(ax2,S.X_m(mask),S.Z_m(mask), ...
            pointSizes(j),colors{j},'filled');
    end

    xlabel(ax2,'Forward X (m)');
    ylabel(ax2,'Height Z (m)');
    title(ax2,'Side view — XZ');
    grid(ax2,'on');
    xlim(ax2,[-2 52]);
    ylim(ax2,[-1 5]);

    % --------- Cross-sectional view: Y and Z ---------
    ax3 = nexttile(layout,3);
    hold(ax3,'on');

    for j=1:4
        mask = masks{j};

        scatter(ax3,S.Y_m(mask),S.Z_m(mask), ...
            pointSizes(j),colors{j},'filled');
    end

    xlabel(ax3,'Lateral Y (m)');
    ylabel(ax3,'Height Z (m)');
    title(ax3,'Cross-section — YZ');
    grid(ax3,'on');
    xlim(ax3,[-22 22]);
    ylim(ax3,[-1 5]);

    % --------- 3D point-cloud view ---------
    ax4 = nexttile(layout,4);
    hold(ax4,'on');

    for j=1:4
        mask = masks{j};

        scatter3(ax4, ...
            S.X_m(mask),S.Y_m(mask),S.Z_m(mask), ...
            pointSizes(j),colors{j},'filled');
    end

    plot3(ax4,0,0,0,'kp','MarkerSize',11, ...
        'MarkerFaceColor','k');

    xlabel(ax4,'Forward X (m)');
    ylabel(ax4,'Lateral Y (m)');
    zlabel(ax4,'Height Z (m)');

    title(ax4,'3D point-cloud view');

    grid(ax4,'on');
    view(ax4,35,25);
    xlim(ax4,[-2 52]);
    ylim(ax4,[-22 22]);
    zlim(ax4,[-1 5]);

    sgtitle(layout,sprintf( ...
        ['GEMSTAR Frame %d | LiDAR %d | Radar %d | ' ...
         'Above-plane %d'], ...
        frame,sum(isLidar),sum(isRadar),sum(isAbove)), ...
        'FontWeight','bold');

    exportgraphics(fig,destination,'Resolution',200);

    assert(isfile(destination), ...
        'MATLAB figure export failed');

    info = dir(destination);
    assert(info.bytes>0,'Exported figure is empty');

    outputNames(k) = string(filename);

    fprintf( ...
        'FRAME=%d LIDAR=%d PLANE=%d ABOVE=%d BELOW=%d RADAR=%d\n', ...
        frame,sum(isLidar),sum(isPlane), ...
        sum(isAbove),sum(isBelow),sum(isRadar));

    fprintf('FIGURE_CREATED=%s\n',filename);
    fprintf('FIGURE_BYTES=%d\n',info.bytes);
end

fprintf('\n=== TASK 24.3.8.D MATLAB GEOMETRY ANALYSIS ===\n');
fprintf('FRAMES_ANALYZED=%d\n',numel(frames));
fprintf('TOTAL_MEASUREMENTS=%d\n',height(T));
fprintf('TOTAL_LIDAR=%d\n',sum(expectedLidar));
fprintf('TOTAL_RADAR=%d\n',sum(expectedRadar));
fprintf('TOTAL_ABOVE_PLANE=%d\n',sum(expectedAbove));
fprintf('FIGURES_CREATED=%d\n',numel(outputNames));
fprintf('GEOMETRY=NOMINAL_UNCALIBRATED\n');
fprintf('OBJECT_ASSOCIATION=NOT_CONFIRMED\n');
fprintf('GROUNDTRUTH_IDENTITIES_USED=NO\n');
fprintf('RAW_OSI_MODIFIED=NO\n');
fprintf('TASK24_03_08D_MATLAB_VISUALIZATION_PASS\n');