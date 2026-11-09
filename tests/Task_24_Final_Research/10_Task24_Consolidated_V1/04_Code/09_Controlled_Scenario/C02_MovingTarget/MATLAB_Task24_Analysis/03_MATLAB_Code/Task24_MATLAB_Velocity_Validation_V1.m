%% TASK 24.10.5.3E.4 - VELOCITY VALIDATION
% Uses saved GT velocity evaluation from clean C02 V2.
% Original EKF states and GT recordings are not modified.
% GT actor velocity and GT bounding-center velocity are
% different reference quantities and must not be conflated.

clear; clc; close all;

%% PATHS

base = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget';

data = fullfile(base, 'C02_V2_EKF_Input_53Frames_V1');
out = fullfile(base, 'MATLAB_Task24_Analysis');

figdir = fullfile(out, '01_Graphs');
finddir = fullfile(out, '04_Research_Findings');

if ~isfolder(figdir), mkdir(figdir); end
if ~isfolder(finddir), mkdir(finddir); end

inputPath = fullfile(data, ...
    'gt_ekf_velocity_comparison_v1.csv');

fig29 = fullfile(figdir, 'Task24_Figure_29.png');
fig30 = fullfile(figdir, 'Task24_Figure_30.png');

report = fullfile(finddir, ...
    'Task24_MATLAB_Velocity_Findings_V1.txt');

assert(isfile(inputPath), 'Missing GT velocity CSV');

assert(~isfile(fig29), 'Figure 29 already exists');
assert(~isfile(fig30), 'Figure 30 already exists');
assert(~isfile(report), 'Findings report already exists');

%% LOAD AND VALIDATE

V = readtable(inputPath);

assert(height(V)==23, 'Expected 23 evaluation frames');
assert(numel(unique(V.frame))==23, 'Duplicate frames');
assert(all(diff(V.time_s)>0), 'Timestamps not increasing');

t = V.time_s;

gtvx = V.gt_vx_ego_mps;
gtvy = V.gt_vy_ego_mps;

lvx = V.lidar_vx_mps;
lvy = V.lidar_vy_mps;

rvx = V.radar_ekf_vx_mps;
rvy = V.radar_ekf_vy_mps;

gtSpeed = hypot(gtvx,gtvy);
lidarSpeed = hypot(lvx,lvy);
radarSpeed = hypot(rvx,rvy);

le = V.lidar_velocity_error_mps;
re = V.radar_velocity_error_mps;

fdDifference = V.gt_actor_vs_center_fd_error_mps;
fdValid = isfinite(fdDifference);

assert(all(isfinite(gtvx) & isfinite(gtvy)), ...
    'Invalid GT actor velocities');

assert(all(isfinite(le) & isfinite(re)), ...
    'Invalid EKF velocity errors');

%% FIGURE 29 - VELOCITY ESTIMATOR COMPARISON

f = figure('Color','w', ...
    'Position',[60 50 1250 1050]);

tiledlayout(3,1, ...
    'TileSpacing','compact', ...
    'Padding','compact');

nexttile;

plot(t,gtvx,'k-','LineWidth',2.1);
hold on;
plot(t,lvx,'-o','LineWidth',1.4,'MarkerSize',4);
plot(t,rvx,'-s','LineWidth',1.4,'MarkerSize',4);

ylabel('Vx (m/s)');
title('A. Longitudinal velocity');
legend('GT actor velocity','LiDAR-only EKF', ...
       'LiDAR-Radar EKF','Location','best');
grid on;

nexttile;

plot(t,gtvy,'k-','LineWidth',2.1);
hold on;
plot(t,lvy,'-o','LineWidth',1.4,'MarkerSize',4);
plot(t,rvy,'-s','LineWidth',1.4,'MarkerSize',4);

ylabel('Vy (m/s)');
title('B. Lateral velocity');
grid on;

nexttile;

plot(t,gtSpeed,'k-','LineWidth',2.1);
hold on;
plot(t,lidarSpeed,'-o','LineWidth',1.4,'MarkerSize',4);
plot(t,radarSpeed,'-s','LineWidth',1.4,'MarkerSize',4);

xlabel('Recording time (s)');
ylabel('Speed magnitude (m/s)');
title('C. Total planar speed');
grid on;

sgtitle(['Figure 29 - GT actor velocity and ', ...
    'EKF velocity states']);

exportgraphics(f,fig29,'Resolution',220);
close(f);

%% FIGURE 30 - REFERENCE AND ERROR DIAGNOSTICS

f = figure('Color','w', ...
    'Position',[60 60 1250 880]);

tiledlayout(2,1, ...
    'TileSpacing','compact', ...
    'Padding','compact');

nexttile;

plot(t,le,'-o','LineWidth',1.6,'MarkerSize',5);
hold on;

plot(t,re,'-s','LineWidth',1.6,'MarkerSize',5);

xlabel('Recording time (s)');
ylabel('2D velocity error (m/s)');

title('A. EKF error relative to exported GT actor velocity');

legend('LiDAR-only EKF','LiDAR-Radar EKF', ...
    'Location','best');

grid on;

nexttile;

plot(t(fdValid), ...
    fdDifference(fdValid), ...
    '-o','LineWidth',1.7,'MarkerSize',5);

hold on;

yline(0,'k:', 'Zero discrepancy', ...
    'HandleVisibility','off');

xlabel('Recording time (s)');
ylabel('Velocity reference difference (m/s)');

title(['B. GT actor velocity vs finite-difference ', ...
    'GT bounding-center velocity']);

grid on;

sgtitle(['Figure 30 - Velocity error and ', ...
    'Ground Truth reference disagreement']);

exportgraphics(f,fig30,'Resolution',220);
close(f);

%% COMPUTE SUMMARY

lidarMean = mean(le);
radarMean = mean(re);

lidarRMSE = sqrt(mean(le.^2));
radarRMSE = sqrt(mean(re.^2));

radarImprovement = le-re;

better = sum(radarImprovement>1e-6);
worse = sum(radarImprovement<(-1e-6));
same = sum(abs(radarImprovement)<=1e-6);

fprintf('\n=== TASK 24 MATLAB VELOCITY RESULTS ===\n');

fprintf('GT_EVALUATED_FRAMES=%d\n',height(V));

fprintf('LIDAR_MEAN_VELOCITY_ERROR_MPS=%.6f\n', ...
    lidarMean);

fprintf('RADAR_MEAN_VELOCITY_ERROR_MPS=%.6f\n', ...
    radarMean);

fprintf('LIDAR_VELOCITY_RMSE_MPS=%.6f\n', ...
    lidarRMSE);

fprintf('RADAR_VELOCITY_RMSE_MPS=%.6f\n', ...
    radarRMSE);

fprintf('RADAR_MEAN_ERROR_REDUCTION_MPS=%.6f\n', ...
    lidarMean-radarMean);

fprintf('RADAR_BETTER_FRAMES=%d\n',better);
fprintf('RADAR_WORSE_FRAMES=%d\n',worse);
fprintf('RADAR_APPROX_UNCHANGED_FRAMES=%d\n',same);

fprintf('GT_CENTER_FD_VALID_FRAMES=%d\n', ...
    sum(fdValid));

if any(fdValid)
    fprintf('GT_ACTOR_CENTER_FD_MEDIAN_DIFFERENCE_MPS=%.6f\n', ...
        median(fdDifference(fdValid)));
end

%% RESEARCH FINDINGS REPORT

fid = fopen(report,'w');

assert(fid>=0,'Unable to create findings report');

fprintf(fid,'TASK 24 - MATLAB VELOCITY VALIDATION\n');
fprintf(fid,'====================================\n\n');

fprintf(fid,'Evaluated frames: %d\n',height(V));
fprintf(fid,'Ground Truth target: 76897 (BP_Small_Car_C)\n\n');

fprintf(fid,'LiDAR mean velocity error: %.6f m/s\n', ...
    lidarMean);

fprintf(fid,'LiDAR velocity RMSE: %.6f m/s\n', ...
    lidarRMSE);

fprintf(fid,'LiDAR-Radar mean velocity error: %.6f m/s\n', ...
    radarMean);

fprintf(fid,'LiDAR-Radar velocity RMSE: %.6f m/s\n', ...
    radarRMSE);

fprintf(fid,'Radar improved frames: %d\n',better);
fprintf(fid,'Radar worsened frames: %d\n',worse);
fprintf(fid,'Approximately unchanged frames: %d\n\n',same);

if any(fdValid)
    fprintf(fid, ...
        'GT actor vs bounding-center FD median difference: %.6f m/s\n\n', ...
        median(fdDifference(fdValid)));
end

fprintf(fid,'LIMITATIONS\n');
fprintf(fid,'Single development recording.\n');
fprintf(fid,'23 temporally correlated evaluation frames.\n');
fprintf(fid,'GT exporter velocity divided by 100.\n');
fprintf(fid,'Full ego-motion audit is still pending.\n');
fprintf(fid,'GT bounding-center and actor velocity references differ.\n');
fprintf(fid,'Finite differences use sparse evaluation samples.\n');
fprintf(fid,'EKF states represent LiDAR-associated target geometry.\n');
fprintf(fid,'Camera-aided velocity state is not available in this CSV.\n');
fprintf(fid,'No statistically generalizable accuracy claim.\n');
fprintf(fid,'Ground Truth was not used for filter updates.\n');

fclose(fid);

fprintf('\nFIGURE_29=%s\n',fig29);
fprintf('FIGURE_30=%s\n',fig30);
fprintf('FINDINGS_REPORT=%s\n',report);

fprintf('RESULT_STATUS=EXPLORATORY_SINGLE_RECORDING\n');
fprintf('ORIGINAL_INPUTS_MODIFIED=NO\n');

fprintf('TASK24_MATLAB_VELOCITY_VALIDATION_COMPLETE\n');