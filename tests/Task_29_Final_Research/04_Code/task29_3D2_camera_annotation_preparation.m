%% Task 29.3D.2 - Camera ground-truth review preparation
clearvars; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';

task28 = fullfile(root,'tests','Task_28_Final_Research');
task29 = fullfile(root,'tests','Task_29_Final_Research');

manifestPath = fullfile(task28,'02_CSV_Data', ...
    'task28_3D4B2_camera_image_manifest.csv');

outputDir = fullfile(task29,'01_Graphs', ...
    'Camera_Annotation_Review');

dataDir = fullfile(task29,'02_CSV_Data');

if ~exist(outputDir,'dir')
    mkdir(outputDir);
end

T = readtable(manifestPath,'TextType','string');

assert(height(T)==20,'Expected exactly 20 images');

scenarios = [
    "baseline_clear"
    "baseline_fog_working_radar"
    "fog_mor100"
    "fog_postfix_validation"
];

reviewRows = table();

fprintf('\n=== TASK 29.3D.2: CAMERA REVIEW ===\n');

for s = 1:numel(scenarios)

    scenario = scenarios(s);

    rows = T(T.Scenario==scenario,:);

    assert(height(rows)==5, ...
        'Expected five images per scenario');

    frames = str2double(string(rows.Frame));
    [~,order] = sort(frames);
    rows = rows(order,:);

    fig = figure('Color','w', ...
        'Position',[80 80 1400 850]);

    layout = tiledlayout(2,3, ...
        'TileSpacing','compact', ...
        'Padding','compact');

    title(layout, ...
        "GEMSTAR Camera Review - " + scenario, ...
        'Interpreter','none');

    for j = 1:height(rows)

        imagePath = char(rows.OutputPNG(j));

        assert(isfile(imagePath), ...
            'Missing camera image: %s',imagePath);

        img = imread(imagePath);

        assert(size(img,1)==480 && size(img,2)==640, ...
            'Unexpected image resolution');

        nexttile;
        image(img);
        axis image off;

        frameNumber = str2double(string(rows.Frame(j)));

        title(sprintf('Frame %d',frameNumber), ...
            'FontSize',11);

        newRow = table( ...
            scenario, ...
            frameNumber, ...
            string(imagePath), ...
            "UNREVIEWED", ...
            NaN, ...
            "", ...
            'VariableNames',{ ...
                'Scenario', ...
                'Frame', ...
                'ImagePath', ...
                'ReviewStatus', ...
                'ReferenceObjectCount', ...
                'Notes' ...
            });

        reviewRows = [reviewRows;newRow];

    end

    nexttile;
    axis off;

    text(0.05,0.8, ...
        {'Review questions:', ...
         '1. Which objects are visible?', ...
         '2. Are any pedestrians visible?', ...
         '3. Are vehicles partly occluded?', ...
         '4. Are object classes ambiguous?', ...
         '5. Are weather effects visible?'}, ...
         'FontSize',12, ...
         'VerticalAlignment','top');

    name = "task29_3D2_review_" + scenario;

    savefig(fig,fullfile(outputDir,name + ".fig"));

    exportgraphics(fig, ...
        fullfile(outputDir,name + ".png"), ...
        'Resolution',250);

    fprintf('SAVED: %s\n',name);

    close(fig);
end

assert(height(reviewRows)==20, ...
    'Review inventory must contain 20 rows');

reviewPath = fullfile(dataDir, ...
    'task29_3D2_camera_review_checklist.csv');

if isfile(reviewPath)
    error('Existing review checklist preserved: %s', ...
        reviewPath);
end

writetable(reviewRows,reviewPath);

fprintf('\n=== TASK 29.3D.2 SUMMARY ===\n');
fprintf('Scenarios: %d\n',numel(scenarios));
fprintf('Images prepared: %d\n',height(reviewRows));
fprintf('Review checklist: %s\n',reviewPath);
fprintf('Ground-truth annotations created: 0\n');
fprintf('Manual review still required: YES\n');

fprintf('\nTASK 29.3D.2: PASS\n');
fprintf('Saved four PNG and four FIG files in:\n%s\n', ...
    outputDir);
