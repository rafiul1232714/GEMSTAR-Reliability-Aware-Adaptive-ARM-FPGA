%% TASK 21.7 - MATLAB RADAR CPU BENCHMARK
clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';
task = fullfile(root,'tests','Task_21_Final_Research');

inputDir = fullfile(task,'02_Imported_Data');
benchmarkDir = fullfile(task,'05_Benchmark_Results');
graphDir = fullfile(task,'03_Graphs');
findingDir = fullfile(task,'06_Research_Findings');

if ~isfolder(benchmarkDir), mkdir(benchmarkDir); end
if ~isfolder(graphDir), mkdir(graphDir); end
if ~isfolder(findingDir), mkdir(findingDir); end

source = fullfile(inputDir, ...
    'task20_49_50m_radar_returns.mat');

S = load(source,'T');
T = S.T;

frame = double(T.Frame);
rangeM = double(T.RangeM);
signal = double(T.SignalStrength);

NFRAMES = 99;
BATCH = 100;
TRIALS = 5;

fprintf('\n=== TASK 21.7 CPU BENCHMARK ===\n');
fprintf('Computer: %s\n',getenv('COMPUTERNAME'));
fprintf('Processor: %s\n',getenv('PROCESSOR_IDENTIFIER'));
fprintf('MATLAB: %s\n',version);
fprintf('Batch repetitions: %d\n',BATCH);
fprintf('Benchmark trials: %d\n',TRIALS);

%% VERIFY BOTH IMPLEMENTATIONS

referenceA = processVectorized( ...
    frame,rangeM,signal,NFRAMES,1);

referenceB = processByFrame( ...
    frame,rangeM,signal,NFRAMES,1);

assert(isequal(referenceA.Counts,referenceB.Counts), ...
    'Return-count results disagree');

assert(isequal(referenceA.Beyond10,referenceB.Beyond10), ...
    'Beyond-10m results disagree');

assert(max(abs(referenceA.SumRange - ...
    referenceB.SumRange)) < 1e-7, ...
    'Range sums disagree');

assert(sum(referenceA.Counts) == 5614, ...
    'Unexpected number of validated radar returns');

fprintf('Correctness validation: PASSED\n');
fprintf('Candidate returns: %d\n',sum(referenceA.Counts));

%% WARM-UP

processVectorized(frame,rangeM,signal,NFRAMES,3);
processByFrame(frame,rangeM,signal,NFRAMES,3);

%% BENCHMARK

vectorTimes = zeros(TRIALS,1);
loopTimes = zeros(TRIALS,1);

for k = 1:TRIALS

    vectorTimes(k) = timeit(@() ...
        processVectorized( ...
        frame,rangeM,signal,NFRAMES,BATCH));

    loopTimes(k) = timeit(@() ...
        processByFrame( ...
        frame,rangeM,signal,NFRAMES,BATCH));

    fprintf('Trial %d: Vectorized %.5f ms | Loop %.5f ms\n', ...
        k,1000*vectorTimes(k)/BATCH, ...
        1000*loopTimes(k)/BATCH);
end

% Seconds per complete 99-frame dataset pass.
vectorMs = 1000*vectorTimes/BATCH;
loopMs = 1000*loopTimes/BATCH;

summary = table( ...
    ["Vectorized MATLAB";"Frame-by-frame MATLAB"], ...
    [median(vectorMs);median(loopMs)], ...
    [min(vectorMs);min(loopMs)], ...
    [max(vectorMs);max(loopMs)], ...
    'VariableNames', ...
    {'Method','MedianMsPerDataset', ...
    'MinimumMsPerDataset','MaximumMsPerDataset'});

%% SAVE RESULTS

trialTable = table( ...
    (1:TRIALS)',vectorMs,loopMs, ...
    'VariableNames', ...
    {'Trial','VectorizedMs','LoopMs'});

trialPath = fullfile(benchmarkDir, ...
    'task21_07_cpu_benchmark_trials.csv');

summaryPath = fullfile(benchmarkDir, ...
    'task21_07_cpu_benchmark_summary.csv');

writetable(trialTable,trialPath);
writetable(summary,summaryPath);

%% GRAPH

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 900 550]);

bar([median(vectorMs),median(loopMs)]);
set(gca,'XTick',1:2, ...
    'XTickLabel',{'Vectorized','Frame-by-frame'});

ylabel('Median CPU processing time (ms)');
title('MATLAB radar processing benchmark');
grid on;

graphPath = fullfile(graphDir, ...
    'task21_07_cpu_benchmark.png');

print(f,graphPath,'-dpng','-r180');
close(f);

%% SAVE CONFIGURATION AND FINDINGS

configPath = fullfile(benchmarkDir, ...
    'task21_07_benchmark_environment.txt');

fid = fopen(configPath,'w');
if fid < 0, error('Cannot create environment file'); end

fprintf(fid,'Computer: %s\n',getenv('COMPUTERNAME'));
fprintf(fid,'Processor: %s\n',getenv('PROCESSOR_IDENTIFIER'));
fprintf(fid,'MATLAB version: %s\n',version);
fprintf(fid,'MATLAB release: %s\n',version('-release'));
fprintf(fid,'Batch repetitions: %d\n',BATCH);
fprintf(fid,'Trials: %d\n',TRIALS);
fprintf(fid,'Frames per pass: %d\n',NFRAMES);
fprintf(fid,'Dataset source: %s\n',source);
fprintf(fid,'Timing excludes MAT loading, disk I/O and plotting.\n');
fprintf(fid,'No CPU affinity or fixed frequency enforced.\n');
fclose(fid);

findingPath = fullfile(findingDir, ...
    'task21_07_cpu_benchmark_findings.txt');

fid = fopen(findingPath,'w');
if fid < 0, error('Cannot create findings file'); end

fprintf(fid,'TASK 21.7 - MATLAB CPU PERFORMANCE\n\n');
fprintf(fid,'Correctness comparison: PASSED\n');
fprintf(fid,'Candidate returns: 5614\n');
fprintf(fid,'Vectorized median ms/pass: %.8f\n',median(vectorMs));
fprintf(fid,'Frame loop median ms/pass: %.8f\n',median(loopMs));
fprintf(fid,'Workload: range filtering and per-frame aggregation.\n');
fprintf(fid,'Execution platform: Windows desktop CPU.\n');
fprintf(fid,'Timing excludes MAT loading and external transfer.\n');
fprintf(fid,'Small workload timings are sensitive to overhead.\n');
fprintf(fid,'Actual power and energy were NOT measured.\n');
fprintf(fid,'No ARM/FPGA speedup established.\n');
fclose(fid);

%% OUTPUT

fprintf('\n=== TASK 21.7 BENCHMARK RESULTS ===\n');
disp(summary);

fprintf('Trial CSV saved: %d\n',isfile(trialPath));
fprintf('Summary CSV saved: %d\n',isfile(summaryPath));
fprintf('Graph saved: %d\n',isfile(graphPath));
fprintf('Environment saved: %d\n',isfile(configPath));
fprintf('Findings saved: %d\n',isfile(findingPath));

fprintf('\n=== TASK 21.7 COMPLETE ===\n');

%% LOCAL FUNCTIONS

function result = processVectorized( ...
    frames,ranges,signals,nFrames,repeats)

    for rep = 1:repeats

        good = isfinite(frames) & ...
            isfinite(ranges) & ...
            isfinite(signals) & ...
            frames >= 1 & frames <= nFrames & ...
            frames == floor(frames) & ...
            ranges > 0 & ranges <= 50.01;

        f = frames(good);
        r = ranges(good);

        counts = accumarray(f,1,[nFrames,1],@sum,0);
        beyond = accumarray(f,double(r>10), ...
            [nFrames,1],@sum,0);
        sums = accumarray(f,r,[nFrames,1],@sum,0);
    end

    result.Counts = counts;
    result.Beyond10 = beyond;
    result.SumRange = sums;
end

function result = processByFrame( ...
    frames,ranges,signals,nFrames,repeats)

    for rep = 1:repeats

        counts = zeros(nFrames,1);
        beyond = zeros(nFrames,1);
        sums = zeros(nFrames,1);

        for j = 1:numel(frames)
            f = frames(j);
            r = ranges(j);

            if ~isfinite(f) || ~isfinite(r) || ...
               ~isfinite(signals(j)) || ...
               f < 1 || f > nFrames || ...
               f ~= floor(f) || ...
               r <= 0 || r > 50.01
                continue;
            end

            counts(f) = counts(f)+1;
            beyond(f) = beyond(f)+(r>10);
            sums(f) = sums(f)+r;
        end
    end

    result.Counts = counts;
    result.Beyond10 = beyond;
    result.SumRange = sums;
end
