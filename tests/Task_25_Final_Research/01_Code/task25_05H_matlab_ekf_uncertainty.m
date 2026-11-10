%% TASK 25.5H - MATLAB EKF UNCERTAINTY ANALYSIS
% GEMSTAR research - validated observational diagnostics.
% Does not modify source CSVs.

clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_25_Final_Research';
dataDir = fullfile(root,'02_CSV_Data');
plotDir = fullfile(root,'04_Plots');
findDir = fullfile(root,'06_Research_Findings');

if ~exist(plotDir,'dir'), mkdir(plotDir); end
if ~exist(findDir,'dir'), mkdir(findDir); end

%% 1. Load validated datasets
N = readtable(fullfile(dataDir, ...
    'task25_43_validated_radar_nis.csv'), ...
    'TextType','string');

R = readtable(fullfile(dataDir, ...
    'task25_40_ekf_consistency_audit.csv'), ...
    'TextType','string');

assert(height(N)==24, 'Expected 24 NIS records');
assert(height(R)==23, 'Expected 23 residual records');

nisFrame = str2double(string(N.Frame));
nisStatus = string(N.Radar_Status);
nisValid = strcmpi(strtrim(string(N.NIS_Valid)),'true');
nisValue = str2double(string(N.Radar_NIS));

assert(all(isfinite(nisFrame)), ...
    'Invalid Radar frame identifiers');

assert(numel(unique(nisFrame))==24, ...
    'Duplicate Radar frame identifiers');

assert(nnz(nisValid)==4, ...
    'Expected exactly four valid NIS values');

assert(all(isfinite(nisValue(nisValid))) && ...
    all(nisValue(nisValid)>=0), ...
    'Invalid finite NIS value');

assert(all(nisStatus(nisValid)=="ACCEPTED"), ...
    'Valid NIS and accepted statuses disagree');

assert(nnz(nisStatus=="NOT_AVAILABLE")==19 && ...
    nnz(nisStatus=="INSUFFICIENT_RETURNS")==1, ...
    'Radar status distribution mismatch');

assert(all(~isfinite(nisValue(~nisValid))), ...
    'Unexpected NIS value marked unavailable');

gtFrame = str2double(string(R.Frame));
lidarResidual = str2double(string(R.LiDAR_ResidualX_m));
radarResidual = str2double(string(R.Radar_ResidualX_m));
lidarSigma = str2double(string(R.LiDAR_SigmaX_m));
radarSigma = str2double(string(R.Radar_SigmaX_m));

assert(numel(unique(gtFrame))==23 && ...
    all(ismember(gtFrame,nisFrame)), ...
    'GT frame alignment mismatch');

assert(all(isfinite([lidarResidual;radarResidual; ...
    lidarSigma;radarSigma])), ...
    'Nonfinite residual or uncertainty');

assert(all(lidarSigma>0) && all(radarSigma>0), ...
    'Uncertainty sigma must be positive');

lidarRatio = abs(lidarResidual)./lidarSigma;
radarRatio = abs(radarResidual)./radarSigma;

fprintf('\nTASK 25.5H - INPUT VALIDATION\n');
fprintf('Valid Radar NIS: %d\n',nnz(nisValid));
fprintf('GT residual observations: %d\n',height(R));
disp('TASK25_05H_INPUT_VALIDATION_PASS');

%% 2. Figure 1 - Radar NIS
f1 = figure('Color','w','Position',[100 100 1100 600]);

stem(nisFrame(nisValid),nisValue(nisValid), ...
    'filled','LineWidth',1.8,'MarkerSize',8);

grid on;
xlabel('Original GEMSTAR frame index');
ylabel('Normalized Innovation Squared (NIS)');
title('Task 25.5 - Valid Radar EKF NIS Measurements');

xlim([min(nisFrame)-20 max(nisFrame)+20]);
ylim([0 max(nisValue(nisValid))*1.35]);

text(0.02,0.96, ...
    'Only 4 accepted updates have finite NIS; gate threshold not plotted', ...
    'Units','normalized','VerticalAlignment','top', ...
    'FontSize',10);

exportgraphics(f1,fullfile(plotDir, ...
    'task25_44_matlab_radar_nis.png'), ...
    'Resolution',300);

exportgraphics(f1,fullfile(plotDir, ...
    'task25_44_matlab_radar_nis.pdf'), ...
    'ContentType','vector');

disp('FIGURE_1_SAVED');

%% 3. Figure 2 - Signed residuals and 1-sigma bounds
f2 = figure('Color','w','Position',[110 110 1200 780]);

subplot(2,1,1);
plot(gtFrame,lidarResidual,'-o','LineWidth',1.5);
hold on;
plot(gtFrame,lidarSigma,'--','LineWidth',1.2);
plot(gtFrame,-lidarSigma,'--','LineWidth',1.2);
yline(0,':');
hold off;
grid on;
ylabel('X-position (m)');
title('LiDAR: signed GT-center X residual versus reported 1 sigma');
legend('Signed residual','+1 sigma','-1 sigma','Zero', ...
    'Location','best');

subplot(2,1,2);
plot(gtFrame,radarResidual,'-o','LineWidth',1.5);
hold on;
plot(gtFrame,radarSigma,'--','LineWidth',1.2);
plot(gtFrame,-radarSigma,'--','LineWidth',1.2);
yline(0,':');
hold off;
grid on;
xlabel('Original GEMSTAR frame index');
ylabel('X-position (m)');
title('Radar EKF: signed GT-center X residual versus reported 1 sigma');
legend('Signed residual','+1 sigma','-1 sigma','Zero', ...
    'Location','best');

exportgraphics(f2,fullfile(plotDir, ...
    'task25_45_matlab_residual_sigma.png'), ...
    'Resolution',300);

exportgraphics(f2,fullfile(plotDir, ...
    'task25_45_matlab_residual_sigma.pdf'), ...
    'ContentType','vector');

disp('FIGURE_2_SAVED');

%% 4. Figure 3 - Normalized absolute residual
f3 = figure('Color','w','Position',[120 120 1150 640]);

plot(gtFrame,lidarRatio,'-o','LineWidth',1.5);
hold on;
plot(gtFrame,radarRatio,'-s','LineWidth',1.5);
yline(1,'--','1 sigma reference','LineWidth',1.4);
hold off;
grid on;

xlabel('Original GEMSTAR frame index');
ylabel('|X residual| / reported sigma X');
title('Task 25.5 - Normalized GT-Center X Residuals');

legend('LiDAR','Radar EKF','1 sigma reference', ...
    'Location','best');

exportgraphics(f3,fullfile(plotDir, ...
    'task25_46_matlab_normalized_residual.png'), ...
    'Resolution',300);

exportgraphics(f3,fullfile(plotDir, ...
    'task25_46_matlab_normalized_residual.pdf'), ...
    'ContentType','vector');

disp('FIGURE_3_SAVED');

%% 5. Print numerical findings
fprintf('\n=== TASK 25.5H SCIENTIFIC FINDINGS ===\n');
fprintf('Radar accepted NIS values: %d\n',nnz(nisValid));

fprintf('LiDAR mean signed X residual: %.6f m\n', ...
    mean(lidarResidual));
fprintf('Radar mean signed X residual: %.6f m\n', ...
    mean(radarResidual));

fprintf('LiDAR mean reported sigma X: %.6f m\n', ...
    mean(lidarSigma));
fprintf('Radar mean reported sigma X: %.6f m\n', ...
    mean(radarSigma));

fprintf('LiDAR residual > 1 sigma: %d / %d\n', ...
    nnz(lidarRatio>1),numel(lidarRatio));

fprintf('Radar residual > 1 sigma: %d / %d\n', ...
    nnz(radarRatio>1),numel(radarRatio));

%% 6. Save research findings
findPath = fullfile(findDir, ...
    'task25_47_matlab_uncertainty_findings.txt');

fid = fopen(findPath,'w');
assert(fid>0,'Cannot create research findings');

fprintf(fid,'TASK 25.5H - EKF UNCERTAINTY DIAGNOSTICS\n\n');
fprintf(fid,'Valid Radar NIS: %d of 24 observations\n',nnz(nisValid));
fprintf(fid,'GT X residual observations: %d\n',height(R));
fprintf(fid,'LiDAR mean signed X residual: %.9f m\n',mean(lidarResidual));
fprintf(fid,'Radar mean signed X residual: %.9f m\n',mean(radarResidual));
fprintf(fid,'LiDAR mean reported sigma X: %.9f m\n',mean(lidarSigma));
fprintf(fid,'Radar mean reported sigma X: %.9f m\n',mean(radarSigma));
fprintf(fid,'LiDAR |residual| > sigma: %d of 23\n',nnz(lidarRatio>1));
fprintf(fid,'Radar |residual| > sigma: %d of 23\n',nnz(radarRatio>1));

fprintf(fid,'\nLIMITATIONS\n');
fprintf(fid,'NIS has only four accepted Radar measurements.\n');
fprintf(fid,'NIS gate threshold was not independently verified.\n');
fprintf(fid,'GT-center versus sensed-surface geometry may create bias.\n');
fprintf(fid,'One trajectory does not establish statistical calibration.\n');
fprintf(fid,'X residual divided by sigma is not full-state NEES.\n');
fprintf(fid,'No full covariance matrix was established.\n');
fprintf(fid,'No original measurements were bias-corrected.\n');
fprintf(fid,'TASK25_05H_MATLAB_PASS\n');
fclose(fid);

%% 7. Verify exported files
outputs = {
    'task25_44_matlab_radar_nis.png'
    'task25_44_matlab_radar_nis.pdf'
    'task25_45_matlab_residual_sigma.png'
    'task25_45_matlab_residual_sigma.pdf'
    'task25_46_matlab_normalized_residual.png'
    'task25_46_matlab_normalized_residual.pdf'
};

for k=1:numel(outputs)
    info=dir(fullfile(plotDir,outputs{k}));
    assert(~isempty(info) && info.bytes>0, ...
        ['Missing or empty figure: ',outputs{k}]);
end

info=dir(findPath);
assert(~isempty(info) && info.bytes>0, ...
    'Missing or empty research findings');

fprintf('\nFIGURE_FILES_VERIFIED: %d\n',numel(outputs));
disp('TASK25_05H_MATLAB_PASS');
disp(['Saved to: ',plotDir]);
