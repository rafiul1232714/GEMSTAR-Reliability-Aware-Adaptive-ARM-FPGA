
%% TASK 8.10 - CLEAR WEATHER CAMERA QUALITY
% GEMSTAR Multi-Sensor Reliability Monitoring

clc;
clear;
close all;

project = "E:\GEMSTAR_Project\sensor-health-monitor";

imageFolder = project + "\results\figures\clear_camera";

tableFolder = project + "\results\tables";
figureFolder = project + "\results\figures";

if ~isfolder(tableFolder)
    mkdir(tableFolder);
end

if ~isfolder(figureFolder)
    mkdir(figureFolder);
end

%% Read clear-weather image metadata
metadata = readtable( ...
    imageFolder + "\clear_camera_frames.csv");

n = height(metadata);

brightness = zeros(n, 1);
contrast = zeros(n, 1);
edgeStrength = zeros(n, 1);

%% Analyze images
for k = 1:n

    filename = string(metadata.filename(k));

    img = imread(fullfile(imageFolder, filename));
    img = im2double(img);

    % Convert RGB to grayscale
    gray = 0.2989 * img(:,:,1) + ...
           0.5870 * img(:,:,2) + ...
           0.1140 * img(:,:,3);

    % Image brightness
    brightness(k) = mean(gray(:));

    % Image contrast
    contrast(k) = std(gray(:));

    % Edge strength (average gradient magnitude)
    [gx, gy] = gradient(gray);
    edgeMagnitude = hypot(gx, gy);

    edgeStrength(k) = mean(edgeMagnitude(:));

end

%% Save results
results = table( ...
    metadata.frame, ...
    metadata.timestamp_s, ...
    brightness, ...
    contrast, ...
    edgeStrength, ...
    'VariableNames', { ...
        'Frame', ...
        'Timestamp_s', ...
        'Brightness', ...
        'Contrast', ...
        'EdgeStrength' ...
    });

disp('========== CLEAR CAMERA QUALITY ==========');
disp(results);

csvFile = tableFolder + "\task08_clear_camera_quality.csv";

writetable(results, csvFile);

%% Create figure
fig = figure('Color', 'w');

plot(results.Timestamp_s, brightness, ...
    '-o', 'LineWidth', 1.5);

hold on;

plot(results.Timestamp_s, contrast, ...
    '-s', 'LineWidth', 1.5);

plot(results.Timestamp_s, edgeStrength, ...
    '-^', 'LineWidth', 1.5);

xlabel('Simulation Time (s)');
ylabel('Image Metric Value');

title('GEMSTAR Clear Weather - Camera Image Quality');

legend('Brightness', 'Contrast', 'Edge Strength', ...
    'Location', 'best');

grid on;

%% Save research figures
exportgraphics(fig, ...
    figureFolder + "\task08_clear_camera_quality.png", ...
    'Resolution', 300);

savefig(fig, ...
    figureFolder + "\task08_clear_camera_quality.fig");

disp(' ');
disp('TASK 8.10 COMPLETED SUCCESSFULLY');
disp('Saved CSV: ' + csvFile);
disp('Saved clear-weather Camera figures.');
