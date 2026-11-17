%% GEMSTAR Task 29.3C.3 - Controlled YOLO model comparison
% Uses existing measured CPU benchmark data only.
% Saves four publication-style figures as PNG and MATLAB FIG.
% Detection counts are NOT detection accuracy.

clearvars; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_29_Final_Research';
dataDir = fullfile(root,'02_CSV_Data');
outDir = fullfile(root,'01_Graphs');

S = readtable(fullfile(dataDir, ...
    'task29_3C1_yolo_comparison_summary.csv'),'TextType','string');

R = readtable(fullfile(dataDir, ...
    'task29_3C1_yolo_comparison_raw.csv'),'TextType','string');

assert(height(S)==40,'Expected 40 model-image summaries');
assert(height(R)==400,'Expected 400 raw measurements');

fieldsS = ["Frame","MedianMs","P95Ms","P99Ms","Detections"];
fieldsR = ["Frame","Repeat","ElapsedMs","Detections"];

for c = fieldsS
    if ~isnumeric(S.(c))
        S.(c) = str2double(string(S.(c)));
    end
    assert(all(isfinite(S.(c))), ...
        'Invalid summary field: %s',char(c));
end

for c = fieldsR
    if ~isnumeric(R.(c))
        R.(c) = str2double(string(R.(c)));
    end
    assert(all(isfinite(R.(c))), ...
        'Invalid raw field: %s',char(c));
end

S.Model = string(S.Model);
S.Scenario = string(S.Scenario);
R.Model = string(R.Model);
R.Scenario = string(R.Scenario);

scenarios = ["baseline_clear", ...
    "baseline_fog_working_radar", ...
    "fog_mor100", ...
    "fog_postfix_validation"];

shortNames = {'Clear','Fog + radar','Fog MOR100','Fog postfix'};

% Pair exactly the same image in both models.
N = S(S.Model=="yolo11n",:);
D = S(S.Model=="yolo11s",:);

N = sortrows(N,{'Scenario','Frame'});
D = sortrows(D,{'Scenario','Frame'});

assert(height(N)==20 && height(D)==20, ...
    'Expected 20 images per model');

assert(isequal(N.Scenario,D.Scenario) && ...
    isequal(N.Frame,D.Frame), ...
    'YOLO image pairs do not match');

% Arrange consistently by scenario then increasing frame.
order = zeros(20,1);
p = 1;
for k=1:numel(scenarios)
    idx = find(N.Scenario==scenarios(k));
    [~,loc] = sort(N.Frame(idx));
    idx = idx(loc);
    order(p:p+numel(idx)-1) = idx;
    p = p+numel(idx);
end

N = N(order,:);
D = D(order,:);

blue = [0.16 0.42 0.78];
orange = [0.91 0.46 0.13];
x = (1:20)';

%% Figure 1 - Paired image median latency
f1 = figure('Color','w','Position',[100 100 1100 600]);

plot(x,N.MedianMs,'-o','Color',blue, ...
    'LineWidth',1.8,'MarkerSize',5);
hold on;
plot(x,D.MedianMs,'-s','Color',orange, ...
    'LineWidth',1.8,'MarkerSize',5);

xlabel('Matched Camera image (ordered by scenario)');
ylabel('Median CPU prediction time (ms)');
title('Task 29 - YOLO11n vs YOLO11s: Paired latency');
legend('YOLO11n','YOLO11s','Location','best');
xticks(1:20);
xlim([0.5 20.5]);
grid on; box on;
hold off;

%% Figure 2 - Scenario mean of image medians
scenarioLatency = zeros(4,2);
scenarioRows = table();

for k=1:4
    n = N.MedianMs(N.Scenario==scenarios(k));
    d = D.MedianMs(D.Scenario==scenarios(k));

    assert(numel(n)==5 && numel(d)==5, ...
        'Expected 5 matched images per scenario');

    scenarioLatency(k,:) = [mean(n),mean(d)];

    newRow = table(scenarios(k),numel(n),mean(n),mean(d), ...
        'VariableNames',{'Scenario','Images','YOLO11nMeanMedianMs', ...
                         'YOLO11sMeanMedianMs'});
    scenarioRows = [scenarioRows;newRow];
end

f2 = figure('Color','w','Position',[100 100 1100 600]);
b = bar(scenarioLatency,'grouped');
b(1).FaceColor = blue;
b(2).FaceColor = orange;

xticks(1:4);
xticklabels(shortNames);
ylabel('Mean of per-image median latency (ms)');
title('Task 29 - Camera AI latency across recordings');
legend('YOLO11n','YOLO11s','Location','best');
grid on; box on;

writetable(scenarioRows,fullfile(dataDir, ...
    'task29_3C3_yolo_scenario_latency.csv'));

%% Figure 3 - All 400 raw timing observations
f3 = figure('Color','w','Position',[100 100 1000 600]);

rN = R(R.Model=="yolo11n",:);
rS = R(R.Model=="yolo11s",:);

assert(height(rN)==200 && height(rS)==200, ...
    'Expected 200 timing observations per model');

scatter(ones(height(rN),1)+0.12*(rN.Repeat-5.5)/10, ...
    rN.ElapsedMs,20,blue,'filled', ...
    'MarkerFaceAlpha',0.35);
hold on;

scatter(2+0.12*(rS.Repeat-5.5)/10, ...
    rS.ElapsedMs,20,orange,'filled', ...
    'MarkerFaceAlpha',0.35);

xlim([0.5 2.5]);
xticks([1 2]);
xticklabels({'YOLO11n','YOLO11s'});
ylabel('CPU prediction time (ms)');
title('Task 29 - Distribution of 400 timing observations');
grid on; box on;
hold off;

%% Figure 4 - Detections per image (not accuracy)
f4 = figure('Color','w','Position',[100 100 1100 600]);

b = bar(x,[N.Detections,D.Detections],'grouped');
b(1).FaceColor = blue;
b(2).FaceColor = orange;

xlabel('Matched Camera image (ordered by scenario)');
ylabel('Number of reported detections');
title('Task 29 - Detection counts (NOT ground-truth accuracy)');
legend('YOLO11n','YOLO11s','Location','best');
xticks(1:20);
xlim([0.5 20.5]);
grid on; box on;

%% Automatically save all figures
figures = {f1,f2,f3,f4};

names = {
    'task29_3C3_yolo_paired_latency'
    'task29_3C3_yolo_scenario_latency'
    'task29_3C3_yolo_raw_timing'
    'task29_3C3_yolo_detection_counts'
};

for k=1:4
    figPath = fullfile(outDir,[names{k} '.fig']);
    pngPath = fullfile(outDir,[names{k} '.png']);

    savefig(figures{k},figPath);
    exportgraphics(figures{k},pngPath,'Resolution',300);

    assert(isfile(figPath) && isfile(pngPath), ...
        'Figure save failed: %s',names{k});

    fprintf('SAVED: %s\n',names{k});
end

%% Results
medianN = median(N.MedianMs);
medianS = median(D.MedianMs);

fprintf('\n=== TASK 29.3C.3: RESEARCH RESULTS ===\n');
fprintf('YOLO11n median of image medians: %.4f ms\n',medianN);
fprintf('YOLO11s median of image medians: %.4f ms\n',medianS);
fprintf('YOLO11s / YOLO11n ratio: %.4fx\n',medianS/medianN);
fprintf('YOLO11n detections: %d\n',sum(N.Detections));
fprintf('YOLO11s detections: %d\n',sum(D.Detections));
fprintf('Unique matched images: %d\n',height(N));
fprintf('Timing observations: %d\n',height(R));

fprintf('\nTASK 29.3C.3: PASS\n');
fprintf('Saved 4 PNG and 4 FIG figures in:\n%s\n',outDir);
