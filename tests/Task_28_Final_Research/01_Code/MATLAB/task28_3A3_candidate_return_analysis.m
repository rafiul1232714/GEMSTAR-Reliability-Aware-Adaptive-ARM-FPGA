% ============================================================
% GEMSTAR TASK 28.3A.3
% LiDAR/Radar Candidate Return and Signal Analysis
% ============================================================

clear;
clc;
close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';
task = fullfile(root,'tests','Task_28_Final_Research');

dataDir = fullfile(task,'02_CSV_Data');
plotDir = fullfile(task,'04_Plots', ...
    'Candidate_Return_Analysis');

if ~exist(plotDir,'dir')
    mkdir(plotDir);
end

inputFile = fullfile(dataDir, ...
    'task28_3A2_full_candidate_returns.csv');

assert(isfile(inputFile),'Input CSV missing.');

T = readtable(inputFile,'TextType','string');

scenarios = [
    "baseline_clear"
    "baseline_fog_working_radar"
    "fog_mor100"
    "fog_postfix_validation"
];

labels = {
    'Clear'
    'Fog + Radar'
    'Fog MOR 100'
    'Fog postfix'
};

n = numel(scenarios);
expectedFrames = [829;794;466;705];

L = cell(n,1);
R = cell(n,1);

lidarMean = zeros(n,1);
lidarMedian = zeros(n,1);
lidarP95 = zeros(n,1);
lidarPositiveMean = zeros(n,1);
lidarNonPositiveMean = zeros(n,1);

radarMean = zeros(n,1);
radarMedian = zeros(n,1);
radarP95 = zeros(n,1);

lidarPositiveFraction = zeros(n,1);
lidarCandidateFraction = zeros(n,1);
radarCandidateFraction = zeros(n,1);

fprintf('\n=======================================\n');
fprintf('TASK 28.3A.3 — FULL SENSOR ANALYSIS\n');
fprintf('=======================================\n');

assert(height(T)==2*sum(expectedFrames), ...
    'Unexpected total sensor measurement rows.');

for i = 1:n

    scenario = scenarios(i);

    L{i} = T(T.Scenario==scenario & T.Sensor=="LiDAR",:);
    R{i} = T(T.Scenario==scenario & T.Sensor=="Radar",:);

    assert(height(L{i})==expectedFrames(i), ...
        'Unexpected LiDAR frame count: %s',scenario);

    assert(height(R{i})==expectedFrames(i), ...
        'Unexpected Radar frame count: %s',scenario);

    assert(isequal(L{i}.Frame,(0:expectedFrames(i)-1)'), ...
        'LiDAR frames not sequential.');

    assert(isequal(R{i}.Frame,(0:expectedFrames(i)-1)'), ...
        'Radar frames not sequential.');

    assert(all(L{i}.RawReflections==5271), ...
        'Unexpected LiDAR reflection grid.');

    assert(all(R{i}.RawReflections==100), ...
        'Unexpected Radar reflection grid.');

    for dataCell = {L{i},R{i}}
        D = dataCell{1};

        assert(all(D.CandidateReturns>=0 & ...
            D.PositiveSignalCandidates>=0 & ...
            D.PositiveSignalCandidates<=D.CandidateReturns), ...
            'Invalid candidate or signal counts.');

        assert(all(D.ZeroTOF+D.NearZeroReturns+ ...
            D.CandidateReturns==D.RawReflections), ...
            'Return categories do not sum to raw reflections.');
    end

    lidar = L{i}.CandidateReturns;
    lidarPositive = L{i}.PositiveSignalCandidates;
    radar = R{i}.CandidateReturns;

    lidarMean(i) = mean(lidar);
    lidarMedian(i) = median(lidar);
    lidarP95(i) = prctile(lidar,95);

    lidarPositiveMean(i) = mean(lidarPositive);
    lidarNonPositiveMean(i) = ...
        mean(lidar-lidarPositive);

    radarMean(i) = mean(radar);
    radarMedian(i) = median(radar);
    radarP95(i) = prctile(radar,95);

    % Pooled ratio across all candidate returns
    lidarPositiveFraction(i) = 100 * ...
        sum(lidarPositive)/max(sum(lidar),1);

    lidarCandidateFraction(i) = 100 * ...
        sum(lidar)/sum(L{i}.RawReflections);

    radarCandidateFraction(i) = 100 * ...
        sum(radar)/sum(R{i}.RawReflections);

    fprintf('\n%s\n',scenario);
    fprintf('Frames: %d\n',height(L{i}));
    fprintf('LiDAR candidate mean: %.2f\n',lidarMean(i));
    fprintf('LiDAR positive-signal mean: %.2f\n', ...
        lidarPositiveMean(i));
    fprintf('LiDAR nonpositive-signal mean: %.2f\n', ...
        lidarNonPositiveMean(i));
    fprintf('LiDAR positive among candidates: %.2f%%\n', ...
        lidarPositiveFraction(i));
    fprintf('Radar candidate mean: %.2f\n',radarMean(i));
end

%% FIGURE 1 — Mean LiDAR candidate types

f1 = figure('Color','w', ...
    'Name','LiDAR Candidate Comparison');

bar([lidarMean,lidarPositiveMean],'grouped');
grid on;
xticks(1:n);
xticklabels(labels);
ylabel('Mean returns per frame');
title('LiDAR Range Candidates vs Positive-Signal Candidates');
legend({'Range candidates','Positive signal'}, ...
    'Location','best');

%% FIGURE 2 — Positive signal fraction

f2 = figure('Color','w', ...
    'Name','LiDAR Signal Fraction');

bar(lidarPositiveFraction);
grid on;
xticks(1:n);
xticklabels(labels);
ylabel('Positive-signal candidates / range candidates (%)');
ylim([0 105]);
title('LiDAR Candidate Signal Classification');

%% FIGURE 3 — LiDAR candidate distributions

f3 = figure('Color','w', ...
    'Name','LiDAR Candidate Distributions');

tiledlayout(2,2);

for i=1:n
    nexttile;
    histogram(L{i}.CandidateReturns,25);
    grid on;
    xlabel('LiDAR range candidates/frame');
    ylabel('Frames');
    title(labels{i});
end

sgtitle('LiDAR Candidate Return Distributions');

%% FIGURE 4 — Radar candidate distributions

f4 = figure('Color','w', ...
    'Name','Radar Candidate Distributions');

tiledlayout(2,2);

for i=1:n
    nexttile;
    histogram(R{i}.CandidateReturns,20);
    grid on;
    xlabel('Radar range candidates/frame');
    ylabel('Frames');
    title(labels{i});
end

sgtitle('Radar Candidate Return Distributions');

%% FIGURE 5 — Per-frame signal differences

f5 = figure('Color','w', ...
    'Name','LiDAR Candidate Signal Timelines');

tiledlayout(2,2);

for i=1:n
    nexttile;
    plot(L{i}.Frame,L{i}.CandidateReturns, ...
        'LineWidth',1.1);
    hold on;
    plot(L{i}.Frame,L{i}.PositiveSignalCandidates, ...
        'LineWidth',1.1);
    grid on;
    xlabel('Frame');
    ylabel('Returns');
    title(labels{i});
end

legend({'Range candidates','Positive-signal candidates'}, ...
    'Location','best');

sgtitle('Per-Frame LiDAR Candidate and Signal Comparison');

%% Export statistical summary

Summary = table(scenarios,expectedFrames, ...
    lidarMean,lidarMedian,lidarP95, ...
    lidarPositiveMean,lidarNonPositiveMean, ...
    lidarPositiveFraction,lidarCandidateFraction, ...
    radarMean,radarMedian,radarP95, ...
    radarCandidateFraction, ...
    'VariableNames',{ ...
    'Scenario','Frames', ...
    'LiDARCandidateMean','LiDARCandidateMedian', ...
    'LiDARCandidateP95','LiDARPositiveMean', ...
    'LiDARNonPositiveMean','LiDARPositiveFractionPct', ...
    'LiDARCandidateFractionPct', ...
    'RadarCandidateMean','RadarCandidateMedian', ...
    'RadarCandidateP95','RadarCandidateFractionPct'});

summaryFile = fullfile(dataDir, ...
    'task28_3A3_candidate_return_statistics.csv');

assert(~isfile(summaryFile), ...
    'Summary CSV already exists; not overwriting.');

figures = {f1,f2,f3,f4,f5};

names = {
    'task28_3A3_lidar_candidate_comparison'
    'task28_3A3_positive_signal_fraction'
    'task28_3A3_lidar_distributions'
    'task28_3A3_radar_distributions'
    'task28_3A3_lidar_signal_timelines'
};

for i=1:numel(figures)
    assert(~isfile(fullfile(plotDir,[names{i} '.png'])) && ...
           ~isfile(fullfile(plotDir,[names{i} '.fig'])), ...
        'Figure output already exists.');
end

writetable(Summary,summaryFile);

for i=1:numel(figures)
    savefig(figures{i}, ...
        fullfile(plotDir,[names{i} '.fig']));

    exportgraphics(figures{i}, ...
        fullfile(plotDir,[names{i} '.png']), ...
        'Resolution',300);
end

fprintf('\n=======================================\n');
fprintf('TASK 28.3A.3 COMPLETE\n');
fprintf('=======================================\n');
fprintf('Three-sensor frames analyzed: %d\n', ...
    sum(expectedFrames));
fprintf('Figures saved: 5 PNG + 5 FIG\n');
fprintf('Statistics CSV: %s\n',summaryFile);
fprintf('Plots: %s\n',plotDir);
fprintf('\nCaution: Signal classification is not GT accuracy.\n');
fprintf('Caution: Scenario differences are not causal proof.\n');

disp(Summary);
