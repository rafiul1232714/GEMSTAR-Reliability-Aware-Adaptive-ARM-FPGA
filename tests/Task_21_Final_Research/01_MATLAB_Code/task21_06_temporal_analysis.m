%% TASK 21.6 - RADAR TEMPORAL ANALYSIS
clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';
task = fullfile(root,'tests','Task_21_Final_Research');

inputDir = fullfile(task,'02_Imported_Data');
graphDir = fullfile(task,'03_Graphs');
csvDir = fullfile(task,'04_CSV_Results');
findingDir = fullfile(task,'06_Research_Findings');

source = fullfile(inputDir, ...
    'task20_49_50m_radar_returns.mat');

if ~isfile(source)
    error('Task 21.2 radar MAT dataset missing.');
end

S = load(source,'T');
T = S.T;

frame = double(T.Frame);
range = double(T.RangeM);
signal = double(T.SignalStrength);

% Exclude frame zero and invalid measurements.
valid = frame >= 1 & frame <= 99 & ...
    isfinite(frame) & ...
    isfinite(range) & ...
    isfinite(signal) & ...
    range > 0 & range <= 50.01;

frame = frame(valid);
range = range(valid);
signal = signal(valid);

if isempty(frame)
    error('No valid radar records remain.');
end

fprintf('\n=== TASK 21.6 TEMPORAL ANALYSIS ===\n');

fprintf('Analyzed candidate returns: %d\n',numel(range));

% Include every expected frame, even if it has zero returns.
frames = (1:99)';
counts = zeros(99,1);
beyond10 = zeros(99,1);
medianRange = NaN(99,1);
maxRange = NaN(99,1);
meanSignal = NaN(99,1);

for k = 1:numel(frames)

    idx = frame == frames(k);
    values = range(idx);
    strengths = signal(idx);

    counts(k) = nnz(idx);
    beyond10(k) = nnz(values > 10);

    if ~isempty(values)
        medianRange(k) = median(values);
        maxRange(k) = max(values);
        meanSignal(k) = mean(strengths);
    end
end

% Descriptive changes between consecutive frames.
countChange = [NaN; diff(counts)];
absCountChange = abs(countChange);

medianStepChange = [NaN; abs(diff(medianRange))];

% Flag exceptionally large return-count jumps for inspection.
% This is a descriptive threshold, not a fault detector.
jumpThreshold = max(10, 2*std(diff(counts)));
largeJump = false(99,1);
largeJump(2:end) = abs(diff(counts)) > jumpThreshold;

%% SAVE FRAME STATISTICS

frameTable = table( ...
    frames,counts,beyond10,medianRange,maxRange, ...
    meanSignal,countChange,absCountChange, ...
    medianStepChange,largeJump, ...
    'VariableNames', { ...
    'Frame','ReturnCount','ReturnsBeyond10m', ...
    'MedianRangeM','MaximumRangeM', ...
    'MeanSignalStrength','ReturnCountChange', ...
    'AbsoluteCountChange','MedianRangeStepChangeM', ...
    'LargeCountJumpFlag'});

csvPath = fullfile(csvDir, ...
    'task21_06_frame_temporal_statistics.csv');

writetable(frameTable,csvPath);

%% GRAPH 1 - RETURNS OVER TIME

f1 = figure('Visible','off','Color','w', ...
    'Position',[100 100 1050 620]);

plot(frames,counts,'LineWidth',1.5);
hold on;
plot(frames,beyond10,'LineWidth',1.5);

xlabel('GEMSTAR frame index');
ylabel('Candidate radar returns');
title('Radar return counts across frames 1-99');
legend('All returns','Returns beyond 10 m', ...
    'Location','best');
grid on;

plot1 = fullfile(graphDir, ...
    'task21_06_temporal_return_counts.png');

print(f1,plot1,'-dpng','-r180');
close(f1);

%% GRAPH 2 - RADAR RANGE OVER TIME

f2 = figure('Visible','off','Color','w', ...
    'Position',[100 100 1050 620]);

plot(frames,medianRange,'LineWidth',1.5);
hold on;
plot(frames,maxRange,'LineWidth',1.5);

xlabel('GEMSTAR frame index');
ylabel('Measured radar range (m)');
title('Median and maximum radar range per frame');
legend('Median range','Maximum range', ...
    'Location','best');
grid on;
ylim([0 51]);

plot2 = fullfile(graphDir, ...
    'task21_06_temporal_ranges.png');

print(f2,plot2,'-dpng','-r180');
close(f2);

%% GRAPH 3 - FRAME-TO-FRAME COUNT CHANGES

f3 = figure('Visible','off','Color','w', ...
    'Position',[100 100 1050 620]);

plot(frames(2:end),countChange(2:end), ...
    'LineWidth',1.2);
hold on;

yline(jumpThreshold,'--');
yline(-jumpThreshold,'--');

xlabel('GEMSTAR frame index');
ylabel('Change in candidate return count');
title('Frame-to-frame variation in radar returns');
grid on;

plot3 = fullfile(graphDir, ...
    'task21_06_frame_count_changes.png');

print(f3,plot3,'-dpng','-r180');
close(f3);

%% SAVE RESEARCH FINDINGS

findingsPath = fullfile(findingDir, ...
    'task21_06_temporal_findings.txt');

fid = fopen(findingsPath,'w');

if fid < 0
    error('Unable to create findings file.');
end

fprintf(fid,'TASK 21.6 - TEMPORAL RADAR ANALYSIS\n\n');

fprintf(fid,'Analyzed frames: 1-99\n');
fprintf(fid,'Total candidate returns: %d\n',sum(counts));
fprintf(fid,'Minimum returns per frame: %d\n',min(counts));
fprintf(fid,'Maximum returns per frame: %d\n',max(counts));
fprintf(fid,'Mean returns per frame: %.4f\n',mean(counts));
fprintf(fid,'Frames with zero returns: %d\n',nnz(counts == 0));
fprintf(fid,'Large return-count jumps: %d\n',nnz(largeJump));
fprintf(fid,'Jump threshold: %.4f returns\n',jumpThreshold);

fprintf(fid,'\nLIMITATIONS\n');
fprintf(fid,'Frame number is not elapsed time in seconds.\n');
fprintf(fid,'Return-count changes do not prove sensor faults.\n');
fprintf(fid,'Scene changes and ray intersections may affect counts.\n');
fprintf(fid,'No independent object detections verified.\n');
fprintf(fid,'No processing energy measured.\n');

fclose(fid);

%% FINAL SUMMARY

fprintf('\n=== TASK 21.6 TEMPORAL RESULTS ===\n');

fprintf('Frames analyzed: %d\n',numel(frames));
fprintf('Total candidate returns: %d\n',sum(counts));
fprintf('Minimum returns/frame: %d\n',min(counts));
fprintf('Maximum returns/frame: %d\n',max(counts));
fprintf('Average returns/frame: %.4f\n',mean(counts));
fprintf('Frames with zero returns: %d\n',nnz(counts == 0));
fprintf('Large return-count jumps: %d\n',nnz(largeJump));
fprintf('Jump threshold: %.4f\n',jumpThreshold);

fprintf('\n=== TASK 21.6 FILE VERIFICATION ===\n');

fprintf('Graph 1 saved: %d\n',isfile(plot1));
fprintf('Graph 2 saved: %d\n',isfile(plot2));
fprintf('Graph 3 saved: %d\n',isfile(plot3));
fprintf('CSV saved: %d\n',isfile(csvPath));
fprintf('Findings saved: %d\n',isfile(findingsPath));

fprintf('\n=== TASK 21.6 COMPLETE ===\n');
