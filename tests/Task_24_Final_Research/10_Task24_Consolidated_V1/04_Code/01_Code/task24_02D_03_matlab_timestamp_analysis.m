%% Task 24.2.D.3 - GEMSTAR Full-Recording Temporal Analysis
% Source: Actual OSI logger timestamps, 372 paired frames.
% NOTE: Matching logger timestamps do not prove independent
% Camera/LiDAR/Radar acquisition synchronization.

clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research';

csvFile = fullfile(root,'02_CSV_Data', ...
    'task24_02D_02_full_recording_timestamps.csv');

graphDir = fullfile(root,'03_Graphs');

assert(isfile(csvFile),'Timestamp CSV missing');

T = readtable(csvFile,'TextType','string');

assert(height(T)==372,'Expected 372 recorded frames');
assert(all(T.Status=="MATCH"), ...
    'SV-GT timestamp mismatch detected');

assert(all(T.CameraCount==1 & ...
           T.LiDARCount==1 & ...
           T.RadarCount==1), ...
    'Missing or duplicate sensor view detected');

frame = T.Frame;

% Timestamp values are integer nanoseconds.
% Convert to relative seconds for numerical conditioning.
timeSV = double(T.SV_timestamp_ns - T.SV_timestamp_ns(1))/1e9;
timeGT = double(T.GT_timestamp_ns - T.GT_timestamp_ns(1))/1e9;

dt = diff(timeSV)*1000;

assert(all(dt>0),'Non-monotonic timestamps detected');
assert(all(timeSV==timeGT),'SV-GT timestamp mismatch');

%% TIME-01: Timestamp evolution

f1 = figure('Color','w','Position',[80 80 1150 700]);

plot(frame,timeSV,'b-','LineWidth',1.5);
hold on;
plot(frame,timeGT,'r--','LineWidth',1.0);
hold off;

xlabel('Recorded frame index');
ylabel('Elapsed logger time (s)');
title('TIME-01 | GEMSTAR SensorView and GroundTruth timestamps');
legend('SensorView','GroundTruth','Location','northwest');
grid on;

exportgraphics(f1,fullfile(graphDir, ...
    'task24_02D_03_TIME01_timestamps.png'), ...
    'Resolution',200);

%% TIME-02: Frame interval variation

f2 = figure('Color','w','Position',[100 100 1150 700]);

plot(frame(2:end),dt,'k-','LineWidth',1.0);
hold on;
yline(mean(dt),'r--','LineWidth',1.5);
hold off;

xlabel('Recorded frame index');
ylabel('Inter-frame logger interval (ms)');
title('TIME-02 | Variable GEMSTAR recording intervals');
legend('Measured interval','Mean interval','Location','best');
grid on;

exportgraphics(f2,fullfile(graphDir, ...
    'task24_02D_03_TIME02_frame_intervals.png'), ...
    'Resolution',200);

%% TIME-03: Interval distribution

f3 = figure('Color','w','Position',[120 100 1150 700]);

histogram(dt,30,'FaceColor',[0.2 0.5 0.8]);
hold on;
xline(median(dt),'r--','LineWidth',1.5);
hold off;

xlabel('Inter-frame logger interval (ms)');
ylabel('Number of intervals');
title('TIME-03 | Distribution of GEMSTAR logger intervals');
legend('Intervals','Median','Location','best');
grid on;

exportgraphics(f3,fullfile(graphDir, ...
    'task24_02D_03_TIME03_interval_histogram.png'), ...
    'Resolution',200);

%% Print numerical results

fprintf('\n=== TASK 24.2.D.3 MATLAB TEMPORAL ANALYSIS ===\n');
fprintf('FRAME_COUNT=%d\n',height(T));
fprintf('INTERVAL_COUNT=%d\n',numel(dt));
fprintf('DURATION_S=%.6f\n',timeSV(end));
fprintf('MIN_DT_MS=%.6f\n',min(dt));
fprintf('MAX_DT_MS=%.6f\n',max(dt));
fprintf('MEAN_DT_MS=%.6f\n',mean(dt));
fprintf('MEDIAN_DT_MS=%.6f\n',median(dt));
fprintf('STD_DT_MS=%.6f\n',std(dt));
fprintf('AVERAGE_RECORDING_RATE_HZ=%.6f\n',1000/mean(dt));

names = {
    'task24_02D_03_TIME01_timestamps.png'
    'task24_02D_03_TIME02_frame_intervals.png'
    'task24_02D_03_TIME03_interval_histogram.png'
};

for k = 1:numel(names)
    p = fullfile(graphDir,names{k});
    assert(isfile(p),'Missing MATLAB output figure');
    fprintf('FIGURE_CREATED=%s\n',names{k});
end

fprintf('FIGURES_CREATED=3\n');
fprintf('ACQUISITION_SYNCHRONIZATION=NOT_PROVEN\n');
fprintf('TASK24_02D_03_MATLAB_TEMPORAL_ANALYSIS_PASS\n');