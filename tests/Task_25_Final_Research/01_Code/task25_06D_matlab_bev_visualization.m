%% TASK 25.6D - GEMSTAR GEOMETRIC BEV
% Provisional coordinate overlay - NOT calibrated sensor fusion.
% Reads previously validated CSV evidence without changing it.

clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_25_Final_Research';
dataDir = fullfile(root,'02_CSV_Data');
plotDir = fullfile(root,'04_Plots');
findDir = fullfile(root,'06_Research_Findings');

if ~exist(plotDir,'dir'), mkdir(plotDir); end
if ~exist(findDir,'dir'), mkdir(findDir); end

%% Load evidence
T = readtable(fullfile(dataDir, ...
    'task25_49_bev_coordinate_audit.csv'), ...
    'TextType','string');

G = readtable(fullfile(dataDir, ...
    'task25_50_bev_track2_geometry_diagnostic.csv'), ...
    'TextType','string');

assert(height(T)==59, 'Expected 59 BEV coordinate records');
assert(height(G)==3, 'Expected 3 geometry records');

frame = str2double(string(T.Frame));
source = string(T.Source);
track = string(T.TrackID);
x = str2double(string(T.X_m));
y = str2double(string(T.Y_m));

frames = [41 530 816];

assert(all(isfinite(frame)) && all(isfinite(x)) && ...
    all(isfinite(y)), 'Invalid BEV coordinates');

assert(all(ismember(unique(frame),frames)) && ...
    numel(unique(frame))==3, 'Unexpected frame inventory');

assert(nnz(source=="GroundTruth_center_ego")==3, ...
    'Expected three GT centers');

assert(nnz(source=="LiDAR_track")==6, ...
    'Expected six LiDAR track records');

assert(nnz(source=="Radar_return")==50, ...
    'Expected 50 Radar returns');

%% Figure 1 - Three-frame BEV
f1 = figure('Color','w','Position',[60 80 1500 550]);

for k=1:3
    idx = frame==frames(k);

    gt = idx & source=="GroundTruth_center_ego";
    l2 = idx & source=="LiDAR_track" & track=="2";
    l7 = idx & source=="LiDAR_track" & track=="7";
    radar = idx & source=="Radar_return";

    assert(nnz(gt)==1 && nnz(l2)==1 && nnz(l7)==1, ...
        'Missing GT or LiDAR track');

    subplot(1,3,k);
    hold on;

    % Draw only measured coordinate points.
    scatter(x(radar),y(radar),20, ...
        [0.40 0.45 0.55],'filled', ...
        'DisplayName','Radar returns');

    scatter(x(l7),y(l7),110, ...
        [0.54 0.35 0.75],'filled', ...
        'DisplayName','LiDAR Track 7');

    scatter(x(l2),y(l2),110, ...
        [0.02 0.62 0.56],'filled', ...
        'DisplayName','LiDAR Track 2');

    scatter(x(gt),y(gt),160, ...
        [0.90 0.48 0.05],'d','filled', ...
        'DisplayName','GT target center');

    % Provisional separation: coordinate frames unverified.
    plot([x(l2) x(gt)],[y(l2) y(gt)], ...
        'k--','LineWidth',1.1, ...
        'DisplayName','Provisional separation');

    xlabel('Recorded X coordinate (m)');
    ylabel('Recorded Y coordinate (m)');
    title(sprintf('GEMSTAR frame %d',frames(k)));

    axis equal;
    grid on;
    box on;
    legend('Location','best','FontSize',8);
    hold off;
end

sgtitle(['Task 25.6 - Provisional Multi-Sensor BEV', ...
    ' | Coordinate alignment NOT independently verified']);

exportgraphics(f1,fullfile(plotDir, ...
    'task25_51_matlab_bev_three_frames.png'), ...
    'Resolution',300);

exportgraphics(f1,fullfile(plotDir, ...
    'task25_51_matlab_bev_three_frames.pdf'), ...
    'ContentType','vector');

disp('BEV_FIGURE_1_SAVED');

%% Figure 2 - Quantitative geometry diagnostics
gf = str2double(string(G.Frame));
longitudinal = str2double(string(G.LongitudinalOffset_m));
lateral = str2double(string(G.LateralOffset_m));
halfLength = str2double(string(G.GT_HalfLength_m));
separation = str2double(string(G.Separation_m));

[gf,order] = sort(gf);
longitudinal = longitudinal(order);
lateral = lateral(order);
halfLength = halfLength(order);
separation = separation(order);

assert(isequal(gf(:),frames(:)), ...
    'Unexpected geometry frame order');

assert(all(isfinite([longitudinal;lateral; ...
    halfLength;separation])), ...
    'Invalid geometric metrics');

assert(all(halfLength>0), 'Invalid half-length');

f2 = figure('Color','w','Position',[90 90 1150 750]);

subplot(2,1,1);
plot(gf,abs(longitudinal),'-o','LineWidth',1.8);
hold on;
plot(gf,halfLength,'--s','LineWidth',1.8);
hold off;
grid on;
xlabel('Original GEMSTAR frame index');
ylabel('Distance (m)');
title('Longitudinal offset magnitude versus GT half-length');
legend('Absolute longitudinal offset', ...
    'GT half-length','Location','best');

subplot(2,1,2);
plot(gf,lateral,'-o','LineWidth',1.8);
hold on;
yline(0,'--');
hold off;
grid on;
xlabel('Original GEMSTAR frame index');
ylabel('Lateral displacement (m)');
title('Provisional LiDAR Track 2 lateral displacement');

sgtitle('Task 25.6 - Geometric Offset Diagnostics');

exportgraphics(f2,fullfile(plotDir, ...
    'task25_52_matlab_bev_geometry_offsets.png'), ...
    'Resolution',300);

exportgraphics(f2,fullfile(plotDir, ...
    'task25_52_matlab_bev_geometry_offsets.pdf'), ...
    'ContentType','vector');

disp('BEV_FIGURE_2_SAVED');

%% Save numerical findings
reportPath = fullfile(findDir, ...
    'task25_53_matlab_bev_findings.txt');

fid = fopen(reportPath,'w');
assert(fid>0,'Cannot create BEV findings');

fprintf(fid,'TASK 25.6D - PROVISIONAL GEMSTAR BEV\n');
fprintf(fid,'Coordinate frames not independently verified.\n\n');
fprintf(fid,'GT centers: 3\nLiDAR records: 6\n');
fprintf(fid,'Radar returns: 50\n\n');

for k=1:3
    fprintf(fid, ...
        'Frame %d: Longitudinal=%.6f m, Lateral=%.6f m, Separation=%.6f m, HalfLength=%.6f m\n', ...
        gf(k),longitudinal(k),lateral(k), ...
        separation(k),halfLength(k));
end

fprintf(fid,'\nLIMITATIONS\n');
fprintf(fid,'LiDAR and Radar XY reference frames remain unverified.\n');
fprintf(fid,'The plotted lines do not prove object identity.\n');
fprintf(fid,'Radar returns may include repeated payloads.\n');
fprintf(fid,'GT vehicle yaw convention is not independently verified.\n');
fprintf(fid,'Vehicle dimensions alone do not explain all offsets.\n');
fprintf(fid,'No extrinsic correction or bias subtraction was applied.\n');
fprintf(fid,'TASK25_06D_MATLAB_BEV_PASS\n');
fclose(fid);

%% Verify output files
files = {
    'task25_51_matlab_bev_three_frames.png'
    'task25_51_matlab_bev_three_frames.pdf'
    'task25_52_matlab_bev_geometry_offsets.png'
    'task25_52_matlab_bev_geometry_offsets.pdf'
};

for k=1:numel(files)
    info = dir(fullfile(plotDir,files{k}));
    assert(~isempty(info) && info.bytes>0, ...
        ['Missing or empty BEV figure: ',files{k}]);
end

info = dir(reportPath);
assert(~isempty(info) && info.bytes>0, ...
    'Missing BEV findings report');

fprintf('\nBEV_FIGURE_FILES_VERIFIED: %d\n',numel(files));
disp('TASK25_06D_MATLAB_BEV_PASS');
disp(['Saved to: ',plotDir]);
