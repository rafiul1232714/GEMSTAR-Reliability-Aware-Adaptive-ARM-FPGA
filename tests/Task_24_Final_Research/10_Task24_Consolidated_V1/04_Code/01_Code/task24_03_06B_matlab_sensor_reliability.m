%% Task 24.3.6.B — Full GEMSTAR Sensor Reliability Analysis
% 372 recorded frames.
% Measurements are real GEMSTAR OSI outputs.
% Freshness is based on exact recorded-content comparison,
% not independently verified acquisition timestamps.

clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research';

csvFile = fullfile(root,'02_CSV_Data', ...
    'task24_03_06A_full_sensor_frame_summary.csv');

graphDir = fullfile(root,'03_Graphs');

assert(isfile(csvFile),'Frame summary CSV missing');

T = readtable(csvFile,'TextType','string');

assert(height(T)==372,'Expected 372 frames');
assert(isequal(T.Frame,(0:371)'), ...
    'Unexpected frame indexing');

frame = T.Frame;

lidarCount = T.LiDARCandidates;
radarCount = T.RadarCandidates;

lidarRepeated = double(T.LiDARFreshness=="REPEATED");
radarRepeated = double(T.RadarFreshness=="REPEATED");

hostAvailable = double(T.HostPoseAvailable);
allZeroDoppler = double(T.RadarExactZeroDopplerCandidates == ...
    T.RadarCandidates & T.RadarCandidates>0);

extremeDoppler = T.RadarExtremeDopplerCandidates;

assert(sum(lidarCount)==823254);
assert(sum(radarCount)==24161);
assert(sum(lidarRepeated)==148);
assert(sum(radarRepeated)==57);
assert(sum(allZeroDoppler)==149);
assert(sum(extremeDoppler)==58);
assert(sum(hostAvailable)==355);

%% SEN-01 — Candidate return counts

f1 = figure('Color','w','Position',[60 60 1200 750]);

yyaxis left;
plot(frame,lidarCount,'LineWidth',1.3);
ylabel('LiDAR candidate returns per frame');

yyaxis right;
plot(frame,radarCount,'LineWidth',1.3);
ylabel('Radar candidate returns per frame');

xlabel('Recorded frame index');
title('SEN-01 | LiDAR and Radar candidate return counts');
grid on;

exportgraphics(f1,fullfile(graphDir, ...
    'task24_03_06B_SEN01_candidate_counts.png'), ...
    'Resolution',200);

%% SEN-02 — Payload freshness status

f2 = figure('Color','w','Position',[80 80 1200 650]);

hold on;

stairs(frame,lidarRepeated+1,'LineWidth',1.3);
stairs(frame,radarRepeated+3,'LineWidth',1.3);

yline(2.5,'k:');

yticks([1 2 3 4]);
yticklabels({
    'LiDAR changed','LiDAR repeated', ...
    'Radar changed','Radar repeated'
});

xlabel('Recorded frame index');
ylabel('Recorded payload status');
title('SEN-02 | Sensor payload repetition versus frame index');

ylim([0.5 4.5]);
grid on;
hold off;

exportgraphics(f2,fullfile(graphDir, ...
    'task24_03_06B_SEN02_payload_freshness.png'), ...
    'Resolution',200);

%% SEN-03 — Radar Doppler anomalies

f3 = figure('Color','w','Position',[100 100 1200 750]);

hold on;

plot(frame,T.RadarMaxAbsRadialVelocity_mps, ...
    'LineWidth',1.3);

yline(70,'r--','Diagnostic review threshold: 70 m/s');

scatter(frame(extremeDoppler>0), ...
    T.RadarMaxAbsRadialVelocity_mps(extremeDoppler>0), ...
    90,'r','filled');

xlabel('Recorded frame index');
ylabel('Maximum |radial velocity| (m/s)');
title('SEN-03 | Radar velocity magnitude and extreme-value flags');

grid on;
hold off;

exportgraphics(f3,fullfile(graphDir, ...
    'task24_03_06B_SEN03_radar_doppler_anomalies.png'), ...
    'Resolution',200);

%% SEN-04 — Combined reliability timeline

f4 = figure('Color','w','Position',[120 100 1300 750]);

images = [
    lidarRepeated';
    radarRepeated';
    allZeroDoppler';
    (1-hostAvailable)';
    double(frame'>=311)
];

imagesc(frame,1:5,images);
colormap([0.9 0.95 0.9; 0.92 0.35 0.25]);
caxis([0 1]);

yticks(1:5);
yticklabels({
    'LiDAR payload repeated'
    'Radar payload repeated'
    'Radar all-zero Doppler'
    'Embedded host pose missing'
    'Long interval regime'
});

xlabel('Recorded frame index');
title('SEN-04 | GEMSTAR sensor reliability and timing timeline');

xlim([-0.5 371.5]);
colorbar;
grid on;

exportgraphics(f4,fullfile(graphDir, ...
    'task24_03_06B_SEN04_reliability_timeline.png'), ...
    'Resolution',200);

%% Verify the four generated figures

names = {
    'task24_03_06B_SEN01_candidate_counts.png'
    'task24_03_06B_SEN02_payload_freshness.png'
    'task24_03_06B_SEN03_radar_doppler_anomalies.png'
    'task24_03_06B_SEN04_reliability_timeline.png'
};

for k = 1:numel(names)
    path = fullfile(graphDir,names{k});
    assert(isfile(path),'Missing generated figure');
    assert(dir(path).bytes>0,'Empty generated figure');
    fprintf('FIGURE_CREATED=%s\n',names{k});
end

fprintf('\n=== TASK 24.3.6.B MATLAB SENSOR ANALYSIS ===\n');
fprintf('FRAMES=%d\n',height(T));
fprintf('LIDAR_CANDIDATES=%d\n',sum(lidarCount));
fprintf('RADAR_CANDIDATES=%d\n',sum(radarCount));
fprintf('LIDAR_REPEATED_FRAMES=%d\n',sum(lidarRepeated));
fprintf('RADAR_REPEATED_FRAMES=%d\n',sum(radarRepeated));
fprintf('RADAR_ALL_ZERO_FRAMES=%d\n',sum(allZeroDoppler));
fprintf('RADAR_EXTREME_RETURNS=%d\n',sum(extremeDoppler));
fprintf('HOST_AVAILABLE_FRAMES=%d\n',sum(hostAvailable));
fprintf('FIGURES_CREATED=4\n');
fprintf('FRESHNESS_MEANS_EXACT_CONTENT_COMPARISON\n');
fprintf('TASK24_03_06B_MATLAB_SENSOR_ANALYSIS_PASS\n');