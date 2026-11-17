%% GEMSTAR Task 29.2A.4 - LiDAR CPU latency research plots
% Source: Task 29.2A.2 measured benchmark predictions.
% Four figures saved as PNG and editable MATLAB FIG.

clearvars;
clc;
close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_29_Final_Research';
csvFile = fullfile(root,'02_CSV_Data', ...
    'task29_2A2_lidar_cpu_predictions.csv');
outDir = fullfile(root,'01_Graphs');

if ~exist(outDir,'dir')
    mkdir(outDir);
end

T = readtable(csvFile,'TextType','string');

assert(height(T)==106,'Expected 106 prediction rows');

% Ensure numeric data even if MATLAB imported some columns as strings.
numericColumns = ["Frame","Workload","ActualMs", ...
                  "PredictedMs","AbsoluteErrorMs"];

for j = 1:numel(numericColumns)
    c = numericColumns(j);
    if ~isnumeric(T.(c))
        T.(c) = str2double(string(T.(c)));
    end
    assert(all(isfinite(T.(c))), ...
        "Invalid numeric values in column " + c);
end

stages = ["filter","cluster"];
splits = ["train","validation","test"];

colors = [0.15 0.55 0.32;
          0.95 0.53 0.12;
          0.15 0.40 0.80];

for s = 1:numel(stages)

    stage = stages(s);
    D = T(string(T.Stage)==stage,:);

    assert(height(D)==53, ...
        "Expected 53 rows for stage " + stage);

    % ----- FIGURE 1: Workload vs measured/predicted latency -----
    f1 = figure('Color','w','Position',[100 100 1000 580]);
    hold on;

    for k = 1:3
        mask = string(D.Split)==splits(k);

        scatter(D.Workload(mask),D.ActualMs(mask), ...
            65,colors(k,:),'filled', ...
            'DisplayName',char(splits(k) + " actual"));
    end

    [xSorted,order] = sort(D.Workload);

    plot(xSorted,D.PredictedMs(order),'k-', ...
        'LineWidth',2, ...
        'DisplayName','Linear prediction');

    xlabel('LiDAR point count');
    ylabel('Median CPU execution time (ms)');
    title("Task 29 - LiDAR " + stage + ...
          ": Measured vs predicted latency");

    legend('Location','best');
    grid on;
    box on;
    hold off;

    fileBase = char("task29_2A4_" + stage + "_latency");

    savefig(f1,fullfile(outDir,[fileBase '.fig']));
    exportgraphics(f1,fullfile(outDir,[fileBase '.png']), ...
        'Resolution',300);

    % ----- FIGURE 2: Residual errors by frame -----
    f2 = figure('Color','w','Position',[120 120 1000 580]);
    hold on;

    for k = 1:3
        mask = string(D.Split)==splits(k);

        residualUs = 1000 * ...
            (D.ActualMs(mask)-D.PredictedMs(mask));

        scatter(D.Frame(mask),residualUs, ...
            65,colors(k,:),'filled', ...
            'DisplayName',char(splits(k)));
    end

    yline(0,'k--','LineWidth',1.5);

    xlabel('Frame ID');
    ylabel('Residual: actual - predicted (microseconds)');
    title("Task 29 - LiDAR " + stage + ...
          ": Prediction residuals");

    legend('Location','best');
    grid on;
    box on;
    hold off;

    fileBase = char("task29_2A4_" + stage + "_residuals");

    savefig(f2,fullfile(outDir,[fileBase '.fig']));
    exportgraphics(f2,fullfile(outDir,[fileBase '.png']), ...
        'Resolution',300);

    % ----- Print summary -----
    fprintf('\nSTAGE: %s\n',char(stage));

    for k = 1:3
        mask = string(D.Split)==splits(k);

        maeUs = 1000 * mean(abs( ...
            D.ActualMs(mask)-D.PredictedMs(mask)));

        nWorkloads = numel(unique(D.Workload(mask)));

        fprintf('%s: %d frames | %d unique workloads | MAE %.4f us\n', ...
            char(splits(k)),sum(mask),nWorkloads,maeUs);
    end
end

fprintf('\nTASK 29.2A.4: COMPLETE\n');
fprintf('All plots saved to:\n%s\n',outDir);
fprintf('Total: 4 PNG + 4 FIG files\n');
