%% Task 26.6C.2 - Diagnostic EKF Position Accuracy
% Uses 23 matching GEMSTAR ground-truth/EKF observations.
% Ground truth is the object center in ego coordinates.
% Original coordinate transform is preliminary.
% Camera update is experimental and not authorized.
% This is NOT formal validated perception accuracy.
% No Statistics Toolbox required.

clear; clc; close all;

root = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_26_Final_Research";

csvDir = fullfile(root,"02_CSV_Data");
plotDir = fullfile(root,"04_Plots");
reportDir = fullfile(root,"06_Research_Findings");

framePath = fullfile(csvDir, ...
    "task26_6C_ekf_position_errors_by_frame.csv");

summaryPath = fullfile(csvDir, ...
    "task26_6C_ekf_position_error_summary.csv");

reportPath = fullfile(reportDir, ...
    "task26_6C2_ekf_accuracy_matlab_findings.txt");

plots = [
    "task26_6C2_position_error_by_frame.png"
    "task26_6C2_gt_vs_ekf_trajectory.png"
    "task26_6C2_rmse_mean_comparison.png"
    "task26_6C2_signed_position_bias.png"
];

%% Protect input and existing output files

if ~isfile(framePath) || ~isfile(summaryPath)
    error("Task 26.6C input CSV missing.");
end

if isfile(reportPath)
    error("Existing findings report preserved.");
end

for k = 1:numel(plots)
    if isfile(fullfile(plotDir,plots(k)))
        error("Existing plot preserved: %s",plots(k));
    end
end

%% Load measured diagnostic errors

T = readtable(framePath,"TextType","string");
S = readtable(summaryPath,"TextType","string");

if height(T) ~= 23 || height(S) ~= 3
    error("Unexpected GT/EKF analysis dimensions.");
end

required = [
    "frame"
    "time_s"
    "gt_center_x_ego_m"
    "gt_center_y_ego_m"
    "lidar_only_x_error_m"
    "lidar_only_y_error_m"
    "lidar_only_center_error_m"
    "radar_assisted_x_error_m"
    "radar_assisted_y_error_m"
    "radar_assisted_center_error_m"
    "camera_experimental_x_error_m"
    "camera_experimental_y_error_m"
    "camera_experimental_center_error_m"
];

if ~all(ismember(required, ...
        string(T.Properties.VariableNames)))
    error("Missing required per-frame columns.");
end

T = sortrows(T,"frame");

expectedMethods = [
    "lidar_only"
    "radar_assisted"
    "camera_experimental"
];

if ~all(ismember(expectedMethods,S.method))
    error("Missing EKF method summaries.");
end

[~,order] = ismember(expectedMethods,S.method);
S = S(order,:);

frames = T.frame;

lidarError = T.lidar_only_center_error_m;
radarError = T.radar_assisted_center_error_m;
cameraError = T.camera_experimental_center_error_m;

% Reconstruct estimated positions from GT center + signed errors.
gx = T.gt_center_x_ego_m;
gy = T.gt_center_y_ego_m;

lx = gx + T.lidar_only_x_error_m;
ly = gy + T.lidar_only_y_error_m;

rx = gx + T.radar_assisted_x_error_m;
ry = gy + T.radar_assisted_y_error_m;

cx = gx + T.camera_experimental_x_error_m;
cy = gy + T.camera_experimental_y_error_m;

%% Verify mathematical consistency

recomputed = [
    hypot(T.lidar_only_x_error_m,T.lidar_only_y_error_m), ...
    hypot(T.radar_assisted_x_error_m,T.radar_assisted_y_error_m), ...
    hypot(T.camera_experimental_x_error_m,T.camera_experimental_y_error_m)
];

recorded = [lidarError,radarError,cameraError];

maxErrorDifference = max(abs(recomputed-recorded),[],"all");

if maxErrorDifference > 1e-7
    error("Signed and radial errors are inconsistent.");
end

rmseComputed = sqrt(mean(recorded.^2,1));
maeComputed = mean(recorded,1);

rmseArchived = S.position_rmse_m_diagnostic';
maeArchived = S.mean_center_error_m';

if any(abs(rmseComputed-rmseArchived)>1e-8)
    error("RMSE does not match Python summary.");
end

if any(abs(maeComputed-maeArchived)>1e-8)
    error("Mean center error does not match Python summary.");
end

%% Figure 1 - Per-frame position error

f1 = figure("Color","w","Position",[100 100 1120 550]);

plot(frames,lidarError,"-o","LineWidth",1.5);
hold on;
plot(frames,radarError,"-s","LineWidth",1.5);
plot(frames,cameraError,"-^","LineWidth",1.5);
hold off;

xlabel("GEMSTAR frame");
ylabel("2D object-center position error (m)");
title("Task 26.6C - Diagnostic EKF position error");

legend("LiDAR only","Radar assisted", ...
    "Camera experimental","Location","best");

grid on;
saveas(f1,fullfile(plotDir,plots(1)));

%% Figure 2 - Position trajectories in ego coordinates

f2 = figure("Color","w","Position",[100 100 900 650]);

plot(gx,gy,"k-o","LineWidth",1.8);
hold on;

plot(lx,ly,"--o","LineWidth",1.2);
plot(rx,ry,"--s","LineWidth",1.2);
plot(cx,cy,"--^","LineWidth",1.2);

hold off;

axis equal;
xlabel("Ego-frame X (m)");
ylabel("Ego-frame Y (m)");

title("Task 26.6C - GT center versus EKF position");

legend("GT object center","LiDAR only", ...
    "Radar assisted","Camera experimental", ...
    "Location","best");

grid on;
saveas(f2,fullfile(plotDir,plots(2)));

%% Figure 3 - Aggregate RMSE and mean center error

f3 = figure("Color","w","Position",[100 100 950 550]);

bar([rmseComputed(:),maeComputed(:)]);

set(gca,"XTick",1:3, ...
    "XTickLabel", ...
    {"LiDAR only","Radar assisted","Camera experimental"});

ylabel("Position error (m)");

title("Task 26.6C - Diagnostic RMSE and mean error");

legend("Position RMSE","Mean center error", ...
    "Location","best");

grid on;
saveas(f3,fullfile(plotDir,plots(3)));

%% Figure 4 - Signed X/Y error and systematic bias

f4 = figure("Color","w","Position",[100 100 1050 550]);

bias = [
    mean(T.lidar_only_x_error_m), ...
    mean(T.lidar_only_y_error_m);
    mean(T.radar_assisted_x_error_m), ...
    mean(T.radar_assisted_y_error_m);
    mean(T.camera_experimental_x_error_m), ...
    mean(T.camera_experimental_y_error_m)
];

bar(bias);

set(gca,"XTick",1:3, ...
    "XTickLabel", ...
    {"LiDAR only","Radar assisted","Camera experimental"});

ylabel("Mean signed position error (m)");
title("Task 26.6C - Longitudinal and lateral bias");

legend("X error","Y error","Location","best");

yline(0,"k-");
grid on;

saveas(f4,fullfile(plotDir,plots(4)));

%% Numerical summary

disp("=== TASK 26.6C.2 MATLAB ACCURACY ANALYSIS ===");

fprintf("MATCHED_FRAMES: %d\n",height(T));
fprintf("LIDAR_RMSE_M: %.6f\n",rmseComputed(1));
fprintf("RADAR_RMSE_M: %.6f\n",rmseComputed(2));
fprintf("CAMERA_RMSE_M: %.6f\n",rmseComputed(3));

fprintf("RADAR_MINUS_LIDAR_RMSE_M: %.9f\n", ...
    rmseComputed(2)-rmseComputed(1));

fprintf("CAMERA_MINUS_RADAR_RMSE_M: %.9f\n", ...
    rmseComputed(3)-rmseComputed(2));

fprintf("RADAR_RELATIVE_RMSE_REDUCTION_PERCENT: %.4f\n", ...
    100*(rmseComputed(1)-rmseComputed(2))/rmseComputed(1));

fprintf("LIDAR_MEAN_X_BIAS_M: %.6f\n",bias(1,1));
fprintf("LIDAR_MEAN_Y_BIAS_M: %.6f\n",bias(1,2));

fprintf("RADAR_MEAN_X_BIAS_M: %.6f\n",bias(2,1));
fprintf("RADAR_MEAN_Y_BIAS_M: %.6f\n",bias(2,2));

fprintf("CAMERA_MEAN_X_BIAS_M: %.6f\n",bias(3,1));
fprintf("CAMERA_MEAN_Y_BIAS_M: %.6f\n",bias(3,2));

fprintf("MAX_INTERNAL_ERROR_DIFFERENCE_M: %.12g\n", ...
    maxErrorDifference);

%% Write research report
% Earlier existence check prevents overwriting an existing report.

fid = fopen(reportPath,"w");

if fid == -1
    error("Could not create findings report.");
end

fprintf(fid,"TASK 26.6C.2 - EKF DIAGNOSTIC ACCURACY\n");
fprintf(fid,"====================================\n\n");

fprintf(fid,"Matching GT/EKF observations: %d\n\n",height(T));

for k = 1:3
    fprintf(fid,"%s\n",expectedMethods(k));
    fprintf(fid,"RMSE: %.9f m\n",rmseComputed(k));
    fprintf(fid,"Mean center error: %.9f m\n",maeComputed(k));
    fprintf(fid,"Mean signed X error: %.9f m\n",bias(k,1));
    fprintf(fid,"Mean signed Y error: %.9f m\n\n",bias(k,2));
end

fprintf(fid,"Radar relative RMSE reduction: %.6f percent\n\n", ...
    100*(rmseComputed(1)-rmseComputed(2))/rmseComputed(1));

fprintf(fid,"IMPORTANT LIMITATIONS:\n");
fprintf(fid,"- Ground-truth coordinate transformation remains preliminary.\n");
fprintf(fid,"- GT target identity is evaluation-only.\n");
fprintf(fid,"- GT object-center versus visible LiDAR surface bias is uncorrected.\n");
fprintf(fid,"- Camera update is experimental and not authorized.\n");
fprintf(fid,"- GT actor velocity has six integrity warnings.\n");
fprintf(fid,"- Diagnostic center-position RMSE is not detection precision/recall.\n");
fprintf(fid,"- No official validated perception-accuracy claim is made.\n");
fprintf(fid,"- No FPGA speedup or board energy was measured.\n");

fclose(fid);

disp("PLOTS_GENERATED: 4");
disp("POSITION_ERROR_ANALYSIS: DIAGNOSTIC_ONLY");
disp("OFFICIAL_PERCEPTION_ACCURACY_VALIDATED: NO");
disp("ENERGY_MEASURED: NO");
disp("TASK26_6C2_EKF_MATLAB_ANALYSIS_PASS");
disp("REPORT: " + reportPath);
disp("PLOTS: " + plotDir);
