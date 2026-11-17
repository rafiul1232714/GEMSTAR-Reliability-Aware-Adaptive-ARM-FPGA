%% GEMSTAR TASK 29.2B.4
% Integrated LiDAR-Radar CPU latency model visualization
% Uses real Task 29.2B.3 model predictions and metrics.
% Saves 4 PNG and 4 MATLAB FIG files.

clearvars;
clc;
close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_29_Final_Research';

dataDir = fullfile(root,'02_CSV_Data');
outDir = fullfile(root,'01_Graphs');

predictionFile = fullfile(dataDir, ...
    'task29_2B3_integrated_model_predictions.csv');

metricsFile = fullfile(dataDir, ...
    'task29_2B3_integrated_model_metrics.csv');

P = readtable(predictionFile,'TextType','string');
M = readtable(metricsFile,'TextType','string');

assert(height(P)==159,'Expected 159 prediction rows');
assert(height(M)==9,'Expected 9 metric rows');

numP = ["Frame","ActualMs","PredictedMs", ...
    "ResidualMs","LiDARInputPoints", ...
    "LiDARFilteredPoints","RadarInputReturns"];

for j = 1:numel(numP)
    name = numP(j);

    if ~isnumeric(P.(name))
        P.(name) = str2double(string(P.(name)));
    end

    assert(all(isfinite(P.(name))), ...
        'Invalid prediction column: %s',char(name));
end

numM = ["MAE_Ms","RMSE_Ms","Bias_Ms","MaxAE_Ms"];

for j = 1:numel(numM)
    name = numM(j);

    if ~isnumeric(M.(name))
        M.(name) = str2double(string(M.(name)));
    end

    assert(all(isfinite(M.(name))), ...
        'Invalid metrics column: %s',char(name));
end

P.Model = string(P.Model);
P.Split = string(P.Split);
M.Model = string(M.Model);
M.Split = string(M.Split);

models = ["constant","input_only","stage_aware"];
names = ["Constant baseline","Input-only ridge", ...
         "Stage-aware ridge"];

colors = [0.48 0.48 0.48;
          0.15 0.42 0.78;
          0.12 0.62 0.38];

%% FIGURE 1 - Actual vs predicted latency by frame

f1 = figure('Color','w','Position',[100 100 1100 600]);
hold on;

reference = P(P.Model=="constant",:);
reference = sortrows(reference,'Frame');

plot(reference.Frame,reference.ActualMs, ...
    'k-','LineWidth',2.2,'DisplayName','Measured median');

for k=1:3

    D = P(P.Model==models(k),:);
    D = sortrows(D,'Frame');

    plot(D.Frame,D.PredictedMs, ...
        'LineWidth',1.5,'Color',colors(k,:), ...
        'DisplayName',char(names(k)));
end

xlabel('Frame ID');
ylabel('Integrated CPU latency (ms)');
title('GEMSTAR - Actual vs predicted integrated latency');
legend('Location','best');
grid on;
box on;
hold off;

savefig(f1,fullfile(outDir, ...
    'task29_2B4_integrated_predictions.fig'));

exportgraphics(f1,fullfile(outDir, ...
    'task29_2B4_integrated_predictions.png'), ...
    'Resolution',300);

%% FIGURE 2 - Test MAE and RMSE comparison

f2 = figure('Color','w','Position',[100 100 1050 600]);

testMetrics = M(M.Split=="test",:);

mae = zeros(1,3);
rmse = zeros(1,3);

for k=1:3

    r = testMetrics(testMetrics.Model==models(k),:);

    assert(height(r)==1, ...
        'Missing test metrics for %s',char(models(k)));

    mae(k) = r.MAE_Ms * 1000;
    rmse(k) = r.RMSE_Ms * 1000;
end

b = bar([mae;rmse]');
b(1).DisplayName = 'MAE';
b(2).DisplayName = 'RMSE';

set(gca,'XTick',1:3,'XTickLabel',cellstr(names));
ylabel('Prediction error (microseconds)');
title('GEMSTAR - Held-out test error comparison');
legend('Location','best');
grid on;
box on;

savefig(f2,fullfile(outDir, ...
    'task29_2B4_integrated_model_errors.fig'));

exportgraphics(f2,fullfile(outDir, ...
    'task29_2B4_integrated_model_errors.png'), ...
    'Resolution',300);

%% FIGURE 3 - Residuals by frame

f3 = figure('Color','w','Position',[100 100 1100 600]);
hold on;

for k=1:3

    D = P(P.Model==models(k),:);
    D = sortrows(D,'Frame');

    scatter(D.Frame,1000*D.ResidualMs, ...
        35,colors(k,:),'filled', ...
        'DisplayName',char(names(k)));
end

yline(0,'k--','LineWidth',1.2);

xlabel('Frame ID');
ylabel('Actual - predicted (microseconds)');
title('GEMSTAR - Integrated latency residuals');
legend('Location','best');
grid on;
box on;
hold off;

savefig(f3,fullfile(outDir, ...
    'task29_2B4_integrated_residuals.fig'));

exportgraphics(f3,fullfile(outDir, ...
    'task29_2B4_integrated_residuals.png'), ...
    'Resolution',300);

%% FIGURE 4 - Workload vs measured latency

f4 = figure('Color','w','Position',[100 100 1050 600]);
hold on;

splits = ["train","validation","test"];

splitColors = [0.15 0.55 0.32;
               0.95 0.55 0.12;
               0.15 0.40 0.80];

for k=1:3

    mask = reference.Split==splits(k);

    scatter(reference.LiDARInputPoints(mask), ...
        reference.ActualMs(mask), ...
        65,splitColors(k,:),'filled', ...
        'DisplayName',char(splits(k)));
end

xlabel('LiDAR input point count');
ylabel('Integrated CPU median latency (ms)');
title('GEMSTAR - Measured latency vs LiDAR workload');
legend('Location','best');
grid on;
box on;
hold off;

savefig(f4,fullfile(outDir, ...
    'task29_2B4_integrated_workload.fig'));

exportgraphics(f4,fullfile(outDir, ...
    'task29_2B4_integrated_workload.png'), ...
    'Resolution',300);

%% FINAL REPORT

fprintf('\n=== TASK 29.2B.4: TEST MODEL PERFORMANCE ===\n');

for k=1:3
    fprintf('%s | MAE %.4f us | RMSE %.4f us\n', ...
        char(names(k)),mae(k),rmse(k));
end

[bestMAE,index] = min(mae);

fprintf('\nLowest TEST MAE: %s (%.4f us)\n', ...
    char(names(index)),bestMAE);

fprintf('\nImportant: test contains only one distinct workload.\n');
fprintf('Lowest test error does not prove generalization.\n');

fprintf('\nTASK 29.2B.4: COMPLETE\n');
fprintf('Saved 4 PNG and 4 FIG files in:\n%s\n',outDir);
