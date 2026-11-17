%% GEMSTAR Task 29.3D.3B
% Manual ground-truth annotation: resumable batches
% No YOLO predictions are used as reference labels.
% Existing annotations are preserved.

clearvars;
clc;
close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';

task28 = fullfile(root,'tests','Task_28_Final_Research');
task29 = fullfile(root,'tests','Task_29_Final_Research');

manifestPath = fullfile(task28,'02_CSV_Data', ...
    'task28_3D4B2_camera_image_manifest.csv');

outDir = fullfile(task29,'03_Configurations', ...
    'Camera_GroundTruth_Annotations');

if ~exist(outDir,'dir')
    mkdir(outDir);
end

T = readtable(manifestPath,'TextType','string');

assert(height(T)==20,'Expected 20 Camera images');

%% Verify previously saved Frame 0 annotation

firstPath = fullfile(outDir, ...
    'task29_labels_baseline_clear_frame00000.json');

assert(isfile(firstPath), ...
    'First annotation missing. Complete Task 29.3D.3A');

first = jsondecode(fileread(firstPath));

assert(first.reviewed==true, ...
    'First annotation is not reviewed');

assert(isempty(first.objects), ...
    'Expected zero objects in reviewed Frame 0');

fprintf('\n=== PREVIOUS ANNOTATION VERIFIED ===\n');
fprintf('Baseline clear Frame 0: 0 objects\n');

%% Annotate up to four new images per run

batchSize = 4;
processed = 0;
saved = 0;
skipped = 0;

allowed = ["car","truck","bus","person", ...
    "bicycle","motorcycle"];

fprintf('\n=== TASK 29.3D.3B: CAMERA ANNOTATION ===\n');
fprintf('Maximum new images this run: %d\n',batchSize);

for i = 1:height(T)

    scenario = string(T.Scenario(i));
    frame = str2double(string(T.Frame(i)));

    assert(isfinite(frame), ...
        'Invalid frame number');

    fileName = sprintf( ...
        'task29_labels_%s_frame%05d.json', ...
        char(scenario),frame);

    outPath = fullfile(outDir,fileName);

    if isfile(outPath)
        fprintf('ALREADY ANNOTATED: %s\n',fileName);
        continue;
    end

    if processed >= batchSize
        break;
    end

    processed = processed + 1;

    imagePath = char(T.OutputPNG(i));

    assert(isfile(imagePath), ...
        'Missing original image: %s',imagePath);

    img = imread(imagePath);

    assert(size(img,1)==480 && size(img,2)==640, ...
        'Unexpected Camera resolution');

    fig = figure('Color','w', ...
        'Name','GEMSTAR Ground Truth Annotation', ...
        'Position',[100 100 1050 750]);

    ax = axes(fig);
    image(ax,img);
    axis(ax,'image');
    axis(ax,'on');

    title(ax,sprintf('%s | Frame %d', ...
        char(scenario),frame), ...
        'Interpreter','none');

    fprintf('\n====================================\n');
    fprintf('IMAGE %d OF THIS BATCH\n',processed);
    fprintf('Scenario: %s\n',scenario);
    fprintf('Frame: %d\n',frame);
    fprintf('====================================\n');

    fprintf('\nAllowed classes:\n');
    fprintf('car, truck, bus, person, bicycle, motorcycle\n');

    fprintf('\nReview all visible target objects.\n');
    fprintf('Count = 0 only after confirming an empty image.\n');
    fprintf('Type skip for ambiguous images.\n');
    fprintf('Type stop to finish this session.\n');

    answer = lower(strtrim(string(input( ...
        'Number of objects (or skip/stop): ','s'))));

    if answer == "stop"
        close(fig);
        break;
    end

    if answer == "skip"
        skipped = skipped + 1;
        close(fig);
        fprintf('Image skipped; no annotation saved.\n');
        continue;
    end

    count = str2double(answer);

    if ~isfinite(count) || count<0 || count~=floor(count)
        skipped = skipped + 1;
        close(fig);
        fprintf('Invalid count; image skipped.\n');
        continue;
    end

    objects = struct('class',{}, ...
        'x1',{},'y1',{},'x2',{},'y2',{});

    valid = true;

    for k = 1:count

        fprintf('\nOBJECT %d OF %d\n',k,count);

        cls = lower(strtrim(string(input( ...
            'Object class: ','s'))));

        if ~any(cls==allowed)
            fprintf('Invalid class; image not saved.\n');
            valid = false;
            break;
        end

        fprintf('Click top-left and bottom-right corners.\n');
        fprintf('Use the ORIGINAL Camera image.\n');

        figure(fig);
        [x,y] = ginput(2);

        x1 = max(0,min(x));
        x2 = min(size(img,2),max(x));
        y1 = max(0,min(y));
        y2 = min(size(img,1),max(y));

        if x2<=x1 || y2<=y1
            fprintf('Invalid bounding box.\n');
            valid = false;
            break;
        end

        rectangle(ax, ...
            'Position',[x1 y1 x2-x1 y2-y1], ...
            'EdgeColor','g','LineWidth',2);

        text(ax,x1,max(1,y1-8),char(cls), ...
            'Color',[0 0.6 0], ...
            'FontWeight','bold');

        objects(k).class = char(cls);
        objects(k).x1 = x1;
        objects(k).y1 = y1;
        objects(k).x2 = x2;
        objects(k).y2 = y2;

        drawnow;
    end

    if ~valid
        skipped = skipped + 1;
        close(fig);
        continue;
    end

    confirmation = lower(strtrim(string(input( ...
        'Annotation complete and correct? (yes/no): ','s'))));

    if confirmation ~= "yes"
        skipped = skipped + 1;
        close(fig);
        fprintf('Not saved; review again later.\n');
        continue;
    end

    record = struct();

    record.task = '29.3D.3B';
    record.scenario = char(scenario);
    record.frame = frame;
    record.image = imagePath;
    record.image_sha256 = char(T.ImageSHA256(i));
    record.reviewed = true;
    record.annotation_source = 'manual_visual_review';
    record.independently_verified = false;
    record.objects = objects;

    jsonText = jsonencode(record,'PrettyPrint',true);

    % Never overwrite an existing annotation.
    if isfile(outPath)
        close(fig);
        error('Annotation appeared during session: %s',outPath);
    end

    fid = fopen(outPath,'w');

    if fid == -1
        close(fig);
        error('Cannot save annotation: %s',outPath);
    end

    fprintf(fid,'%s\n',jsonText);
    fclose(fid);

    saved = saved + 1;

    fprintf('\nSAVED: %s\n',fileName);
    fprintf('Reference objects: %d\n',count);

    close(fig);
end

%% Count completed annotation files

completed = 0;

for i = 1:height(T)

    scenario = char(string(T.Scenario(i)));
    frame = str2double(string(T.Frame(i)));

    fileName = sprintf( ...
        'task29_labels_%s_frame%05d.json', ...
        scenario,frame);

    if isfile(fullfile(outDir,fileName))
        completed = completed + 1;
    end
end

fprintf('\n=== TASK 29.3D.3B: SESSION SUMMARY ===\n');
fprintf('New annotations saved: %d\n',saved);
fprintf('Images skipped this run: %d\n',skipped);
fprintf('Total annotation files: %d/20\n',completed);
fprintf('Remaining images: %d\n',20-completed);
fprintf('Independent second review: PENDING\n');

fprintf('\nTASK 29.3D.3B: SESSION COMPLETE\n');
