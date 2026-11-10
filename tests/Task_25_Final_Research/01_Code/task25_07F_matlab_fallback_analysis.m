%% TASK 25.7F - MATLAB FALLBACK ANALYSIS
% Offline policy classifications only.
% No validated perception quality or hardware energy claims.

clearvars; close all; clc;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_25_Final_Research';
dataDir = fullfile(root, '02_CSV_Data');
plotDir = fullfile(root, '04_Plots');
findDir = fullfile(root, '06_Research_Findings');

decisionPath = fullfile(dataDir, 'task25_65_fallback_decisions.csv');
summaryPath = fullfile(dataDir, 'task25_66_fallback_scenario_summary.csv');
auditPath = fullfile(dataDir, 'task25_67_fallback_decision_audit.csv');

assert(isfile(decisionPath), 'Missing fallback decisions');
assert(isfile(summaryPath), 'Missing scenario summary');
assert(isfile(auditPath), 'Missing decision audit');

D = readtable(decisionPath, 'TextType', 'string');
S = readtable(summaryPath, 'TextType', 'string');
A = readtable(auditPath, 'TextType', 'string');

assert(height(D) == 168, 'Expected 168 decisions');
assert(height(S) == 7, 'Expected seven scenarios');

issueRow = strcmp(string(A.Check), "ISSUE_COUNT");
assert(nnz(issueRow) == 1, 'Missing audit issue count');

issues = str2double(string(A.Count(issueRow)));

assert(issues == 0, 'Decision audit contains issues');

scenarios = string(S.scenario);
mode = strtrim(string(D.controller_mode));
scenarioCol = string(D.scenario);

normal = str2double(string(S.normal_candidate));
degraded = str2double(string(S.degraded_candidate));
holdCount = str2double(string(S.hold_or_alert));
samples = str2double(string(S.samples));

assert(all(isfinite([normal; degraded; holdCount; samples])), ...
    'Non-finite summary values');

assert(all(samples == 24), ...
    'Expected 24 samples per scenario');

assert(all(normal + degraded + holdCount == 24), ...
    'Scenario totals do not match');

assert(sum(normal) == 143 && ...
       sum(degraded) == 16 && ...
       sum(holdCount) == 9, ...
       'Unexpected fallback totals');

validModes = [
    "NORMAL_CANDIDATE"
    "DEGRADED_CANDIDATE"
    "HOLD_OR_ALERT"
];

assert(all(ismember(mode, validModes)), ...
    'Unexpected controller mode');

assert(all(string(D.quality_authorization) == "UNVERIFIED"), ...
    'Unexpected quality authorization');

if ~isfolder(plotDir)
    mkdir(plotDir);
end

if ~isfolder(findDir)
    mkdir(findDir);
end

%% FIGURE 1 - Scenario comparison

colors = [
    0.22 0.58 0.46
    0.95 0.65 0.20
    0.78 0.29 0.30
];

f1 = figure( ...
    'Color', 'w', ...
    'Position', [100 100 1320 700] ...
);

counts = [normal degraded holdCount];

b = bar(counts, 'stacked', 'BarWidth', 0.72);

for k = 1:3
    b(k).FaceColor = colors(k,:);
end

xticks(1:numel(scenarios));
xticklabels(strrep(cellstr(scenarios), '_', ' '));
xtickangle(28);

ylabel('Replay samples');
ylim([0 27]);
yticks(0:4:24);

grid on;

set(gca, ...
    'FontSize', 11, ...
    'GridAlpha', 0.12 ...
);

legend( ...
    {'Normal candidate', 'Degraded candidate', 'Hold or alert'}, ...
    'Location', 'northoutside', ...
    'Orientation', 'horizontal' ...
);

title('Task 25.7 - Fallback decisions by fault scenario');

subtitle( ...
    'Offline rule classifications; perception quality remains unverified' ...
);

p1 = fullfile( ...
    plotDir, ...
    'task25_68_matlab_fallback_scenario_comparison' ...
);

exportgraphics(f1, [p1 '.png'], 'Resolution', 300);

exportgraphics( ...
    f1, [p1 '.pdf'], 'ContentType', 'vector' ...
);

disp('FALLBACK_FIGURE_1_SAVED');

%% FIGURE 2 - Decision timeline

matrix = zeros(numel(scenarios), 24);

for i = 1:numel(scenarios)

    idx = find(scenarioCol == scenarios(i));

    assert(numel(idx) == 24, ...
        'Scenario does not have 24 decisions');

    sampleValues = str2double(string(D.sample(idx)));

    assert(all(isfinite(sampleValues)), ...
        'Invalid sample indices');

    assert(numel(unique(sampleValues)) == 24, ...
        'Duplicate sample indices');

    [~, order] = sort(sampleValues);

    idx = idx(order);

    for j = 1:24

        switch mode(idx(j))

            case "NORMAL_CANDIDATE"
                matrix(i,j) = 1;

            case "DEGRADED_CANDIDATE"
                matrix(i,j) = 2;

            case "HOLD_OR_ALERT"
                matrix(i,j) = 3;

            otherwise
                error('Unknown controller mode');

        end
    end
end

assert(nnz(matrix == 1) == 143);
assert(nnz(matrix == 2) == 16);
assert(nnz(matrix == 3) == 9);

f2 = figure( ...
    'Color', 'w', ...
    'Position', [100 100 1320 650] ...
);

imagesc(matrix);

colormap(f2, colors);
clim([0.5 3.5]);

axis tight;

yticks(1:numel(scenarios));
yticklabels(strrep(cellstr(scenarios), '_', ' '));

xticks(1:24);

xlabel('Replay sample order within scenario');
ylabel('Controlled fault scenario');

set(gca, ...
    'FontSize', 11, ...
    'TickLength', [0 0] ...
);

cb = colorbar;

cb.Ticks = [1 2 3];

cb.TickLabels = {
    'Normal candidate'
    'Degraded candidate'
    'Hold or alert'
};

title('Task 25.7 - Per-sample fallback decision timeline');

subtitle( ...
    'Sample order is not an independent sensor acquisition timestamp' ...
);

p2 = fullfile( ...
    plotDir, ...
    'task25_69_matlab_fallback_decision_timeline' ...
);

exportgraphics(f2, [p2 '.png'], 'Resolution', 300);

exportgraphics( ...
    f2, [p2 '.pdf'], 'ContentType', 'vector' ...
);

disp('FALLBACK_FIGURE_2_SAVED');

%% Verify exported figures

paths = {
    [p1 '.png']
    [p1 '.pdf']
    [p2 '.png']
    [p2 '.pdf']
};

for i = 1:numel(paths)

    assert(isfile(paths{i}), ...
        'Missing exported figure');

    info = dir(paths{i});

    assert(info.bytes > 0, ...
        'Exported figure is empty');
end

%% Save research findings

report = fullfile( ...
    findDir, ...
    'task25_70_matlab_fallback_findings.txt' ...
);

fid = fopen(report, 'w');

assert(fid > 0, ...
    'Cannot create MATLAB findings report');

fprintf(fid, 'TASK 25.7F - FALLBACK MATLAB FINDINGS\n');
fprintf(fid, 'SCENARIOS: %d\n', height(S));
fprintf(fid, 'REPLAY_SAMPLES: %d\n', height(D));
fprintf(fid, 'NORMAL_CANDIDATE: %d\n', sum(normal));
fprintf(fid, 'DEGRADED_CANDIDATE: %d\n', sum(degraded));
fprintf(fid, 'HOLD_OR_ALERT: %d\n', sum(holdCount));
fprintf(fid, 'QUALITY_AUTHORIZATION: UNVERIFIED\n');
fprintf(fid, 'ENERGY_SAVINGS_CLAIMED: NO\n');
fprintf(fid, 'INTERPRETATION: Offline policy classifications only.\n');
fprintf(fid, 'NOTE: Replay scenarios are not independent recordings.\n');
fprintf(fid, 'NOTE: Repeated payload is not proven sensor failure.\n');
fprintf(fid, 'NOTE: Accuracy and latency limits are not validated.\n');

fclose(fid);

assert(isfile(report), ...
    'MATLAB findings report missing');

%% Final verification

fprintf('\n=== TASK 25.7F MATLAB FALLBACK ANALYSIS ===\n');

fprintf('SCENARIOS_VERIFIED: %d\n', height(S));
fprintf('DECISIONS_VERIFIED: %d\n', height(D));
fprintf('NORMAL_CANDIDATE: %d\n', sum(normal));
fprintf('DEGRADED_CANDIDATE: %d\n', sum(degraded));
fprintf('HOLD_OR_ALERT: %d\n', sum(holdCount));
fprintf('FIGURE_FILES_VERIFIED: %d\n', numel(paths));
fprintf('QUALITY_AUTHORIZATION: UNVERIFIED\n');

fprintf('TASK25_07F_MATLAB_FALLBACK_PASS\n');
fprintf('Saved to: %s\n', plotDir);
