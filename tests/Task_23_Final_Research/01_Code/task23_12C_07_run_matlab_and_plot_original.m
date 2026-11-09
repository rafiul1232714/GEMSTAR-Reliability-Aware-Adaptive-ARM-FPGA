% Task 23.12.C.7 - Run MATLAB validation and save graph

task = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research';

validationScript = fullfile(task, '01_Code', ...
    'task23_12C_07_matlab_camera_validation.m');

graphPath = fullfile(task, '03_Graphs', ...
    'task23_12C_07_matlab_camera_weather_comparison.png');

if isfile(graphPath)
    error('PNG already exists. Refusing to overwrite.');
end

% Execute independent MATLAB validation first.
run(validationScript);

% The validation script raises an error if comparison fails.

scenarioNames = {'Clear', 'Fog100', 'Fog20'};

fig = figure('Visible', 'off', ...
    'Color', 'white', ...
    'Position', [100 100 1100 470]);

tiledlayout(1, 2, 'Padding', 'compact');

nexttile;
bar([refLuminance matlabLuminance]);
set(gca, 'XTick', 1:3, 'XTickLabel', scenarioNames);
ylabel('Mean grayscale intensity (0-255)');
title('Camera Luminance');
legend('Python', 'MATLAB', 'Location', 'best');
grid on;

nexttile;
bar([refContrast matlabContrast]);
set(gca, 'XTick', 1:3, 'XTickLabel', scenarioNames);
ylabel('Grayscale standard deviation');
title('Camera Contrast');
legend('Python', 'MATLAB', 'Location', 'best');
grid on;

sgtitle('Task 23.12 - MATLAB Camera Weather Validation');

exportgraphics(fig, graphPath, 'Resolution', 200);
close(fig);

if ~isfile(graphPath)
    error('MATLAB PNG graph was not created.');
end

fprintf('PNG_SAVED=%s\n', graphPath);
fprintf('TASK23_12C_07_MATLAB_PNG_SAVED_PASS\n');
