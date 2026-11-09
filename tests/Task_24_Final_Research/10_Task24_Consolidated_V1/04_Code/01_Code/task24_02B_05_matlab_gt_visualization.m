%% Task 24.2.B.5 - GroundTruth Visualization
% Source: 372_GEMSTAR GroundTruth, first 100 frames
% These are GroundTruth plots, not sensor-fusion estimates.
% Simulation camera actor 77191 is not a physical vehicle target.

clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research';

csvFile = fullfile(root, '02_CSV_Data', ...
    'task24_02B_04_gt_trajectories_100frames.csv');

graphDir = fullfile(root, '03_Graphs');

assert(isfile(csvFile), 'GroundTruth CSV not found.');

T = readtable(csvFile, 'TextType', 'string');

assert(height(T) == 327, 'Unexpected observation count.');
assert(numel(unique(T.Frame)) == 100, ...
    'Unexpected number of frames.');

vehicleIDs = [76895, 76870, 76868, 76865];
vehicleNames = ["Small car", "Truck", "Bus", "Large car"];
rigID = 77191;

colors = lines(4);

fprintf('\n=== TASK 24 MATLAB GROUNDTRUTH ANALYSIS ===\n');
fprintf('Total observations: %d\n', height(T));
fprintf('Vehicle candidate observations: %d\n', ...
    sum(ismember(T.ObjectID, vehicleIDs)));
fprintf('Camera-rig observations: %d\n', sum(T.ObjectID == rigID));

%% Figure GT-01: Vehicle XY trajectories

f1 = figure('Color','w','Position',[100 100 1000 700]);
hold on;

for k = 1:4
    S = sortrows(T(T.ObjectID == vehicleIDs(k), :), 'Frame');

    plot(S.X_m, S.Y_m, '-o', ...
        'Color', colors(k,:), ...
        'LineWidth', 1.6, ...
        'MarkerSize', 3, ...
        'DisplayName', char(vehicleNames(k)));

    scatter(S.X_m(1), S.Y_m(1), 75, ...
        colors(k,:), 'filled', ...
        'HandleVisibility','off');
end

xlabel('World X (m)');
ylabel('World Y (m)');
title('GT-01 | Physical vehicle XY trajectories');
legend('Location','best');
axis equal;
grid on;
hold off;

exportgraphics(f1, fullfile(graphDir, ...
    'task24_02B_05_GT01_vehicle_xy_trajectories.png'), ...
    'Resolution',200);

%% Figure GT-02: Position components versus time

f2 = figure('Color','w','Position',[120 100 1050 850]);
components = {'X_m','Y_m','Z_m'};
axisLabels = {'World X (m)','World Y (m)','World Z (m)'};

for p = 1:3
    subplot(3,1,p);
    hold on;

    for k = 1:4
        S = sortrows(T(T.ObjectID == vehicleIDs(k), :), 'Frame');

        plot(S.Timestamp_s, S.(components{p}), ...
            'Color',colors(k,:), ...
            'LineWidth',1.5, ...
            'DisplayName',char(vehicleNames(k)));
    end

    ylabel(axisLabels{p});
    grid on;

    if p == 1
        title('GT-02 | Vehicle positions over time');
        legend('Location','best');
    end

    if p == 3
        xlabel('Recorded container time (s)');
    end

    hold off;
end

exportgraphics(f2, fullfile(graphDir, ...
    'task24_02B_05_GT02_vehicle_position_time.png'), ...
    'Resolution',200);

%% Figure GT-03: Motion speed and discontinuities

f3 = figure('Color','w','Position',[140 100 1100 670]);
hold on;

for k = 1:4
    S = sortrows(T(T.ObjectID == vehicleIDs(k), :), 'Frame');

    plot(S.Timestamp_s, S.ImpliedSpeed_mps, ...
        'Color',colors(k,:), ...
        'LineWidth',1.5, ...
        'DisplayName',char(vehicleNames(k)));
end

R = sortrows(T(T.ObjectID == rigID, :), 'Frame');

plot(R.Timestamp_s, R.ImpliedSpeed_mps, ...
    '--','Color',[0.3 0.3 0.3], ...
    'LineWidth',1.3, ...
    'DisplayName','FollowVehicleCamera (support actor)');

flagged = R.ImpliedSpeed_mps > 50;

scatter(R.Timestamp_s(flagged), ...
    R.ImpliedSpeed_mps(flagged), ...
    100, 'r', 'x', ...
    'LineWidth',2, ...
    'DisplayName','Rig transition > 50 m/s');

yline(50, ':r', 'Diagnostic threshold', ...
    'HandleVisibility','off');

xlabel('Recorded container time (s)');
ylabel('Frame-to-frame implied speed (m/s)');
title('GT-03 | Motion continuity and flagged transitions');
legend('Location','best');
grid on;
hold off;

exportgraphics(f3, fullfile(graphDir, ...
    'task24_02B_05_GT03_motion_speed_flags.png'), ...
    'Resolution',200);

%% Figure GT-04: Vehicle orientation

f4 = figure('Color','w','Position',[160 100 1050 750]);

subplot(2,1,1);
hold on;

for k = 1:4
    S = sortrows(T(T.ObjectID == vehicleIDs(k), :), 'Frame');
    plot(S.Timestamp_s, rad2deg(S.Yaw_rad), ...
        'Color',colors(k,:), ...
        'LineWidth',1.5, ...
        'DisplayName',char(vehicleNames(k)));
end

title('GT-04 | Recorded vehicle orientation');
ylabel('Yaw (degrees)');
legend('Location','best');
grid on;
hold off;

subplot(2,1,2);
hold on;

for k = 1:4
    S = sortrows(T(T.ObjectID == vehicleIDs(k), :), 'Frame');
    plot(S.Timestamp_s, rad2deg(S.Pitch_rad), ...
        'Color',colors(k,:), ...
        'LineWidth',1.5);
end

xlabel('Recorded container time (s)');
ylabel('Pitch (degrees)');
grid on;
hold off;

exportgraphics(f4, fullfile(graphDir, ...
    'task24_02B_05_GT04_vehicle_orientation.png'), ...
    'Resolution',200);

%% Figure GT-05: Object presence timeline

f5 = figure('Color','w','Position',[180 100 1100 520]);

allIDs = [vehicleIDs, rigID];
labels = {'Small car','Truck','Bus','Large car', ...
    'Follow camera rig'};

presence = zeros(5,100);

for k = 1:5
    frames = T.Frame(T.ObjectID == allIDs(k));
    presence(k,frames+1) = 1;
end

imagesc(0:99,1:5,presence);
colormap([0.93 0.93 0.93; 0.15 0.55 0.80]);
caxis([0 1]);

set(gca,'YTick',1:5,'YTickLabel',labels);
xlabel('Frame index');
ylabel('Object');
title('GT-05 | GroundTruth object presence timeline');

exportgraphics(f5, fullfile(graphDir, ...
    'task24_02B_05_GT05_object_presence.png'), ...
    'Resolution',200);

%% Final verification

outputNames = {
    'task24_02B_05_GT01_vehicle_xy_trajectories.png'
    'task24_02B_05_GT02_vehicle_position_time.png'
    'task24_02B_05_GT03_motion_speed_flags.png'
    'task24_02B_05_GT04_vehicle_orientation.png'
    'task24_02B_05_GT05_object_presence.png'
};

for k = 1:numel(outputNames)
    outputPath = fullfile(graphDir,outputNames{k});
    assert(isfile(outputPath), 'Missing generated figure.');
    info = dir(outputPath);
    assert(info.bytes > 0, 'Empty figure file.');
    fprintf('FIGURE_CREATED=%s\n',outputNames{k});
end

fprintf('VEHICLE_IDS=4\n');
fprintf('SUPPORT_ACTORS=1\n');
fprintf('FIGURES_CREATED=5\n');
fprintf('TASK24_02B_05_MATLAB_VISUALIZATION_PASS\n');