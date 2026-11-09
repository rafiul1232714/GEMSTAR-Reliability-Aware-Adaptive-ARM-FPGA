
%% TASK 12.5 - CROSS-SENSOR ASSOCIATION ASSESSMENT
% GEMSTAR MOR100 - Frame 150
% Camera, LiDAR, Radar and Ground Truth evidence.
% No confirmed tri-sensor fusion is claimed.

clc;
clear;
close all;

root = "E:\GEMSTAR_Project\sensor-health-monitor";
task = fullfile(root,"tests","Task_12_Final_Research");

csvDir = fullfile(task,"02_CSV_Data");
graphDir = fullfile(task,"01_Graphs");
findDir = fullfile(task,"06_Research_Findings");
codeDir = fullfile(task,"04_Code");

%% 1. LOAD PREVIOUS TASK RESULTS

camera = readtable(fullfile(csvDir, ...
    "task12_2_groundtruth_camera_validation.csv"));

lidar = readtable(fullfile(csvDir, ...
    "task12_3_lidar_gt_summary.csv"));

radar = readtable(fullfile(csvDir, ...
    "task12_4_radar_gt_summary.csv"));

assert(height(camera)==1,"Expected one camera-GT result.");
assert(camera.frame==150,"Camera frame mismatch.");
assert(camera.target_id==76865,"GT target mismatch.");

assert(isequal(sort(lidar.lateral_sign),[-1;1]), ...
    "LiDAR sign hypotheses missing.");

assert(isequal(sort(radar.lateral_sign),[-1;1]), ...
    "Radar sign hypotheses missing.");

%% 2. BUILD COMPARISON TABLE

signs = [1;-1];

lidar1m = zeros(2,1);
lidar2m = zeros(2,1);
radar1m = zeros(2,1);
radar2m = zeros(2,1);
lidarMin = zeros(2,1);
radarMin = zeros(2,1);

for k = 1:2

    s = signs(k);

    L = lidar(lidar.lateral_sign==s,:);
    R = radar(radar.lateral_sign==s,:);

    lidar1m(k) = L.points_within_1m;
    lidar2m(k) = L.points_within_2m;

    radar1m(k) = R.returns_within_1m;
    radar2m(k) = R.returns_within_2m;

    lidarMin(k) = L.nearest_distance_m;
    radarMin(k) = R.nearest_distance_m;

end

comparison = table( ...
    signs,lidar1m,lidar2m, ...
    radar1m,radar2m, ...
    lidarMin,radarMin, ...
    'VariableNames',{ ...
    'lateral_sign', ...
    'lidar_within_1m', ...
    'lidar_within_2m', ...
    'radar_within_1m', ...
    'radar_within_2m', ...
    'nearest_lidar_m', ...
    'nearest_radar_m'});

writetable(comparison,fullfile(csvDir, ...
    "task12_5_cross_sensor_comparison.csv"));

%% 3. CREATE RESEARCH FIGURE

fig = figure('Color','w', ...
    'Position',[100 100 1150 700]);

t = tiledlayout(2,2, ...
    'TileSpacing','compact', ...
    'Padding','compact');

nexttile;
bar(signs,[lidar1m,lidar2m],'grouped');
xlabel('Lateral sign');
ylabel('LiDAR point count');
title('LiDAR Proximity to GT 76865');
legend('Within 1 m','Within 2 m');
grid on;

nexttile;
bar(signs,[radar1m,radar2m],'grouped');
xlabel('Lateral sign');
ylabel('Radar return count');
title('Radar Proximity to GT 76865');
legend('Within 1 m','Within 2 m');
grid on;

nexttile;
bar(signs,[lidarMin,radarMin],'grouped');
xlabel('Lateral sign');
ylabel('Nearest XY distance (m)');
title('Nearest-Measurement Comparison');
legend('LiDAR','Radar');
grid on;

nexttile;
axis off;

text(0,0.88,'Camera / GT candidate:', ...
    'FontWeight','bold','FontSize',13);

text(0,0.71, ...
    sprintf('GT object: %d',camera.target_id), ...
    'FontSize',12);

text(0,0.56, ...
    sprintf('Camera GT error (-Y): %.1f pixels', ...
    camera.error_negative_px), ...
    'FontSize',12);

text(0,0.41, ...
    'YOLO car detection: visually validated', ...
    'FontSize',12);

text(0,0.24, ...
    'LiDAR/Radar identity: NOT VERIFIED', ...
    'FontSize',12,'Color',[0.7 0.1 0.1]);

text(0,0.08, ...
    'Proximity is not confirmed fusion.', ...
    'FontSize',11);

sgtitle('Task 12.5 - Cross-Sensor Association Evidence');

pngFile = fullfile(graphDir, ...
    "task12_5_cross_sensor_assessment.png");

figFile = fullfile(graphDir, ...
    "task12_5_cross_sensor_assessment.fig");

exportgraphics(fig,pngFile,'Resolution',250);
savefig(fig,figFile);

%% 4. RESEARCH EVIDENCE STATUS TABLE

sensor = ["Camera";"LiDAR";"Radar"];
observation = [
    "YOLO car bbox overlaps GT candidate projection"
    "Measured returns near GT center"
    "Measured returns near GT center"
];

status = [
    "SUPPORTED_CANDIDATE"
    "UNVERIFIED_OBJECT_IDENTITY"
    "UNVERIFIED_OBJECT_IDENTITY"
];

evidence = table(sensor,observation,status);

writetable(evidence,fullfile(csvDir, ...
    "task12_5_evidence_status.csv"));

%% 5. SAVE RESEARCH INTERPRETATION

reportFile = fullfile(findDir, ...
    "task12_5_cross_sensor_findings.txt");

fid = fopen(reportFile,'w');
assert(fid~=-1,"Cannot write findings.");

fprintf(fid,'TASK 12.5 - ASSOCIATION ASSESSMENT\n');
fprintf(fid,'Scenario: MOR100, frame 150\n');
fprintf(fid,'Target GT ID: 76865\n\n');

fprintf(fid,'CAMERA\n');
fprintf(fid,'GT projection supports a car candidate.\n');
fprintf(fid,'Camera correspondence is not fully calibrated.\n\n');

fprintf(fid,'LIDAR / RADAR\n');

for k = 1:height(comparison)
    fprintf(fid,'\nY sign %+d\n',comparison.lateral_sign(k));
    fprintf(fid,'LiDAR within 2 m: %d\n', ...
        comparison.lidar_within_2m(k));
    fprintf(fid,'Radar within 2 m: %d\n', ...
        comparison.radar_within_2m(k));
end

fprintf(fid,'\nFINAL ASSESSMENT\n');
fprintf(fid,'Camera-GT candidate: SUPPORTED, NOT PROVEN.\n');
fprintf(fid,'LiDAR-GT association: UNVERIFIED.\n');
fprintf(fid,'Radar-GT association: UNVERIFIED.\n');
fprintf(fid,'Tri-sensor fusion: NOT CONFIRMED.\n');
fprintf(fid,'XY search circles are not object boundaries.\n');
fprintf(fid,'Coordinate-frame conventions remain provisional.\n');
fprintf(fid,'No energy or accuracy improvement is claimed.\n');

fclose(fid);

%% 6. ARCHIVE SOURCE CODE

source = fullfile(root,"matlab", ...
    "task12_cross_sensor_assessment.m");

if isfile(source)
    copyfile(source,codeDir,'f');
end

%% 7. FINAL RESULTS

disp('===== TASK 12.5 COMPARISON =====');
disp(comparison);

disp('===== EVIDENCE STATUS =====');
disp(evidence);

fprintf('Graph: %s\n',pngFile);
fprintf('Findings: %s\n',reportFile);
fprintf('\nTASK 12.5 COMPLETED\n');
