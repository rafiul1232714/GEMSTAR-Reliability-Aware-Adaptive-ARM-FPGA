
%% TASK 12.4 - RADAR VS GROUND TRUTH VALIDATION
% GEMSTAR MOR100 - Frame 150
% Compare Radar returns against GT vehicle 76865.
% Proximity analysis only; no confirmed object association.

clc;
clear;
close all;

%% 1. PATHS

root = "E:\GEMSTAR_Project\sensor-health-monitor";

task11 = fullfile(root, ...
    "tests","Task_11_Final_Research");

task12 = fullfile(root, ...
    "tests","Task_12_Final_Research");

dataDir = fullfile(task12,"02_CSV_Data");
graphDir = fullfile(task12,"01_Graphs");
findDir = fullfile(task12,"06_Research_Findings");
codeDir = fullfile(task12,"04_Code");

folders = [dataDir,graphDir,findDir,codeDir];

for k = 1:numel(folders)
    if ~isfolder(folders(k))
        mkdir(folders(k));
    end
end

%% 2. LOAD RECORDED DATA

radarFile = fullfile(task11, ...
    "02_CSV_Data", ...
    "task11_frame150_radar_cluster_association.csv");

gtFile = fullfile(task11, ...
    "02_CSV_Data", ...
    "task11_groundtruth_objects.csv");

assert(isfile(radarFile),"Radar CSV missing");
assert(isfile(gtFile),"Ground Truth CSV missing");

R = readtable(radarFile);
G = readtable(gtFile);

frame = 150;
egoID = 76895;
targetID = 76865;

R = R(R.frame==frame,:);

ego = G(G.frame==frame & G.object_id==egoID,:);
target = G(G.frame==frame & G.object_id==targetID,:);

assert(height(ego)==1,"Ego GT missing");
assert(height(target)==1,"Target GT missing");
assert(~isempty(R),"No Radar returns for frame 150");

%% 3. TRANSFORM GT TO EGO FRAME

dx = target.x_m-ego.x_m;
dy = target.y_m-ego.y_m;

yaw = ego.yaw_rad;

targetX = cos(yaw)*dx+sin(yaw)*dy;
targetY = -sin(yaw)*dx+cos(yaw)*dy;

fprintf('\n======================================\n');
fprintf('TASK 12.4 - RADAR GT VALIDATION\n');
fprintf('======================================\n');

fprintf('Frame: %d\n',frame);
fprintf('GT vehicle ID: %d\n',targetID);
fprintf('Target forward: %.3f m\n',targetX);
fprintf('Target lateral: %.3f m\n',targetY);
fprintf('Radar reflections: %d\n',height(R));

%% 4. RADAR COORDINATES

x = R.x_ego_m;
y = R.y_ego_m;
z = R.z_ego_m;

signs = [1,-1];

resultRows = zeros(2,9);
nearTables = cell(2,1);

fig = figure( ...
    'Color','w', ...
    'Position',[80 80 1350 650]);

t = tiledlayout(1,2, ...
    'TileSpacing','compact', ...
    'Padding','compact');

for k = 1:2

    signY = signs(k);
    yy = signY.*y;

    %% 5. DISTANCE ANALYSIS

    d = hypot(x-targetX,yy-targetY);

    near1 = d<=1.0;
    near2 = d<=2.0;

    minD = min(d);
    n1 = sum(near1);
    n2 = sum(near2);

    if any(near2)
        minZ = min(z(near2));
        maxZ = max(z(near2));
        meanSignal = mean(R.signal_strength(near2));
        meanDoppler = mean(R.doppler_hz(near2));
    else
        minZ = NaN;
        maxZ = NaN;
        meanSignal = NaN;
        meanDoppler = NaN;
    end

    fprintf('\n--- LATERAL SIGN %+d ---\n',signY);
    fprintf('Nearest Radar XY distance: %.3f m\n',minD);
    fprintf('Within 1 m: %d\n',n1);
    fprintf('Within 2 m: %d\n',n2);
    fprintf('Nearby Z range: %.3f to %.3f m\n',minZ,maxZ);
    fprintf('Nearby mean signal: %.4f\n',meanSignal);
    fprintf('Nearby mean Doppler: %.4f Hz\n',meanDoppler);

    resultRows(k,:) = [ ...
        signY,minD,n1,n2,minZ,maxZ, ...
        meanSignal,meanDoppler,height(R)];

    %% 6. SAVE NEARBY RETURNS

    selected = R(near2,:);

    selected.test_lateral_sign = ...
        repmat(signY,height(selected),1);

    selected.test_y_ego_m = signY.*selected.y_ego_m;
    selected.distance_to_gt_xy_m = d(near2);

    nearTables{k} = selected;

    %% 7. PLOT

    nexttile(t,k);
    hold on;

    hAll = scatter(x,yy,55, ...
        [0.65 0.65 0.65],'filled');

    hNear = scatter(x(near2),yy(near2), ...
        85,[0.9 0.2 0.1],'filled');

    hGT = plot(targetX,targetY,'gp', ...
        'MarkerSize',16,'LineWidth',2);

    hEgo = plot(0,0,'ks', ...
        'MarkerSize',9,'LineWidth',2);

    theta = linspace(0,2*pi,300);

    hCircle = plot( ...
        targetX+2*cos(theta), ...
        targetY+2*sin(theta), ...
        'g--','LineWidth',1.5);

    xlabel('Forward X (m)');
    ylabel('Lateral Y (m)');

    title(sprintf( ...
        'Radar Y sign %+d | %d returns within 2m', ...
        signY,n2));

    axis equal;
    xlim([0 16]);
    ylim([-10 10]);
    grid on;

    legend( ...
        [hAll,hNear,hGT,hEgo,hCircle], ...
        {'All Radar returns', ...
         'Near GT', ...
         'GT vehicle center', ...
         'Ego origin', ...
         '2m search radius'}, ...
        'Location','best');

end

sgtitle('Task 12.4 - Radar vs Ground Truth Vehicle 76865');

%% 8. SAVE SUMMARY CSV

summary = table( ...
    resultRows(:,1), ...
    resultRows(:,2), ...
    resultRows(:,3), ...
    resultRows(:,4), ...
    resultRows(:,5), ...
    resultRows(:,6), ...
    resultRows(:,7), ...
    resultRows(:,8), ...
    resultRows(:,9), ...
    'VariableNames',{ ...
    'lateral_sign', ...
    'nearest_distance_m', ...
    'returns_within_1m', ...
    'returns_within_2m', ...
    'min_near_z_m', ...
    'max_near_z_m', ...
    'mean_near_signal', ...
    'mean_near_doppler_hz', ...
    'total_radar_returns'});

summaryFile = fullfile(dataDir, ...
    "task12_4_radar_gt_summary.csv");

writetable(summary,summaryFile);

nearFile = fullfile(dataDir, ...
    "task12_4_radar_near_gt_returns.csv");

allNear = vertcat(nearTables{:});
writetable(allNear,nearFile);

%% 9. SAVE MAIN FIGURE

pngFile = fullfile(graphDir, ...
    "task12_4_radar_gt_validation.png");

figFile = fullfile(graphDir, ...
    "task12_4_radar_gt_validation.fig");

exportgraphics(fig,pngFile,'Resolution',250);
savefig(fig,figFile);

%% 10. SAVE RADAR RANGE GRAPH

rangeFig = figure( ...
    'Color','w', ...
    'Position',[150 150 1000 520]);

scatter(R.range_m,R.signal_strength, ...
    65,R.doppler_hz,'filled');

xlabel('Radar range (m)');
ylabel('Signal strength');

title('Task 12.4 - Radar Range, Signal and Doppler');

colorbar;
grid on;

rangePNG = fullfile(graphDir, ...
    "task12_4_radar_signal_analysis.png");

rangeFIG = fullfile(graphDir, ...
    "task12_4_radar_signal_analysis.fig");

exportgraphics(rangeFig,rangePNG,'Resolution',250);
savefig(rangeFig,rangeFIG);

%% 11. WRITE RESEARCH FINDINGS

reportFile = fullfile(findDir, ...
    "task12_4_radar_gt_findings.txt");

fid = fopen(reportFile,'w');
assert(fid~=-1,"Cannot write research report");

fprintf(fid,'TASK 12.4 - RADAR GROUND TRUTH VALIDATION\n');
fprintf(fid,'Scenario: GEMSTAR MOR100\n');
fprintf(fid,'Frame: 150\n');
fprintf(fid,'GT object: 76865\n');
fprintf(fid,'Radar returns: %d\n\n',height(R));

for k = 1:height(summary)

    fprintf(fid,'Lateral sign: %+d\n', ...
        summary.lateral_sign(k));

    fprintf(fid,'Nearest distance: %.4f m\n', ...
        summary.nearest_distance_m(k));

    fprintf(fid,'Within 1 m: %d\n', ...
        summary.returns_within_1m(k));

    fprintf(fid,'Within 2 m: %d\n', ...
        summary.returns_within_2m(k));

    fprintf(fid,'Nearby Z min/max: %.4f / %.4f m\n', ...
        summary.min_near_z_m(k), ...
        summary.max_near_z_m(k));

    fprintf(fid,'Mean nearby signal: %.4f\n', ...
        summary.mean_near_signal(k));

    fprintf(fid,'Mean nearby Doppler: %.4f Hz\n\n', ...
        summary.mean_near_doppler_hz(k));

end

fprintf(fid,'LIMITATIONS\n');
fprintf(fid,'Radar coordinates remain provisional.\n');
fprintf(fid,'2m proximity does not prove object identity.\n');
fprintf(fid,'The search circle is not the GT vehicle footprint.\n');
fprintf(fid,'Doppler must not be interpreted as velocity without calibration.\n');
fprintf(fid,'No confirmed Radar-to-vehicle association yet.\n');

fclose(fid);

%% 12. ARCHIVE MATLAB CODE

source = fullfile(root,"matlab", ...
    "task12_radar_groundtruth_validation.m");

if isfile(source)
    copyfile(source,codeDir,'f');
end

%% 13. FINAL OUTPUT

fprintf('\n===== TASK 12.4 RESULTS =====\n');
disp(summary);

fprintf('Main graph: %s\n',pngFile);
fprintf('Signal graph: %s\n',rangePNG);
fprintf('Summary CSV: %s\n',summaryFile);
fprintf('Nearby returns CSV: %s\n',nearFile);
fprintf('Findings: %s\n',reportFile);

fprintf('\nTASK 12.4 COMPLETED SUCCESSFULLY\n');
