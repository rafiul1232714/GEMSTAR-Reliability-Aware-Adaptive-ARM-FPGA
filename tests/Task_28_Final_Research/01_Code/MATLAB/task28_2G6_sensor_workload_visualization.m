% ============================================================
% GEMSTAR TASK 28.2G.6
% Baseline-clear sensor workload and freshness visualization
% ============================================================

clear;
clc;
close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';

task = fullfile(root, 'tests', ...
    'Task_28_Final_Research');

dataDir = fullfile(task, '02_CSV_Data');

plotDir = fullfile(task, '04_Plots', ...
    'Sensor_Workload_Pilot');

if ~exist(plotDir, 'dir')
    mkdir(plotDir);
end

inputFile = fullfile(dataDir, ...
    'task28_2G5_baseline_clear_first100_frames.csv');

assert(isfile(inputFile), ...
    'Task 28.2G.5 CSV file not found.');

T = readtable(inputFile, 'TextType', 'string');

% Convert numeric fields explicitly for reliable MATLAB use.
vars = {'Frame','Timestamp_ns','DT_ms', ...
    'CameraPresent','LiDARPresent','RadarPresent', ...
    'CameraWidth','CameraHeight','CameraBytes', ...
    'LiDARRays','RadarRays', ...
    'CameraPayloadRepeated', ...
    'LiDARPayloadRepeated', ...
    'RadarPayloadRepeated'};

for k = 1:numel(vars)
    name = vars{k};
    if ~isnumeric(T.(name))
        T.(name) = str2double(string(T.(name)));
    end
end

n = height(T);
assert(n > 0, 'No frame records found.');

fprintf('\n========================================\n');
fprintf('TASK 28.2G.6 — SENSOR WORKLOAD ANALYSIS\n');
fprintf('========================================\n');

fprintf('Frames analyzed: %d\n', n);

frame = T.Frame;

cameraMB = T.CameraBytes / 1e6;
lidarRays = T.LiDARRays;
radarRays = T.RadarRays;

dt = T.DT_ms;
validDt = dt(isfinite(dt));

cameraRepeated = sum(T.CameraPayloadRepeated == 1);
lidarRepeated = sum(T.LiDARPayloadRepeated == 1);
radarRepeated = sum(T.RadarPayloadRepeated == 1);

fprintf('\nSENSOR REPEATED PAYLOADS\n');
fprintf('Camera: %d\n', cameraRepeated);
fprintf('LiDAR:  %d\n', lidarRepeated);
fprintf('Radar:  %d\n', radarRepeated);

fprintf('\nSENSOR WORKLOAD\n');
fprintf('Mean Camera bytes/frame: %.2f\n', ...
    mean(T.CameraBytes));
fprintf('Mean LiDAR rays/frame: %.2f\n', ...
    mean(lidarRays));
fprintf('Mean Radar rays/frame: %.2f\n', ...
    mean(radarRays));

if ~isempty(validDt)
    fprintf('\nFRAME TIMING\n');
    fprintf('Mean:   %.4f ms\n', mean(validDt));
    fprintf('Median: %.4f ms\n', median(validDt));
    fprintf('P95:    %.4f ms\n', prctile(validDt,95));
    fprintf('P99:    %.4f ms\n', prctile(validDt,99));
end

%% FIGURE 1 — Camera payload size

f1 = figure('Color','w', ...
    'Name','Camera Workload', ...
    'Position',[100 100 1050 520]);

plot(frame, cameraMB, '-o', 'LineWidth',1.2, ...
    'MarkerSize',3);

grid on;
xlabel('Frame');
ylabel('Camera image payload (MB)');
title('GEMSTAR Clear — Camera Payload Size');

saveFigure(f1, plotDir, ...
    'task28_2G6_camera_workload');

%% FIGURE 2 — LiDAR and Radar workload

f2 = figure('Color','w', ...
    'Name','LiDAR and Radar Workload', ...
    'Position',[120 120 1050 600]);

tiledlayout(2,1);

nexttile;
plot(frame, lidarRays, '-','LineWidth',1.3);
grid on;
ylabel('LiDAR reflections');
title('LiDAR Input Workload');

nexttile;
plot(frame, radarRays, '-','LineWidth',1.3);
grid on;
xlabel('Frame');
ylabel('Radar reflections');
title('Radar Input Workload');

saveFigure(f2, plotDir, ...
    'task28_2G6_lidar_radar_workload');

%% FIGURE 3 — Frame timing

f3 = figure('Color','w', ...
    'Name','Frame Timing', ...
    'Position',[140 140 1050 520]);

plot(frame, dt, '-','LineWidth',1.3);
grid on;

xlabel('Frame');
ylabel('Recorded inter-frame interval (ms)');
title('GEMSTAR Clear — Frame Timing');

if ~isempty(validDt)
    hold on;
    yline(median(validDt),'--','Median');
    yline(prctile(validDt,95),'--','P95');
end

saveFigure(f3, plotDir, ...
    'task28_2G6_frame_timing');

%% FIGURE 4 — Repeated payload occurrence

f4 = figure('Color','w', ...
    'Name','Repeated Sensor Payloads', ...
    'Position',[160 160 1050 570]);

repeatMatrix = [
    T.CameraPayloadRepeated'
    T.LiDARPayloadRepeated'
    T.RadarPayloadRepeated'
];

imagesc(frame, 1:3, repeatMatrix);
colormap(f4, [1 1 1; 0.15 0.45 0.75]);
clim([0 1]);

yticks(1:3);
yticklabels({'Camera','LiDAR','Radar'});
xlabel('Frame');
title('Repeated Serialized Sensor Views');

cb = colorbar;
cb.Ticks = [0 1];
cb.TickLabels = {'Not repeated','Repeated'};

saveFigure(f4, plotDir, ...
    'task28_2G6_repeated_payload_timeline');

%% FIGURE 5 — Summary of repeated payload counts

f5 = figure('Color','w', ...
    'Name','Repeated Payload Summary', ...
    'Position',[180 180 850 520]);

counts = [
    cameraRepeated
    lidarRepeated
    radarRepeated
];

bar(counts);
grid on;

xticks(1:3);
xticklabels({'Camera','LiDAR','Radar'});
ylabel('Repeated adjacent payloads');
title('GEMSTAR Clear — Repeated Payload Summary');

saveFigure(f5, plotDir, ...
    'task28_2G6_repeated_payload_summary');

%% Save numerical summary

metric = [
    "Frames"
    "Camera_mean_bytes"
    "LiDAR_mean_rays"
    "Radar_mean_rays"
    "Camera_repeated"
    "LiDAR_repeated"
    "Radar_repeated"
    "LiDAR_repeated_fraction"
];

value = [
    n
    mean(T.CameraBytes)
    mean(lidarRays)
    mean(radarRays)
    cameraRepeated
    lidarRepeated
    radarRepeated
    lidarRepeated / n
];

summary = table(metric, value);

outputCSV = fullfile(dataDir, ...
    'task28_2G6_pilot_workload_summary.csv');

writetable(summary, outputCSV);

fprintf('\n========================================\n');
fprintf('TASK 28.2G.6 COMPLETE\n');
fprintf('========================================\n');
fprintf('Figures saved: 5 PNG + 5 FIG\n');
fprintf('Output CSV: %s\n', outputCSV);
fprintf('Plots: %s\n', plotDir);
fprintf('All figures displayed in MATLAB.\n');

%% Local helper function
function saveFigure(fig, folder, name)
    savefig(fig, fullfile(folder, name + ".fig"));
    exportgraphics(fig, ...
        fullfile(folder, name + ".png"), ...
        'Resolution',300);
end
