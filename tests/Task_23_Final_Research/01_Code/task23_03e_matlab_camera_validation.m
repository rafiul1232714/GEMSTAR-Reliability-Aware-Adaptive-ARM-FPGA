%% TASK 23.3E - MATLAB Camera Cross-Validation
clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';
task = fullfile(root,'tests','Task_23_Final_Research');

csvDir = fullfile(task,'02_CSV_Data');
graphDir = fullfile(task,'03_Graphs');
imageDir = fullfile(task,'08_Processed_Data', ...
    'Camera_Validated_RGB');
findingsDir = fullfile(task,'06_Research_Findings');
processedDir = fullfile(task,'08_Processed_Data');

fprintf('\n=== TASK 23.3E MATLAB CAMERA VALIDATION ===\n');

%% 1. Import Python results

csvPath = fullfile(csvDir, ...
    'task23_03d_camera_frame_metrics.csv');

assert(isfile(csvPath),'Python frame CSV missing.');

T = readtable(csvPath);

pairID = str2double(string(T.PairID));
frameID = double(T.Frame);

assert(height(T) == 300, ...
    'Expected 300 camera-frame rows.');

assert(all(ismember(unique(pairID),[1 2 3])), ...
    'Unexpected recording identifiers.');

assert(all(isfinite(T.BrightnessMean)), ...
    'Nonfinite Python brightness values.');

fprintf('Imported Python frames: %d\n',height(T));

%% 2. Independent MATLAB calculation from RGB PNGs

pairs = [1 2 3];
frames = [1 25 99];

results = struct([]);
k = 0;
tolerance = 0.001;

for p = pairs
    for f = frames

        imagePath = fullfile(imageDir, ...
            sprintf('pair%d_frame%03d_rgb.png',p,f));

        assert(isfile(imagePath), ...
            'Required RGB image missing: %s',imagePath);

        rgb = imread(imagePath);

        assert(isa(rgb,'uint8'), ...
            'Expected uint8 image.');

        assert(isequal(size(rgb),[480 640 3]), ...
            'Unexpected image dimensions.');

        % MATLAB calculates metrics independently.
        % Match Python's RGB weights and definitions.
        rgbDouble = double(rgb);

        gray = ...
            0.2126 * rgbDouble(:,:,1) + ...
            0.7152 * rgbDouble(:,:,2) + ...
            0.0722 * rgbDouble(:,:,3);

        matlabBrightness = mean(gray(:));
        matlabContrast = std(gray(:),1);

        matlabDark = 100 * mean(gray(:) < 40);
        matlabBright = 100 * mean(gray(:) > 215);

        small = gray(1:4:end,1:4:end);

        dx = abs(diff(small,1,2));
        dy = abs(diff(small,1,1));

        matlabEdge = ...
            (mean(dx(:)) + mean(dy(:))) / 2;

        row = find(pairID == p & frameID == f);

        assert(numel(row)==1, ...
            'Missing or duplicated Python frame row.');

        pythonValues = [
            T.BrightnessMean(row), ...
            T.ContrastStd(row), ...
            T.DarkPixelPct(row), ...
            T.BrightPixelPct(row), ...
            T.EdgeStrength(row)
        ];

        matlabValues = [
            matlabBrightness, ...
            matlabContrast, ...
            matlabDark, ...
            matlabBright, ...
            matlabEdge
        ];

        errors = abs(matlabValues-pythonValues);

        k = k + 1;

        results(k).PairID = p;
        results(k).Frame = f;
        results(k).BrightnessError = errors(1);
        results(k).ContrastError = errors(2);
        results(k).DarkPercentageError = errors(3);
        results(k).BrightPercentageError = errors(4);
        results(k).EdgeStrengthError = errors(5);
        results(k).MaxAbsoluteError = max(errors);
        results(k).Pass = all(errors < tolerance);

        fprintf(['Pair %d | Frame %d | ', ...
            'Max absolute difference = %.8f | PASS=%d\n'], ...
            p,f,max(errors),results(k).Pass);
    end
end

V = struct2table(results);

validationPath = fullfile(csvDir, ...
    'task23_03e_matlab_cross_validation.csv');

writetable(V,validationPath);

allPass = all(V.Pass);

%% 3. MATLAB graph - brightness for 300 frames

fig1 = figure('Color','w','Position',[100 100 1000 540]);

hold on;
for p = pairs
    idx = pairID == p;
    plot(frameID(idx),T.BrightnessMean(idx), ...
        'LineWidth',1.5, ...
        'DisplayName',sprintf('Pair %d',p));
end
hold off;

xlabel('Recorded frame index');
ylabel('Mean weighted RGB intensity');
title('Task 23.3E - Camera Brightness');
grid on;
legend('Location','best');

graph1 = fullfile(graphDir, ...
    'task23_03e_matlab_brightness.png');
exportgraphics(fig1,graph1,'Resolution',180);
close(fig1);

%% 4. MATLAB graph - contrast

fig2 = figure('Color','w','Position',[100 100 1000 540]);

hold on;
for p = pairs
    idx = pairID == p;
    plot(frameID(idx),T.ContrastStd(idx), ...
        'LineWidth',1.5, ...
        'DisplayName',sprintf('Pair %d',p));
end
hold off;

xlabel('Recorded frame index');
ylabel('Standard deviation of intensity');
title('Task 23.3E - Camera Contrast');
grid on;
legend('Location','best');

graph2 = fullfile(graphDir, ...
    'task23_03e_matlab_contrast.png');
exportgraphics(fig2,graph2,'Resolution',180);
close(fig2);

%% 5. MATLAB graph - edge strength

fig3 = figure('Color','w','Position',[100 100 1000 540]);

hold on;
for p = pairs
    idx = pairID == p;
    plot(frameID(idx),T.EdgeStrength(idx), ...
        'LineWidth',1.5, ...
        'DisplayName',sprintf('Pair %d',p));
end
hold off;

xlabel('Recorded frame index');
ylabel('Mean absolute neighbor difference');
title('Task 23.3E - Camera Edge Strength');
grid on;
legend('Location','best');

graph3 = fullfile(graphDir, ...
    'task23_03e_matlab_edge_strength.png');
exportgraphics(fig3,graph3,'Resolution',180);
close(fig3);

%% 6. MATLAB graph - actual RGB frames

fig4 = figure('Color','w','Position',[100 100 1200 470]);
tiledlayout(1,3,'Padding','compact','TileSpacing','compact');

for p = pairs
    nexttile;
    imagePath = fullfile(imageDir, ...
        sprintf('pair%d_frame025_rgb.png',p));

    image(imread(imagePath));
    axis image off;

    title(sprintf('Pair %d - Frame 25',p));
end

sgtitle('Task 23.3E - Verified RGB Camera Frames');

graph4 = fullfile(graphDir, ...
    'task23_03e_matlab_camera_comparison.png');

exportgraphics(fig4,graph4,'Resolution',180);
close(fig4);

%% 7. Recording summary

fprintf('\n=== MATLAB RECORDING COMPARISON ===\n');

for p = pairs
    idx = pairID == p;

    fprintf( ...
        'Pair %d | Frames=%d | Brightness=%.2f | Contrast=%.2f | Edge=%.2f\n', ...
        p,sum(idx), ...
        mean(T.BrightnessMean(idx)), ...
        mean(T.ContrastStd(idx)), ...
        mean(T.EdgeStrength(idx)));
end

%% 8. Save MATLAB research data

matPath = fullfile(processedDir, ...
    'task23_03e_matlab_camera_validation.mat');

save(matPath,'T','V','pairs','frames', ...
    'allPass','tolerance');

findingsPath = fullfile(findingsDir, ...
    'task23_03e_matlab_findings.txt');

fid = fopen(findingsPath,'w');
assert(fid~=-1,'Unable to create research findings.');

fprintf(fid,'TASK 23.3E - MATLAB CAMERA VALIDATION\n\n');
fprintf(fid,'Python frame rows imported: %d\n',height(T));
fprintf(fid,'RGB images independently checked: %d\n',height(V));
fprintf(fid,'Maximum absolute metric difference: %.9f\n', ...
    max(V.MaxAbsoluteError));
fprintf(fid,'Validation tolerance: %.6f\n',tolerance);
fprintf(fid,'All independent checks passed: %d\n',allPass);
fprintf(fid,'MATLAB graphs produced: 4\n\n');

fprintf(fid,'SCIENTIFIC LIMITATIONS\n');
fprintf(fid,'- MATLAB independently recalculated nine PNG image samples.\n');
fprintf(fid,'- Frame statistics for all 300 frames were imported from Python.\n');
fprintf(fid,'- PNG byte fidelity to original OSI was not independently checked.\n');
fprintf(fid,'- No object detection accuracy or reliability is established.\n');
fprintf(fid,'- Original recording weather conditions remain unverified.\n');
fprintf(fid,'- No ARM-FPGA energy was measured.\n');

fclose(fid);

%% 9. Final verification

fprintf('\n=== TASK 23.3E FINAL VERIFICATION ===\n');
fprintf('Python frame rows: %d\n',height(T));
fprintf('Independently checked images: %d\n',height(V));
fprintf('Maximum metric difference: %.9f\n', ...
    max(V.MaxAbsoluteError));
fprintf('All cross-checks passed: %d\n',allPass);

fprintf('Validation CSV: %d\n',isfile(validationPath));
fprintf('MATLAB brightness graph: %d\n',isfile(graph1));
fprintf('MATLAB contrast graph: %d\n',isfile(graph2));
fprintf('MATLAB edge graph: %d\n',isfile(graph3));
fprintf('MATLAB RGB comparison: %d\n',isfile(graph4));
fprintf('MATLAB data file: %d\n',isfile(matPath));
fprintf('Research findings: %d\n',isfile(findingsPath));

assert(allPass, ...
    'MATLAB/Python metric validation failed.');

fprintf('\n=== TASK 23.3E COMPLETE ===\n');
