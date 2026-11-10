%% TASK 25.4D - MATLAB ASSOCIATION RELIABILITY
clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_25_Final_Research';
dataDir = fullfile(root, '02_CSV_Data');
plotDir = fullfile(root, '04_Plots');
findDir = fullfile(root, '06_Research_Findings');

if ~exist(plotDir,'dir'), mkdir(plotDir); end
if ~exist(findDir,'dir'), mkdir(findDir); end

T = readtable(fullfile(dataDir, ...
    'task25_33_association_distance_analysis.csv'), ...
    'TextType','string');

sensor = string(T.Sensor);
status = string(T.Status);
frame = str2double(string(T.Frame));
distance = str2double(string(T.Distance_m));

assert(height(T)==162,'Expected 162 association rows');
assert(all(isfinite(frame)),'Invalid frame identifiers');

radar = sensor=="Radar";
lidar = sensor=="LiDAR";

radarMatch = radar & ...
    status=="PROVISIONAL_RADAR_SPATIAL_MATCH";

radarMissing = radar & ...
    status=="NO_RADAR_SPATIAL_MATCH";

lidarMatch = lidar & status=="MATCHED";
lidarInit = lidar & status=="INITIALIZED";

assert(nnz(radar)==81 && nnz(lidar)==81, ...
    'Unexpected sensor record counts');

assert(nnz(radarMatch)==65 && nnz(radarMissing)==16, ...
    'Radar status audit mismatch');

assert(nnz(lidarMatch)==74 && nnz(lidarInit)==7, ...
    'LiDAR status audit mismatch');

assert(nnz(isfinite(distance(radarMatch)))==65, ...
    'Missing Radar matched distances');

assert(nnz(isfinite(distance(lidarMatch)))==74, ...
    'Missing LiDAR matched distances');

assert(all(isfinite(distance(radarMatch)) & ...
    distance(radarMatch)>=0), 'Invalid Radar distance');

assert(all(isfinite(distance(lidarMatch)) & ...
    distance(lidarMatch)>=0), 'Invalid LiDAR distance');

R = distance(radarMatch);
L = distance(lidarMatch);

fprintf('\n=== TASK 25.4D ===\n');
fprintf('Radar: N=%d Mean=%.6f Max=%.6f m\n', ...
    numel(R),mean(R),max(R));
fprintf('LiDAR: N=%d Mean=%.6f Max=%.6f m\n', ...
    numel(L),mean(L),max(L));

assert(abs(mean(R)-0.0440801538461539)<1e-5, ...
    'Radar mean differs from audited value');

assert(abs(mean(L)-0.0946882432432432)<1e-5, ...
    'LiDAR mean differs from audited value');

%% Figure 1 - Distance histograms
f1 = figure('Color','w','Position',[100 100 1150 700]);

subplot(2,1,1);
histogram(R,20);
xlabel('Radar spatial gap to candidate box (m)');
ylabel('Record count');
title('Radar provisional spatial association distances');
grid on;

subplot(2,1,2);
histogram(L,20);
xlabel('LiDAR temporal association distance (m)');
ylabel('Record count');
title('LiDAR matched-track association distances');
grid on;

exportgraphics(f1,fullfile(plotDir, ...
    'task25_34_association_distance_histograms.png'), ...
    'Resolution',300);

exportgraphics(f1,fullfile(plotDir, ...
    'task25_34_association_distance_histograms.pdf'), ...
    'ContentType','vector');

disp('FIGURE_1_SAVED');

%% Figure 2 - Association status counts per frame
allFrames = unique(frame);
assert(numel(allFrames)==53,'Expected 53 selected frames');

radarMatchedCount = zeros(size(allFrames));
radarMissingCount = zeros(size(allFrames));
lidarMatchedCount = zeros(size(allFrames));
lidarInitCount = zeros(size(allFrames));

for i=1:numel(allFrames)
    current = frame==allFrames(i);
    radarMatchedCount(i)=nnz(current & radarMatch);
    radarMissingCount(i)=nnz(current & radarMissing);
    lidarMatchedCount(i)=nnz(current & lidarMatch);
    lidarInitCount(i)=nnz(current & lidarInit);
end

f2 = figure('Color','w','Position',[100 100 1200 650]);

plot(allFrames,radarMatchedCount,'-o','LineWidth',1.3);
hold on;
plot(allFrames,radarMissingCount,'-s','LineWidth',1.3);
plot(allFrames,lidarMatchedCount,'-^','LineWidth',1.3);
plot(allFrames,lidarInitCount,'--','LineWidth',1.2);
hold off;

xlabel('Original GEMSTAR frame index');
ylabel('Track-level record count');
title('Sensor association support across 53 selected frames');
legend('Radar provisional match','Radar no match', ...
    'LiDAR matched','LiDAR initialized', ...
    'Location','best');
grid on;

exportgraphics(f2,fullfile(plotDir, ...
    'task25_35_association_support_timeline.png'), ...
    'Resolution',300);

exportgraphics(f2,fullfile(plotDir, ...
    'task25_35_association_support_timeline.pdf'), ...
    'ContentType','vector');

disp('FIGURE_2_SAVED');

%% Figure 3 - Distance versus frame, separated by sensor
f3 = figure('Color','w','Position',[100 100 1150 700]);

subplot(2,1,1);
scatter(frame(radarMatch),R,24,'filled');
xlabel('Original GEMSTAR frame index');
ylabel('Radar spatial gap (m)');
title('Radar provisional matches over selected frames');
grid on;

subplot(2,1,2);
scatter(frame(lidarMatch),L,24,'filled');
xlabel('Original GEMSTAR frame index');
ylabel('LiDAR temporal distance (m)');
title('LiDAR temporal matches over selected frames');
grid on;

exportgraphics(f3,fullfile(plotDir, ...
    'task25_36_association_distance_timeline.png'), ...
    'Resolution',300);

exportgraphics(f3,fullfile(plotDir, ...
    'task25_36_association_distance_timeline.pdf'), ...
    'ContentType','vector');

disp('FIGURE_3_SAVED');

%% Save numerical findings
report = fullfile(findDir, ...
    'task25_37_matlab_association_findings.txt');

fid = fopen(report,'w');
assert(fid>0,'Cannot create findings report');

fprintf(fid,'TASK 25.4D - ASSOCIATION RELIABILITY\n\n');
fprintf(fid,'Radar matched records: %d\n',numel(R));
fprintf(fid,'Radar no-match records: %d\n',nnz(radarMissing));
fprintf(fid,'Radar mean spatial gap: %.9f m\n',mean(R));
fprintf(fid,'Radar max spatial gap: %.9f m\n',max(R));

fprintf(fid,'\nLiDAR matched records: %d\n',numel(L));
fprintf(fid,'LiDAR initialized records: %d\n',nnz(lidarInit));
fprintf(fid,'LiDAR mean temporal distance: %.9f m\n',mean(L));
fprintf(fid,'LiDAR max temporal distance: %.9f m\n',max(L));

fprintf(fid,'\nINTERPRETATION LIMITATIONS\n');
fprintf(fid,'These two distances have different definitions.\n');
fprintf(fid,'Radar zero box gap does not prove correct identity.\n');
fprintf(fid,'Provisional associations are not GT-confirmed matches.\n');
fprintf(fid,'Selected frames are not independent experiments.\n');
fprintf(fid,'TASK25_04D_MATLAB_PASS\n');
fclose(fid);

%% Verify exported research artifacts
outputs = {
    'task25_34_association_distance_histograms.png'
    'task25_34_association_distance_histograms.pdf'
    'task25_35_association_support_timeline.png'
    'task25_35_association_support_timeline.pdf'
    'task25_36_association_distance_timeline.png'
    'task25_36_association_distance_timeline.pdf'
};

for k=1:numel(outputs)
    info=dir(fullfile(plotDir,outputs{k}));
    assert(~isempty(info) && info.bytes>0, ...
        ['Missing or empty output: ',outputs{k}]);
end

fprintf('\nFIGURES_VERIFIED: %d\n',numel(outputs));
disp('TASK25_04D_MATLAB_PASS');
disp(['Saved to: ',plotDir]);
