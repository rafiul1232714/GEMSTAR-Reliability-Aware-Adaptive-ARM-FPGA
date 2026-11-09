%% TASK 21.5 - RADAR RANGE COMPARISON
clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';
task = fullfile(root,'tests','Task_21_Final_Research');

inputDir = fullfile(task,'02_Imported_Data');
graphDir = fullfile(task,'03_Graphs');
csvDir = fullfile(task,'04_CSV_Results');
findingsDir = fullfile(task,'06_Research_Findings');

fprintf('\n=== TASK 21.5 RANGE COMPARISON ===\n');

A = load(fullfile(inputDir, ...
    'task20_28_radar_world_points.mat'),'T');

B = load(fullfile(inputDir, ...
    'task20_49_50m_radar_returns.mat'),'T');

old = A.T;
new = B.T;

r10 = double(old.RangeM);
r50all = double(new.RangeM);
frames50 = double(new.Frame);

% Keep positive, finite baseline ranges.
r10 = r10(isfinite(r10) & r10 > 0);

% Exclude startup frame zero from corrected data.
keep50 = frames50 > 0 & ...
         isfinite(r50all) & r50all > 0;

r50 = r50all(keep50);

% Common distance window.
oldCommon = r10(r10 <= 10);
newCommon = r50(r50 <= 10);

fprintf('Original candidate returns: %d\n',numel(r10));
fprintf('Corrected candidate returns: %d\n',numel(r50));
fprintf('Original returns within 10m: %d\n',numel(oldCommon));
fprintf('Corrected returns within 10m: %d\n',numel(newCommon));
fprintf('Corrected returns beyond 10m: %d\n',nnz(r50 > 10));

%% GRAPH A - COMMON 0-10m DISTRIBUTION

edges = 0:0.5:10;

nOld = histcounts(oldCommon,edges);
nNew = histcounts(newCommon,edges);

% Normalize within each data subset.
pOld = nOld ./ max(1,sum(nOld));
pNew = nNew ./ max(1,sum(nNew));

centers = (edges(1:end-1) + edges(2:end))/2;

f1 = figure('Visible','off','Color','w', ...
    'Position',[100 100 1000 600]);

plot(centers,pOld,'-o','LineWidth',1.6);
hold on;
plot(centers,pNew,'-s','LineWidth',1.6);

xlabel('Radar range (m)');
ylabel('Fraction within 0-10 m subset');
title('Common-range comparison: original vs corrected');
legend('Original archived recordings', ...
       'Corrected 50m, frames 1-99', ...
       'Location','best');
grid on;
xlim([0 10]);

plotA = fullfile(graphDir, ...
    'task21_05_common_range_comparison.png');

print(f1,plotA,'-dpng','-r180');
close(f1);

%% GRAPH B - CORRECTED RADAR DISTANCE BANDS

bandEdges = 0:10:50;
bandCounts = histcounts(r50,bandEdges);
bandFractions = bandCounts ./ max(1,numel(r50));

bandLabels = {'0-10','10-20','20-30','30-40','40-50'};

f2 = figure('Visible','off','Color','w', ...
    'Position',[100 100 1000 600]);

bar(1:5,bandFractions);

set(gca,'XTick',1:5,'XTickLabel',bandLabels);

xlabel('Distance interval (m)');
ylabel('Fraction of corrected candidate returns');
title('Corrected radar: return distribution by range band');
grid on;

plotB = fullfile(graphDir, ...
    'task21_05_corrected_range_bands.png');

print(f2,plotB,'-dpng','-r180');
close(f2);

%% SAVE TABULATED BAND DATA

bandTable = table( ...
    string(bandLabels(:)), ...
    bandCounts(:), ...
    bandFractions(:), ...
    'VariableNames', ...
    {'RangeBandM','ReturnCount','FractionOfReturns'});

bandCSV = fullfile(csvDir, ...
    'task21_05_50m_range_bands.csv');

writetable(bandTable,bandCSV);

%% SAVE COMPARISON SUMMARY

dataset = ["Original archived recordings"; ...
           "Corrected 50m frames 1-99"];

total = [numel(r10);numel(r50)];

within10 = [numel(oldCommon);numel(newCommon)];
beyond10 = [nnz(r10 > 10);nnz(r50 > 10)];

medianWithin10 = [median(oldCommon);median(newCommon)];
maxRange = [max(r10);max(r50)];

summary = table(dataset,total,within10,beyond10, ...
    medianWithin10,maxRange, ...
    'VariableNames', ...
    {'Dataset','TotalReturns','Within10m','Beyond10m', ...
     'MedianWithin10m','MaximumRangeM'});

summaryCSV = fullfile(csvDir, ...
    'task21_05_comparison_summary.csv');

writetable(summary,summaryCSV);

%% SAVE RESEARCH FINDINGS

findingsPath = fullfile(findingsDir, ...
    'task21_05_comparison_findings.txt');

fid = fopen(findingsPath,'w');

if fid < 0
    error('Failed to create research findings.');
end

fprintf(fid,'TASK 21.5 - RANGE COMPARISON\n\n');

fprintf(fid,'Original returns: %d\n',numel(r10));
fprintf(fid,'Corrected returns: %d\n',numel(r50));

fprintf(fid,'Corrected returns beyond 10m: %d\n', ...
    nnz(r50 > 10));

fprintf(fid,'Corrected maximum range: %.6f m\n',max(r50));

fprintf(fid,'\nIMPORTANT LIMITATIONS\n');

fprintf(fid,'Original data combines multiple scenarios.\n');
fprintf(fid,'Corrected data comes from one recording.\n');
fprintf(fid,'Frame zero excluded from corrected analysis.\n');
fprintf(fid,'Measurements are not from paired experiments.\n');
fprintf(fid,'Differences in counts are not causal estimates.\n');
fprintf(fid,'Return counts are not detection accuracy.\n');
fprintf(fid,'No electrical energy was measured.\n');

fclose(fid);

%% FINAL VERIFICATION

fprintf('\n=== TASK 21.5 RANGE BAND STATISTICS ===\n');
disp(bandTable);

fprintf('\n=== TASK 21.5 COMPARISON SUMMARY ===\n');
disp(summary);

fprintf('Common-range graph saved: %d\n',isfile(plotA));
fprintf('Range-band graph saved: %d\n',isfile(plotB));
fprintf('Band CSV saved: %d\n',isfile(bandCSV));
fprintf('Comparison CSV saved: %d\n',isfile(summaryCSV));
fprintf('Research findings saved: %d\n',isfile(findingsPath));

fprintf('\n=== TASK 21.5 COMPLETE ===\n');
