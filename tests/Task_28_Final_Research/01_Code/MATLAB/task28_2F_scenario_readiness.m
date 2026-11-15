% ============================================================
% GEMSTAR TASK 28.2F
% Scenario readiness and recording-pair visualization
% ============================================================

clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';
task = fullfile(root, 'tests', 'Task_28_Final_Research');

dataDir = fullfile(task, '02_CSV_Data');
plotDir = fullfile(task, '04_Plots', 'Scenario_Readiness');

if ~exist(plotDir, 'dir')
    mkdir(plotDir);
end

scenarioFile = fullfile(dataDir, ...
    'task28_2E_scenario_readiness_audit.csv');

pairFile = fullfile(dataDir, ...
    'task28_2E_recording_pair_status.csv');

assert(isfile(scenarioFile), 'Scenario audit CSV missing.');
assert(isfile(pairFile), 'Recording-pair CSV missing.');

T = readtable(scenarioFile, 'TextType', 'string');
P = readtable(pairFile, 'TextType', 'string');

names = string(T.Scenario);

osi = str2double(string(T.OSIFiles));
gt  = str2double(string(T.GTFiles));
sv  = str2double(string(T.SVFiles));

existsFlag = strcmpi(strtrim(string(T.FolderExists)), "True");
scenarioVerified = strcmpi( ...
    strtrim(string(T.ScenarioVerified)), "YES");
sensorVerified = strcmpi( ...
    strtrim(string(T.SensorVerified)), "YES");

candidate = existsFlag & gt > 0 & sv > 0;
fullyVerified = candidate & scenarioVerified & sensorVerified;

n = height(T);

fprintf('\n=== TASK 28.2F ===\n');
fprintf('Scenario folders: %d\n', n);
fprintf('Existing folders: %d\n', sum(existsFlag));
fprintf('GT/SV candidate scenarios: %d\n', sum(candidate));
fprintf('Fully verified: %d\n', sum(fullyVerified));

%% Figure 1: Sensor recording availability

fig1 = figure('Color','w', ...
    'Name','Scenario Recording Availability', ...
    'Position',[100 100 1200 650]);

bar(categorical(names, names), [osi gt sv], 'grouped');
grid on;

ylabel('Files reported in manifest');
xlabel('GEMSTAR scenario');
title('Task 28.2F - OSI / GT / SV Inventory');
legend({'OSI','GT','SV'}, 'Location','best');

xtickangle(35);

savefig(fig1, fullfile(plotDir, ...
    'task28_2F_recording_availability.fig'));

exportgraphics(fig1, fullfile(plotDir, ...
    'task28_2F_recording_availability.png'), ...
    'Resolution',300);

%% Figure 2: Readiness classification

% 0 = Missing GT/SV or folder
% 1 = Candidate, not fully verified
% 2 = Fully verified

readiness = zeros(n,1);
readiness(candidate) = 1;
readiness(fullyVerified) = 2;

fig2 = figure('Color','w', ...
    'Name','Scenario Readiness', ...
    'Position',[120 120 1150 600]);

bar(categorical(names, names), readiness);
grid on;

ylim([0 2.4]);
yticks([0 1 2]);
yticklabels({'Not ready','Candidate','Verified'});

xlabel('Scenario');
ylabel('Readiness classification');
title('Task 28.2F - Dataset Readiness Status');

xtickangle(35);

savefig(fig2, fullfile(plotDir, ...
    'task28_2F_readiness.fig'));

exportgraphics(fig2, fullfile(plotDir, ...
    'task28_2F_readiness.png'), ...
    'Resolution',300);

%% Figure 3: Recording pair status

status = upper(strtrim(string(P.Status)));
paired = strcmp(status, "PAIRED");

fig3 = figure('Color','w', ...
    'Name','GT/SV Recording Pair Status');

bar([sum(paired), sum(~paired)]);
grid on;

xticks([1 2]);
xticklabels({'PAIRED','OTHER'});
ylabel('Recording IDs');
title('Task 28.2F - GT/SV Pair Manifest');

savefig(fig3, fullfile(plotDir, ...
    'task28_2F_pair_status.fig'));

exportgraphics(fig3, fullfile(plotDir, ...
    'task28_2F_pair_status.png'), ...
    'Resolution',300);

%% Figure 4: Summary of scenario readiness

fig4 = figure('Color','w', ...
    'Name','Readiness Summary');

counts = [
    sum(fullyVerified)
    sum(candidate & ~fullyVerified)
    sum(~candidate)
];

bar(counts);
grid on;

xticks(1:3);
xticklabels({'Fully verified','Candidate','Not ready'});
ylabel('Number of scenarios');
title('Task 28.2F - Scenario Inventory Summary');

savefig(fig4, fullfile(plotDir, ...
    'task28_2F_summary.fig'));

exportgraphics(fig4, fullfile(plotDir, ...
    'task28_2F_summary.png'), ...
    'Resolution',300);

%% Save classification CSV

result = table( ...
    names, existsFlag, osi, gt, sv, ...
    candidate, scenarioVerified, sensorVerified, ...
    fullyVerified, readiness, ...
    'VariableNames', { ...
    'Scenario','FolderExists','OSIFiles','GTFiles', ...
    'SVFiles','Candidate','ScenarioVerified', ...
    'SensorVerified','FullyVerified','ReadinessCode'});

outputCSV = fullfile(dataDir, ...
    'task28_2F_scenario_classification.csv');

writetable(result, outputCSV);

fprintf('\nPAIR STATUS:\n');
fprintf('Paired IDs: %d / %d\n', sum(paired),height(P));

fprintf('\nSCENARIO CLASSIFICATION:\n');
disp(result(:, {'Scenario','Candidate','FullyVerified'}));

fprintf('\nCSV: %s\n', outputCSV);
fprintf('Plots: %s\n', plotDir);
fprintf('\nTASK 28.2F COMPLETE\n');
