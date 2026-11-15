% ==========================================================
% GEMSTAR TASK 28.3B.6
% Full LiDAR identity + signal classification
% ==========================================================

clear;
clc;
close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';
task = fullfile(root,'tests','Task_28_Final_Research');

dataDir = fullfile(task,'02_CSV_Data');
plotDir = fullfile(task,'04_Plots','LiDAR_Identity_Validation');
findDir = fullfile(task,'06_Research_Findings');

if ~exist(plotDir,'dir'), mkdir(plotDir); end
if ~exist(findDir,'dir'), mkdir(findDir); end

auditFile = fullfile(dataDir, ...
    'task28_3B5_full_identity_audit.csv');

candidateFile = fullfile(dataDir, ...
    'task28_3A2_full_candidate_returns.csv');

assert(isfile(auditFile) && isfile(candidateFile), ...
    'Required Task 28 input CSV missing.');

A = readtable(auditFile);
C = readtable(candidateFile,'TextType','string');

F = C(C.Scenario == "fog_postfix_validation" & ...
      C.Sensor == "LiDAR",:);

assert(height(A)==705 && height(F)==705, ...
    'Expected 705 LiDAR frames.');

assert(isequal(A.Frame,(0:704)'), ...
    'Identity audit frame numbering mismatch.');

assert(isequal(F.Frame,A.Frame), ...
    'Candidate CSV frame alignment mismatch.');

assert(all(A.IdentityConsistent==1), ...
    'Identity verification failed.');

assert(all(A.RangeCandidates == F.CandidateReturns), ...
    'Candidate counts disagree between source CSVs.');

assert(all(A.PositiveSignalObjectID == ...
    F.PositiveSignalCandidates), ...
    'Positive-signal counts disagree.');

assert(all(A.ZeroSignalInvalidID + ...
    A.PositiveSignalObjectID == A.RangeCandidates), ...
    'Candidate classification totals disagree.');

assert(all(A.ZeroSignalObjectID==0) && ...
       all(A.ZeroSignalMissingID==0) && ...
       all(A.PositiveSignalInvalidOrMissingID==0) && ...
       all(A.OtherSignalCandidates==0), ...
       'Unexpected return-identity category.');

N = height(A);

rangeTotal = sum(A.RangeCandidates);
invalidTotal = sum(A.ZeroSignalInvalidID);
associatedTotal = sum(A.PositiveSignalObjectID);

assert(rangeTotal==1698619 && ...
       invalidTotal==996340 && ...
       associatedTotal==702279, ...
       'Unexpected full-recording totals.');

invalidPct = 100 * invalidTotal/rangeTotal;
associatedPct = 100 * associatedTotal/rangeTotal;

perFrameInvalidPct = ...
    100*A.ZeroSignalInvalidID./A.RangeCandidates;

perFrameAssociatedPct = ...
    100*A.PositiveSignalObjectID./A.RangeCandidates;

fprintf('\n=========================================\n');
fprintf('TASK 28.3B.6 - LIDAR IDENTITY ANALYSIS\n');
fprintf('=========================================\n');
fprintf('Frames: %d\n',N);
fprintf('Range candidates: %d\n',rangeTotal);
fprintf('Zero signal + invalid ID: %d (%.3f%%)\n', ...
    invalidTotal,invalidPct);
fprintf('Positive signal + object ID: %d (%.3f%%)\n', ...
    associatedTotal,associatedPct);

%% Figure 1: Per-frame return classes

f1 = figure('Color','w','Name','LiDAR Identity Timeline', ...
    'Position',[100 100 1100 550]);

plot(A.Frame,A.RangeCandidates,'LineWidth',1.2);
hold on;
plot(A.Frame,A.ZeroSignalInvalidID,'LineWidth',1.2);
plot(A.Frame,A.PositiveSignalObjectID,'LineWidth',1.2);

grid on;
xlabel('Frame');
ylabel('Reflection count');
title('Fog Postfix: LiDAR Range and Identity Classes');
legend('Range candidates', ...
    'Zero signal + invalid ID', ...
    'Positive signal + object ID','Location','best');

%% Figure 2: Per-frame fractions

f2 = figure('Color','w','Name','Identity Fractions', ...
    'Position',[120 120 1100 550]);

plot(A.Frame,perFrameInvalidPct,'LineWidth',1.2);
hold on;
plot(A.Frame,perFrameAssociatedPct,'LineWidth',1.2);

grid on;
ylim([0 100]);
xlabel('Frame');
ylabel('Percentage of range candidates');
title('Fog Postfix: LiDAR Identity Fractions');
legend('Zero signal + invalid ID', ...
    'Positive signal + object ID','Location','best');

%% Figure 3: Overall classification

f3 = figure('Color','w','Name','Identity Composition', ...
    'Position',[140 140 900 550]);

bar([invalidPct,associatedPct]);
grid on;
ylim([0 100]);
xticks(1:2);
xticklabels({'Zero + invalid ID', ...
             'Positive + object ID'});
ylabel('Percentage of total range candidates');
title('Fog Postfix: Full-Recording LiDAR Composition');

%% Figure 4: Distribution of object-associated returns

f4 = figure('Color','w','Name','Associated Return Distribution', ...
    'Position',[160 160 1050 560]);

histogram(A.PositiveSignalObjectID,30);
grid on;
xlabel('Positive-signal object-associated returns/frame');
ylabel('Number of frames');
title('Fog Postfix: Object-Associated Return Distribution');

%% Save statistics and figures without overwriting

statsFile = fullfile(dataDir, ...
    'task28_3B6_lidar_identity_statistics.csv');

reportFile = fullfile(findDir, ...
    'task28_3B6_lidar_identity_findings.txt');

figs = {f1,f2,f3,f4};
names = {
    'task28_3B6_identity_timeline'
    'task28_3B6_identity_fractions'
    'task28_3B6_identity_composition'
    'task28_3B6_associated_return_distribution'
};

assert(~isfile(statsFile) && ~isfile(reportFile), ...
    'Statistics or report already exists.');

for k = 1:numel(names)
    assert(~isfile(fullfile(plotDir,[names{k} '.png'])) && ...
           ~isfile(fullfile(plotDir,[names{k} '.fig'])), ...
           'A figure output already exists.');
end

Metric = [
    "Frames"
    "RangeCandidates"
    "ZeroSignalInvalidID"
    "PositiveSignalObjectID"
    "ZeroSignalInvalidIDPct"
    "PositiveSignalObjectIDPct"
    "MeanAssociatedReturnsPerFrame"
    "MedianAssociatedReturnsPerFrame"
    "P95AssociatedReturnsPerFrame"
];

Value = [
    N
    rangeTotal
    invalidTotal
    associatedTotal
    invalidPct
    associatedPct
    mean(A.PositiveSignalObjectID)
    median(A.PositiveSignalObjectID)
    prctile(A.PositiveSignalObjectID,95)
];

Stats = table(Metric,Value);
writetable(Stats,statsFile);

for k = 1:numel(figs)
    savefig(figs{k},fullfile(plotDir,[names{k} '.fig']));
    exportgraphics(figs{k}, ...
        fullfile(plotDir,[names{k} '.png']), ...
        'Resolution',300);
end

fid = fopen(reportFile,'w');
assert(fid~=-1,'Could not create research findings report.');

fprintf(fid,'GEMSTAR TASK 28.3B.6\n');
fprintf(fid,'FULL LIDAR IDENTITY VALIDATION\n');
fprintf(fid,'====================================\n\n');
fprintf(fid,'Scenario: fog_postfix_validation\n');
fprintf(fid,'Frames: %d\n',N);
fprintf(fid,'Range candidates: %d\n',rangeTotal);
fprintf(fid,'Zero-signal invalid-ID returns: %d\n',invalidTotal);
fprintf(fid,'Positive-signal object-ID returns: %d\n', ...
    associatedTotal);
fprintf(fid,'Invalid-ID proportion: %.4f%%\n',invalidPct);
fprintf(fid,'Object-associated proportion: %.4f%%\n\n', ...
    associatedPct);

fprintf(fid,'VALIDATED FINDINGS\n');
fprintf(fid,'- All 705 frames passed identity consistency checks.\n');
fprintf(fid,'- Range candidates can include invalid object IDs.\n');
fprintf(fid,'- Zero-signal candidate returns all carry invalid IDs.\n');
fprintf(fid,'- Positive-signal candidates carry ordinary object IDs.\n\n');

fprintf(fid,'LIMITATIONS\n');
fprintf(fid,'- Object association is simulator metadata, not GT accuracy.\n');
fprintf(fid,'- Weather causality is not established.\n');
fprintf(fid,'- Zero-signal returns may retain positive time of flight.\n');
fprintf(fid,'- Energy savings and execution latency are not measured.\n\n');

fprintf(fid,'SCHEDULER IMPLICATION\n');
fprintf(fid,'Track raw rays, range candidates, object-associated\n');
fprintf(fid,'returns, payload age, and independent quality checks\n');
fprintf(fid,'as separate workload/reliability variables.\n');

fclose(fid);

fprintf('\n=========================================\n');
fprintf('TASK 28.3B.6 COMPLETE\n');
fprintf('=========================================\n');
fprintf('Figures: 4 PNG + 4 FIG\n');
fprintf('Statistics: %s\n',statsFile);
fprintf('Findings: %s\n',reportFile);

disp(Stats);
