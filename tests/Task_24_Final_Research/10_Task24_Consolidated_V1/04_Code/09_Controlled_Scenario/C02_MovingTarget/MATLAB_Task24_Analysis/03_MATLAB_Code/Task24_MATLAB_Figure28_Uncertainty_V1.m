%% TASK 24.10.5.3D.4 - FIGURE 28
% EKF reported X uncertainty versus GT-center X residual.
% Different object reference points may dominate the residual.
% This is NOT an NEES or calibrated covariance consistency test.

clear; clc; close all;

base = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget';

data = fullfile(base,'C02_V2_EKF_Input_53Frames_V1');
out  = fullfile(base,'MATLAB_Task24_Analysis');

figDir = fullfile(out,'01_Graphs');
csvDir = fullfile(out,'02_CSV_Data');

if ~isfolder(figDir), mkdir(figDir); end
if ~isfolder(csvDir), mkdir(csvDir); end

gtPath = fullfile(data,'gt_center_comparison_track2_v1.csv');
ekfPath = fullfile(data,'lidar_radar_ekf_track2_v1.csv');

figPath = fullfile(figDir,'Task24_Figure_28.png');
csvPath = fullfile(csvDir, ...
    'Task24_Figure28_X_Uncertainty_Residual_V1.csv');

assert(isfile(gtPath),'Missing GT comparison');
assert(isfile(ekfPath),'Missing EKF data');
assert(~isfile(figPath),'Figure already exists');
assert(~isfile(csvPath),'CSV already exists');

%% LOAD AND ALIGN BY FRAME

G = readtable(gtPath);
E = readtable(ekfPath);

assert(height(G)==23,'Expected 23 GT comparisons');
assert(height(E)==24,'Expected 24 EKF observations');

[matched,idx] = ismember(G.frame,E.frame);

assert(all(matched),'GT frames missing from EKF table');
assert(numel(unique(G.frame))==height(G), ...
    'Duplicate GT frame');

EK = E(idx,:);

assert(all(abs(G.time_s-EK.time_s)<1e-5), ...
    'Timestamp mismatch');

t = G.time_s;

lidarResidual = G.lidar_x_error_m;
radarResidual = G.radar_x_error_m;

lidarSigma = EK.lidar_only_std_x_m;
radarSigma = EK.radar_ekf_std_x_m;

assert(all(isfinite(lidarSigma) & lidarSigma>0), ...
    'Invalid LiDAR uncertainty');

assert(all(isfinite(radarSigma) & radarSigma>0), ...
    'Invalid Radar EKF uncertainty');

lidarRatio = abs(lidarResidual)./lidarSigma;
radarRatio = abs(radarResidual)./radarSigma;

%% FIGURE 28: TWO PANELS

f = figure('Color','w', ...
    'Position',[80 60 1200 850]);

tiledlayout(2,1, ...
    'TileSpacing','compact', ...
    'Padding','compact');

%% PANEL A: RESIDUALS AND NOMINAL UNCERTAINTY

nexttile;
hold on;

plot(t,lidarResidual,'-o', ...
    'LineWidth',1.6,'MarkerSize',5, ...
    'DisplayName','LiDAR-only X residual');

plot(t,radarResidual,'-s', ...
    'LineWidth',1.6,'MarkerSize',5, ...
    'DisplayName','LiDAR-Radar X residual');

plot(t,radarSigma,'k--', ...
    'LineWidth',1.4, ...
    'DisplayName','Radar EKF +1 sigma');

plot(t,-radarSigma,'k:', ...
    'LineWidth',1.4, ...
    'DisplayName','Radar EKF -1 sigma');

yline(0,'Color',[0.5 0.5 0.5]);

ylabel('Longitudinal residual / uncertainty (m)');

title('A. GT-center X residual versus reported X sigma');

legend('Location','best');
grid on;

%% PANEL B: NORMALIZED RESIDUAL MAGNITUDE

nexttile;
hold on;

plot(t,lidarRatio,'-o', ...
    'LineWidth',1.6,'MarkerSize',5, ...
    'DisplayName','LiDAR-only |error| / sigma');

plot(t,radarRatio,'-s', ...
    'LineWidth',1.6,'MarkerSize',5, ...
    'DisplayName','LiDAR-Radar |error| / sigma');

yline(1,'k--','Ratio = 1');
yline(2,'k:','Ratio = 2');

xlabel('Recording time (s)');
ylabel('Absolute X residual / reported sigma');

title(['B. Diagnostic ratio; object-center and ', ...
       'LiDAR-surface references differ']);

legend('Location','best');
grid on;

sgtitle(['Figure 28 - EKF X uncertainty and ', ...
    'GT-center reference mismatch']);

exportgraphics(f,figPath,'Resolution',220);
close(f);

%% EXPORT FRAME-ALIGNED EVIDENCE

Evidence = table( ...
    G.frame,t, ...
    lidarResidual,radarResidual, ...
    lidarSigma,radarSigma, ...
    lidarRatio,radarRatio, ...
    'VariableNames',{ ...
    'Frame','Time_s', ...
    'LiDAR_GTcenter_Xresidual_m', ...
    'Radar_GTcenter_Xresidual_m', ...
    'LiDAR_ReportedSigmaX_m', ...
    'Radar_ReportedSigmaX_m', ...
    'LiDAR_AbsResidualOverSigma', ...
    'Radar_AbsResidualOverSigma'});

writetable(Evidence,csvPath);

%% NUMERICAL FINDINGS

fprintf('\n=== TASK 24 FIGURE 28 RESULTS ===\n');

fprintf('EVALUATED_FRAMES=%d\n',height(G));

fprintf('MEAN_LIDAR_X_RESIDUAL_M=%.6f\n', ...
    mean(lidarResidual));

fprintf('MEAN_RADAR_X_RESIDUAL_M=%.6f\n', ...
    mean(radarResidual));

fprintf('MEAN_LIDAR_SIGMA_X_M=%.6f\n', ...
    mean(lidarSigma));

fprintf('MEAN_RADAR_SIGMA_X_M=%.6f\n', ...
    mean(radarSigma));

fprintf('MEAN_LIDAR_ABS_ERROR_OVER_SIGMA=%.6f\n', ...
    mean(lidarRatio));

fprintf('MEAN_RADAR_ABS_ERROR_OVER_SIGMA=%.6f\n', ...
    mean(radarRatio));

fprintf('RADAR_FRAMES_RATIO_ABOVE_2=%d\n', ...
    sum(radarRatio>2));

fprintf('FIGURE=%s\n',figPath);
fprintf('EVIDENCE_CSV=%s\n',csvPath);

fprintf('REFERENCE_POINT_MISMATCH=UNRESOLVED\n');
fprintf('VALIDATED_COVARIANCE_CONSISTENCY=NO\n');
fprintf('FULL_STATE_NEES_COMPUTED=NO\n');
fprintf('GROUND_TRUTH_USED_FOR_FILTER_UPDATE=NO\n');
fprintf('ORIGINAL_INPUTS_MODIFIED=NO\n');

fprintf('TASK24_MATLAB_FIGURE28_COMPLETE\n');