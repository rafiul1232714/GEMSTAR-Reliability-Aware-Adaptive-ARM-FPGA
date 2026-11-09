%% TASK 21.4 - MATLAB RADAR DISTRIBUTION ANALYSIS
clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';
task = fullfile(root,'tests','Task_21_Final_Research');

inputDir = fullfile(task,'02_Imported_Data');
graphDir = fullfile(task,'03_Graphs');
csvDir = fullfile(task,'04_CSV_Results');
findingDir = fullfile(task,'06_Research_Findings');

if ~isfolder(graphDir), mkdir(graphDir); end
if ~isfolder(csvDir), mkdir(csvDir); end
if ~isfolder(findingDir), mkdir(findingDir); end

fprintf('\n=== TASK 21.4 RADAR DISTRIBUTION ANALYSIS ===\n');

% Load existing MATLAB datasets.
A = load(fullfile(inputDir, ...
    'task20_28_radar_world_points.mat'),'T');

B = load(fullfile(inputDir, ...
    'task20_49_50m_radar_returns.mat'),'T');

original = A.T;
corrected = B.T;

% Explicit data selection.
range10 = double(original.RangeM);
range50all = double(corrected.RangeM);
frame50all = double(corrected.Frame);
signal50all = double(corrected.SignalStrength);

% Exclude the frame-zero startup observations.
keep = frame50all > 0 & ...
    isfinite(range50all) & ...
    isfinite(signal50all) & ...
    range50all > 0;

range50 = range50all(keep);
frame50 = frame50all(keep);
signal50 = signal50all(keep);

range10 = range10(isfinite(range10) & range10 > 0);

fprintf('Original records: %d\n',numel(range10));
fprintf('Corrected valid records (frame > 0): %d\n', ...
    numel(range50));

fprintf('Maximum original range: %.4f m\n',max(range10));
fprintf('Maximum corrected range: %.4f m\n',max(range50));
fprintf('Corrected returns > 10 m: %d\n',nnz(range50 > 10));
fprintf('Corrected returns > 20 m: %d\n',nnz(range50 > 20));
fprintf('Corrected returns > 40 m: %d\n',nnz(range50 > 40));

%% GRAPH 1 - RANGE DISTRIBUTION COMPARISON

f1 = figure('Color','w','Visible','off', ...
    'Position',[100 100 1000 600]);

edges = 0:1:50;

histogram(range10,edges, ...
    'Normalization','probability');
hold on;
histogram(range50,edges, ...
    'Normalization','probability');

xlabel('Radar measured range (m)');
ylabel('Fraction of candidate returns');
title('Original 10 m vs corrected 50 m radar range');
legend('Original archived data', ...
       'Corrected 50 m, frames 1-99', ...
       'Location','northeast');
grid on;
xlim([0 50]);

png1 = fullfile(graphDir, ...
    'task21_04_range_comparison.png');
print(f1,png1,'-dpng','-r180');
close(f1);

%% GRAPH 2 - SIGNAL STRENGTH VS RANGE

f2 = figure('Color','w','Visible','off', ...
    'Position',[100 100 1000 600]);

scatter(range50,signal50,8,'filled');

xlabel('Measured radar range (m)');
ylabel('Recorded signal strength');
title('Corrected radar: signal strength vs range');
grid on;

png2 = fullfile(graphDir, ...
    'task21_04_signal_vs_range.png');
print(f2,png2,'-dpng','-r180');
close(f2);

%% GRAPH 3 - RETURNS PER FRAME

[uniqueFrame,~,groupIndex] = unique(frame50);

frameCounts = accumarray(groupIndex,1);

f3 = figure('Color','w','Visible','off', ...
    'Position',[100 100 1000 600]);

plot(uniqueFrame,frameCounts,'-o', ...
    'LineWidth',1.2,'MarkerSize',3);

xlabel('GEMSTAR frame index');
ylabel('Candidate radar returns');
title('Corrected 50 m radar: returns per frame');
grid on;

png3 = fullfile(graphDir, ...
    'task21_04_returns_per_frame.png');
print(f3,png3,'-dpng','-r180');
close(f3);

%% SAVE CSV STATISTICS

dataset = ["Original archived 10m data"; ...
           "Corrected 50m frames 1-99"];

count = [numel(range10);numel(range50)];
minimum = [min(range10);min(range50)];
medianRange = [median(range10);median(range50)];
maximum = [max(range10);max(range50)];
beyond10 = [nnz(range10 > 10);nnz(range50 > 10)];

stats = table(dataset,count,minimum,medianRange, ...
    maximum,beyond10, ...
    'VariableNames', ...
    {'Dataset','Count','MinimumRangeM', ...
     'MedianRangeM','MaximumRangeM','ReturnsBeyond10m'});

statsPath = fullfile(csvDir, ...
    'task21_04_radar_distribution_statistics.csv');

writetable(stats,statsPath);

frameTable = table(uniqueFrame,frameCounts, ...
    'VariableNames',{'Frame','ReturnCount'});

framePath = fullfile(csvDir, ...
    'task21_04_returns_per_frame.csv');

writetable(frameTable,framePath);

%% RESEARCH FINDINGS

findingsPath = fullfile(findingDir, ...
    'task21_04_distribution_findings.txt');

fid = fopen(findingsPath,'w');

if fid < 0
    error('Could not create research findings file.');
end

fprintf(fid,'TASK 21.4 - MATLAB RADAR DISTRIBUTIONS\n\n');
fprintf(fid,'Original records: %d\n',numel(range10));
fprintf(fid,'Corrected records, excluding frame 0: %d\n', ...
    numel(range50));
fprintf(fid,'Original maximum range: %.6f m\n',max(range10));
fprintf(fid,'Corrected maximum range: %.6f m\n',max(range50));
fprintf(fid,'Corrected returns above 10m: %d\n', ...
    nnz(range50 > 10));
fprintf(fid,'Corrected returns above 20m: %d\n', ...
    nnz(range50 > 20));
fprintf(fid,'Corrected returns above 40m: %d\n', ...
    nnz(range50 > 40));

fprintf(fid,'\nLIMITATIONS\n');
fprintf(fid,'Original and corrected data are not paired.\n');
fprintf(fid,'Original dataset combines archived scenario records.\n');
fprintf(fid,'Frame 0 excluded from corrected plots.\n');
fprintf(fid,'Candidate returns do not establish object detection.\n');
fprintf(fid,'Signal strength is simulator output, not calibrated SNR.\n');
fprintf(fid,'No hardware power or energy measured.\n');

fclose(fid);

fprintf('\n=== TASK 21.4 STATISTICS ===\n');
disp(stats);

fprintf('Graph 1 saved: %d\n',isfile(png1));
fprintf('Graph 2 saved: %d\n',isfile(png2));
fprintf('Graph 3 saved: %d\n',isfile(png3));
fprintf('Statistics saved: %d\n',isfile(statsPath));
fprintf('Frame counts saved: %d\n',isfile(framePath));
fprintf('Findings saved: %d\n',isfile(findingsPath));

fprintf('\n=== TASK 21.4 COMPLETE ===\n');
