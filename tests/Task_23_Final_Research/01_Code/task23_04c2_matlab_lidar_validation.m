%% TASK 23.4C-2
% Independent MATLAB LiDAR Range Validation

clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';
task = fullfile(root,'tests','Task_23_Final_Research');

dataDir = fullfile(task,'08_Processed_Data');
csvDir = fullfile(task,'02_CSV_Data');
graphDir = fullfile(task,'03_Graphs');
findingsDir = fullfile(task,'06_Research_Findings');

fprintf('\n=== TASK 23.4C-2 MATLAB LIDAR VALIDATION ===\n');

%% 1. Load original exported measurements

rawPath = fullfile(dataDir, ...
    'task23_04c_raw_lidar_measurements.csv');

assert(isfile(rawPath),'Raw LiDAR CSV missing.');

T = readtable(rawPath);

assert(height(T)==63252, ...
    'Expected 63252 measurement rows.');

pair = toNumeric(T.PairID);
frame = toNumeric(T.Frame);
ray = toNumeric(T.RayIndex);

tof = toNumeric(T.TimeOfFlightS);
strength = toNumeric(T.SignalStrength);

pythonRange = toNumeric(T.PythonRangeM);
pythonPositive = toNumeric(T.PythonPositive);
pythonScreened = toNumeric(T.PythonScreened);

fprintf('Raw LiDAR measurements imported: %d\n',height(T));

%% 2. Independently reconstruct distances

c = 299792458.0;

matlabRange = c .* tof ./ 2;

finiteMask = isfinite(tof) & isfinite(strength);

positiveMask = finiteMask & ...
    tof > 0 & strength > 0;

screenedMask = positiveMask & ...
    matlabRange >= 0.05 & matlabRange <= 200 & ...
    isfinite(matlabRange);

pythonPositiveMask = pythonPositive == 1;
pythonScreenedMask = pythonScreened == 1;

positiveMismatch = nnz( ...
    positiveMask ~= pythonPositiveMask);

screenMismatch = nnz( ...
    screenedMask ~= pythonScreenedMask);

assert(positiveMismatch==0, ...
    'Positive-return classification differs.');

assert(screenMismatch==0, ...
    'Range-screening classification differs.');

% The Python reference column contains blank values
% where measurements were rejected.

assert(all(isnan(pythonRange(~screenedMask))), ...
    'Unexpected Python ranges in rejected rows.');

rangeError = abs( ...
    matlabRange(screenedMask) - ...
    pythonRange(screenedMask));

maxRangeError = max(rangeError);

tolerance = 1e-7;

rangePass = all(rangeError < tolerance);

assert(rangePass, ...
    'MATLAB/Python reconstructed ranges disagree.');

fprintf('\n=== NUMERICAL VALIDATION ===\n');
fprintf('Positive returns: %d\n',nnz(positiveMask));
fprintf('Screened returns: %d\n',nnz(screenedMask));
fprintf('Positive classification mismatches: %d\n', ...
    positiveMismatch);
fprintf('Screening classification mismatches: %d\n', ...
    screenMismatch);
fprintf('Maximum range difference (m): %.12g\n', ...
    maxRangeError);
fprintf('Range validation passed: %d\n',rangePass);

%% 3. Check individual scan dimensions and ray indices

pairs = [1 2 3];
frames = [0 1 25 99];

nx = 251;
ny = 21;
nRays = nx * ny;

scanResults = struct([]);
index = 0;

rangeImages = cell(3,4);

fprintf('\n=== FRAME-BY-FRAME ANALYSIS ===\n');

for pi = 1:numel(pairs)
    p = pairs(pi);

    for fi = 1:numel(frames)
        f = frames(fi);

        idx = find(pair==p & frame==f);

        assert(numel(idx)==nRays, ...
            'Unexpected ray count for pair %d frame %d',p,f);

        [orderedRay,order] = sort(ray(idx));
        orderedIdx = idx(order);

        assert(isequal(orderedRay,(0:nRays-1)'), ...
            'Ray indices are incomplete or duplicated.');

        ranges = matlabRange(orderedIdx);
        mask = screenedMask(orderedIdx);

        ranges(~mask) = NaN;

        % Python flattens a [21,251] array row-major.
        % MATLAB uses column-major storage.
        % Transpose after reshape to preserve ray order.

        imageMatrix = reshape(ranges,nx,ny)';

        rangeImages{pi,fi} = imageMatrix;

        nPositive = nnz(positiveMask(orderedIdx));
        nScreened = nnz(mask);

        nRejected = nPositive - nScreened;

        nBelow = nnz(positiveMask(orderedIdx) & ...
            matlabRange(orderedIdx) < 0.05);

        nAbove = nnz(positiveMask(orderedIdx) & ...
            matlabRange(orderedIdx) > 200);

        validRanges = matlabRange(orderedIdx(mask));

        index = index+1;

        scanResults(index).PairID = p;
        scanResults(index).Frame = f;
        scanResults(index).RaySlots = nRays;
        scanResults(index).PositiveReturns = nPositive;
        scanResults(index).ScreenedReturns = nScreened;
        scanResults(index).RejectedPositive = nRejected;
        scanResults(index).BelowMinimum = nBelow;
        scanResults(index).AboveMaximum = nAbove;
        scanResults(index).CoveragePct = ...
            100*nScreened/nRays;
        scanResults(index).MedianRangeM = ...
            median(validRanges);
        scanResults(index).MinRangeM = ...
            min(validRanges);
        scanResults(index).MaxRangeM = ...
            max(validRanges);

        fprintf(['Pair %d | Frame %2d | ', ...
            'Positive=%4d | Screened=%4d | ', ...
            'Rejected=%4d | Below=%.0f | Above=%.0f\n'], ...
            p,f,nPositive,nScreened,nRejected,nBelow,nAbove);
    end
end

S = struct2table(scanResults);

summaryPath = fullfile(csvDir, ...
    'task23_04c2_matlab_scan_validation.csv');

writetable(S,summaryPath);

%% 4. Figure 1: Rejected measurements by frame

fig1 = figure('Color','w', ...
    'Position',[100 100 1000 500]);

hold on;

for p = pairs
    selected = S.PairID==p;

    plot(S.Frame(selected), ...
        S.RejectedPositive(selected), ...
        '-o','LineWidth',1.6, ...
        'DisplayName',sprintf('Pair %d',p));
end

hold off;
grid on;

xlabel('Recorded frame index');
ylabel('Positive returns rejected by range screening');
title('Task 23.4C - LiDAR Rejected-Return Investigation');
legend('Location','best');

graph1 = fullfile(graphDir, ...
    'task23_04c2_matlab_rejected_returns.png');

exportgraphics(fig1,graph1,'Resolution',180);
close(fig1);

%% 5. Figure 2: LiDAR range images at frame 25

fig2 = figure('Color','w', ...
    'Position',[100 100 1200 850]);

tiledlayout(3,1, ...
    'Padding','compact', ...
    'TileSpacing','compact');

for pi = 1:numel(pairs)

    nexttile;

    rangeImage = rangeImages{pi,3};

    h = imagesc(rangeImage,[0 50]);
    set(h,'AlphaData',double(isfinite(rangeImage)));

    axis tight;
    set(gca,'YDir','reverse');

    colorbar;
    colormap(gca,'parula');

    title(sprintf( ...
        'Pair %d - Frame 25 - Range image',pairs(pi)));

    xlabel('Horizontal ray index');
    ylabel('Vertical ray index');
end

sgtitle('LiDAR 21 x 251 Range-Image Reconstruction');

graph2 = fullfile(graphDir, ...
    'task23_04c2_matlab_range_images.png');

exportgraphics(fig2,graph2,'Resolution',180);
close(fig2);

%% 6. Figure 3: Range distributions

fig3 = figure('Color','w', ...
    'Position',[100 100 1000 500]);

hold on;

for p = pairs
    idx = pair==p & screenedMask;

    histogram(matlabRange(idx), ...
        'BinEdges',linspace(0,75,76), ...
        'Normalization','pdf', ...
        'DisplayStyle','stairs', ...
        'LineWidth',1.5, ...
        'DisplayName',sprintf('Pair %d',p));
end

hold off;
grid on;

xlabel('LiDAR reconstructed range (m)');
ylabel('Probability density');
title('Task 23.4C - LiDAR Range Distributions');
legend('Location','best');

graph3 = fullfile(graphDir, ...
    'task23_04c2_matlab_range_distributions.png');

exportgraphics(fig3,graph3,'Resolution',180);
close(fig3);

%% 7. Summarize rejected measurements

fprintf('\n=== REJECTED-RETURN DIAGNOSTICS ===\n');

for p = pairs

    idx = pair==p;

    positive = nnz(positiveMask(idx));
    accepted = nnz(screenedMask(idx));

    rejected = positive-accepted;

    frameZero = S.PairID==p & S.Frame==0;

    fprintf( ...
        'Pair %d | Rejected=%d | Frame0Rejected=%d\n', ...
        p,rejected,S.RejectedPositive(frameZero));
end

%% 8. Save research data

matPath = fullfile(dataDir, ...
    'task23_04c2_matlab_lidar_validation.mat');

save(matPath,'S','rangeImages', ...
    'pairs','frames','c','tolerance', ...
    'maxRangeError','positiveMismatch', ...
    'screenMismatch');

findingsPath = fullfile(findingsDir, ...
    'task23_04c2_matlab_findings.txt');

fid = fopen(findingsPath,'w');

assert(fid~=-1,'Cannot write findings file.');

fprintf(fid,'TASK 23.4C-2 - MATLAB LIDAR VALIDATION\n\n');
fprintf(fid,'Raw measurement rows: %d\n',height(T));
fprintf(fid,'Independently reconstructed ranges: %d\n', ...
    height(T));
fprintf(fid,'Positive returns: %d\n',nnz(positiveMask));
fprintf(fid,'Screened returns: %d\n',nnz(screenedMask));
fprintf(fid,'Positive classification mismatches: %d\n', ...
    positiveMismatch);
fprintf(fid,'Screening classification mismatches: %d\n', ...
    screenMismatch);
fprintf(fid,'Maximum range error (m): %.12g\n', ...
    maxRangeError);
fprintf(fid,'Range validation passed: %d\n\n',rangePass);

for p = pairs
    r = S.PairID==p;

    fprintf(fid,'Pair %d - Sampled frame results:\n',p);

    for j = find(r)'
        fprintf(fid, ...
            'Frame %d: positive %d, screened %d, rejected %d\n', ...
            S.Frame(j),S.PositiveReturns(j), ...
            S.ScreenedReturns(j),S.RejectedPositive(j));
    end
end

fprintf(fid,'\nSCIENTIFIC LIMITATIONS\n');
fprintf(fid,'- LiDAR source values were exported by Python.\n');
fprintf(fid,'- MATLAB independently recalculated range and screening.\n');
fprintf(fid,'- Only four frames per complete recording were checked.\n');
fprintf(fid,'- The full 100-frame Python dataset was not independently reprocessed.\n');
fprintf(fid,'- Range-image ordering is based on assumed row-major ray indexing.\n');
fprintf(fid,'- 3D beam geometry has not been GroundTruth-validated.\n');
fprintf(fid,'- No FPGA energy or detection accuracy measured.\n');

fclose(fid);

%% 9. Final verification

fprintf('\n=== TASK 23.4C-2 FINAL VERIFICATION ===\n');

fprintf('Raw LiDAR rows: %d\n',height(T));
fprintf('Reconstructed range-image matrices: %d\n', ...
    numel(rangeImages));
fprintf('Range validation passed: %d\n',rangePass);
fprintf('Positive mismatches: %d\n',positiveMismatch);
fprintf('Screening mismatches: %d\n',screenMismatch);
fprintf('Maximum range difference: %.12g m\n',maxRangeError);

fprintf('Validation CSV: %d\n',isfile(summaryPath));
fprintf('Rejected-return graph: %d\n',isfile(graph1));
fprintf('Range-image graph: %d\n',isfile(graph2));
fprintf('Distribution graph: %d\n',isfile(graph3));
fprintf('MAT data: %d\n',isfile(matPath));
fprintf('Research findings: %d\n',isfile(findingsPath));

fprintf('\n=== TASK 23.4C-2 COMPLETE ===\n');

%% Local numeric import helper
function out = toNumeric(values)
    if isnumeric(values)
        out = double(values);
    else
        out = str2double(string(values));
    end
end
