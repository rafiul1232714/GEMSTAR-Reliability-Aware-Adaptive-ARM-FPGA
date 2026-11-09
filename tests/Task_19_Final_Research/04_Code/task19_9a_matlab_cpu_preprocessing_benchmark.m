
%% TASK 19.9A - CPU LiDAR Preprocessing Benchmark
% GEMSTAR Frame 150
% Measure ROI and voxel processing latency in MATLAB.
% No additional toolbox required.
%
% IMPORTANT:
% These are MATLAB runtimes on the current PC.
% They are NOT ARM CPU or FPGA measurements.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

inputFile = fullfile(cloudDir, ...
    "task19_2a_frame150_candidate_xyz.csv");

assert(isfile(inputFile),"Candidate cloud CSV missing.");

%% 2. Load data - I/O excluded from timed region

T = readtable(inputFile);

P = double([T.X,T.Y,T.Z]);

assert(size(P,2)==3,"Expected 3D points.");
assert(all(isfinite(P(:))),"Nonfinite points detected.");

fprintf("\n=== TASK 19.9A CPU BASELINE ===\n");
fprintf("Input points: %d\n",size(P,1));

%% 3. Processing settings

roiXMin = 0;
roiXMax = 20;
roiYMin = -6;
roiYMax = 6;

voxelSize = 0.25;

%% 4. Validate output correctness before timing

P_roi = roiFilter(P,roiXMin,roiXMax,roiYMin,roiYMax);

P_voxel = voxelCentroids(P_roi,voxelSize);

fprintf("ROI output points: %d\n",size(P_roi,1));
fprintf("Voxel output points: %d\n",size(P_voxel,1));

assert(size(P_roi,1)==1922, ...
    "ROI count differs from Task 19.4A.");

assert(size(P_voxel,1)==418, ...
    "Voxel count differs from Task 19.5A.");

%% 5. Timing experiment
% Repeated warm measurements.
% tic/toc measures elapsed wall-clock time.
% The first untimed calls above serve as warm-up.
% CSV reading and writing are excluded.

runs = 200;

roiTimes = zeros(runs,1);
voxelTimes = zeros(runs,1);
pipelineTimes = zeros(runs,1);

for k = 1:runs

    tic;
    resultROI = roiFilter( ...
        P,roiXMin,roiXMax,roiYMin,roiYMax);
    roiTimes(k) = toc*1000;

    tic;
    resultVoxel = voxelCentroids( ...
        P_roi,voxelSize);
    voxelTimes(k) = toc*1000;

    tic;
    intermediate = roiFilter( ...
        P,roiXMin,roiXMax,roiYMin,roiYMax);

    resultPipeline = voxelCentroids( ...
        intermediate,voxelSize);

    pipelineTimes(k) = toc*1000;

end

assert(size(resultROI,1)==1922);
assert(size(resultVoxel,1)==418);
assert(size(resultPipeline,1)==418);

%% 6. Create summary statistics

names = ["ROI filtering"; ...
         "Voxel downsampling"; ...
         "ROI + voxel pipeline"];

timing = [roiTimes,voxelTimes,pipelineTimes];

summary = table();

summary.Operation = names;
summary.Runs = repmat(runs,3,1);

summary.MeanMs = mean(timing,1)';
summary.MedianMs = median(timing,1)';
summary.MinMs = min(timing,[],1)';
summary.MaxMs = max(timing,[],1)';

summary.P95Ms = zeros(3,1);

for k = 1:3
    values = sort(timing(:,k));
    index = ceil(0.95*runs);
    summary.P95Ms(k) = values(index);
end

summary.InputPoints = [ ...
    size(P,1);size(P_roi,1);size(P,1)];

summary.OutputPoints = [ ...
    size(P_roi,1);size(P_voxel,1);size(P_voxel,1)];

fprintf("\n=== TIMING RESULTS (milliseconds) ===\n");
disp(summary);

%% 7. Save full timing samples

samples = table();

samples.Run = (1:runs)';
samples.ROI_Ms = roiTimes;
samples.Voxel_Ms = voxelTimes;
samples.Pipeline_Ms = pipelineTimes;

samplesFile = fullfile(dataDir, ...
    "task19_9a_cpu_timing_samples.csv");

summaryFile = fullfile(dataDir, ...
    "task19_9a_cpu_timing_summary.csv");

writetable(samples,samplesFile);
writetable(summary,summaryFile);

%% 8. Visualize timing results

fig = figure("Color","w", ...
    "Position",[100 100 1120 480]);

subplot(1,2,1);

bar(summary.MedianMs);

xticks(1:3);
xticklabels(names);
xtickangle(20);

ylabel("Median execution time (ms)");
title("CPU Preprocessing - Median Latency");
grid on;

subplot(1,2,2);

plot(samples.Run,samples.ROI_Ms,"LineWidth",1);
hold on;

plot(samples.Run,samples.Voxel_Ms,"LineWidth",1);
plot(samples.Run,samples.Pipeline_Ms,"LineWidth",1);

xlabel("Benchmark run");
ylabel("Execution time (ms)");

title("Execution Time Across 200 Runs");

legend(names,"Location","best");
grid on;

graphFile = fullfile(graphDir, ...
    "task19_9a_cpu_latency_benchmark.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 9. Completion

fprintf("\n=== TASK 19.9A COMPLETE ===\n");

fprintf("Timing samples saved: %d\n",isfile(samplesFile));
fprintf("Timing summary saved: %d\n",isfile(summaryFile));
fprintf("Benchmark graph saved: %d\n",isfile(graphFile));

fprintf("\nROI median: %.6f ms\n",summary.MedianMs(1));
fprintf("Voxel median: %.6f ms\n",summary.MedianMs(2));
fprintf("Pipeline median: %.6f ms\n",summary.MedianMs(3));

fprintf("\nPC MATLAB baseline only.");
fprintf("\nNo FPGA performance or power measured.\n");

%% Local functions

function output = roiFilter(P,xmin,xmax,ymin,ymax)

    mask = ...
        P(:,1)>=xmin & ...
        P(:,1)<=xmax & ...
        P(:,2)>=ymin & ...
        P(:,2)<=ymax;

    output = P(mask,:);

end

function output = voxelCentroids(P,voxelSize)

    if isempty(P)
        output = zeros(0,3);
        return;
    end

    voxelIndex = floor(P./voxelSize);

    [~,~,group] = unique(voxelIndex,"rows");

    count = accumarray(group,1);

    output = zeros(numel(count),3);

    for axisIndex = 1:3
        totals = accumarray(group,P(:,axisIndex));
        output(:,axisIndex) = totals./count;
    end

end
