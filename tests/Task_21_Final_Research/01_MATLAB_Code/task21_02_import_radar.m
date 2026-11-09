%% TASK 21.2 - GEMSTAR RADAR DATA IMPORT
clear;
clc;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';

task20 = fullfile(root,'tests','Task_20_Final_Research');
task21 = fullfile(root,'tests','Task_21_Final_Research');

dataFolder = fullfile(task20,'02_CSV_Data');
outputFolder = fullfile(task21,'02_Imported_Data');
reportFolder = fullfile(task21,'06_Research_Findings');

if ~isfolder(outputFolder)
    mkdir(outputFolder);
end

if ~isfolder(reportFolder)
    mkdir(reportFolder);
end

datasets = {
    'task20_28_radar_world_points.csv'
    'task20_49_50m_radar_returns.csv'
    'task20_55_ray_alignment.csv'
    'task20_57_ray_box_intersections.csv'
};

fprintf('\n=== TASK 21.2 MATLAB RADAR IMPORT ===\n');

summary = table();

for k = 1:numel(datasets)

    filename = datasets{k};
    sourcePath = fullfile(dataFolder,filename);

    fprintf('\nDataset: %s\n',filename);

    if ~isfile(sourcePath)
        fprintf('STATUS: MISSING\n');

        summary = [summary; table( ...
            string(filename), false, NaN, NaN, ...
            'VariableNames', ...
            {'Dataset','Imported','Rows','Columns'})];

        continue;
    end

    try
        opts = detectImportOptions(sourcePath);
        T = readtable(sourcePath,opts);

        [~,name] = fileparts(filename);

        matPath = fullfile(outputFolder,[name '.mat']);

        % Preserve data as a MATLAB table.
        % Also retain its original source path.
        sourceCSV = sourcePath;

        save(matPath,'T','sourceCSV','-v7.3');

        fprintf('Rows: %d\n',height(T));
        fprintf('Columns: %d\n',width(T));
        fprintf('Saved MAT: %s\n',matPath);

        fprintf('Column names:\n');
        disp(T.Properties.VariableNames');

        fprintf('First three rows:\n');
        disp(head(T,3));

        summary = [summary; table( ...
            string(filename), true, ...
            height(T), width(T), ...
            'VariableNames', ...
            {'Dataset','Imported','Rows','Columns'})];

    catch ME
        fprintf('IMPORT FAILED: %s\n',ME.message);

        summary = [summary; table( ...
            string(filename), false, NaN, NaN, ...
            'VariableNames', ...
            {'Dataset','Imported','Rows','Columns'})];
    end
end

summaryPath = fullfile( ...
    reportFolder,'task21_02_import_summary.csv');

writetable(summary,summaryPath);

fprintf('\n=== IMPORT SUMMARY ===\n');
disp(summary);

fprintf('Summary saved: %d\n',isfile(summaryPath));
fprintf('Imported datasets: %d/%d\n', ...
    nnz(summary.Imported),numel(datasets));

fprintf('\n=== TASK 21.2 COMPLETE ===\n');
