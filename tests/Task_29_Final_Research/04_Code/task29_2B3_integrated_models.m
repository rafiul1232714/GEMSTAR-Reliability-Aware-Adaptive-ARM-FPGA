%% GEMSTAR Task 29.2B.3
% Integrated LiDAR-Radar CPU latency prediction.
% Models: constant, input-only ridge, stage-aware ridge.
% Training-only standardization and coefficients.
% Fixed ridge penalty, not selected on validation/test.

clearvars;
clc;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_29_Final_Research';
dataDir = fullfile(root,'02_CSV_Data');

inFile = fullfile(dataDir, ...
    'task29_2B1_integrated_frame_latency_summary.csv');

T = readtable(inFile,'TextType','string');

required = ["Frame","Split","LiDARInputPoints", ...
    "LiDARFilteredPoints","RadarInputReturns", ...
    "TotalMedianMs"];

assert(all(ismember(required,string(T.Properties.VariableNames))), ...
    'Required columns missing.');

assert(height(T)==53,'Expected 53 frames.');
assert(numel(unique(T.Frame))==53,'Duplicate frame IDs.');

numericNames = ["Frame","LiDARInputPoints", ...
    "LiDARFilteredPoints","RadarInputReturns","TotalMedianMs"];

for j=1:numel(numericNames)
    name = numericNames(j);
    if ~isnumeric(T.(name))
        T.(name) = str2double(string(T.(name)));
    end
    assert(all(isfinite(T.(name))), ...
        'Invalid numeric values in %s',char(name));
end

T.Split = string(T.Split);
assert(all(ismember(T.Split,["train","validation","test"])), ...
    'Unexpected split label.');

isTrain = T.Split=="train";
isVal = T.Split=="validation";
isTest = T.Split=="test";

assert(sum(isTrain)==37,'Expected 37 training frames.');
assert(sum(isVal)==8,'Expected 8 validation frames.');
assert(sum(isTest)==8,'Expected 8 testing frames.');
assert(all(T.TotalMedianMs>0),'Invalid target latency.');

y = T.TotalMedianMs;
trainBaseline = median(y(isTrain));

lambda = 1.0;
models = ["constant","input_only","stage_aware"];
splitNames = ["train","validation","test"];

pred = zeros(height(T),3);
pred(:,1) = trainBaseline;

coefficientRows = table();

for m = 2:3

    if m==2
        featureNames = ["LiDARInputPoints","RadarInputReturns"];
    else
        featureNames = ["LiDARInputPoints", ...
            "LiDARFilteredPoints","RadarInputReturns"];
    end

    X = zeros(height(T),numel(featureNames));

    for j=1:numel(featureNames)
        X(:,j) = T.(featureNames(j));
    end

    Xtrain = X(isTrain,:);
    ytrain = y(isTrain);

    % Standardize exclusively using training data.
    mu = mean(Xtrain,1);
    sigma = std(Xtrain,0,1);
    sigma(sigma<1e-12) = 1;

    Ztrain = (Xtrain-mu)./sigma;
    Zall = (X-mu)./sigma;

    A = [ones(size(Ztrain,1),1),Ztrain];

    % Unpenalized intercept, regularized feature terms.
    penalty = diag([0,ones(1,size(Ztrain,2))]);
    beta = (A'*A+lambda*penalty)\(A'*ytrain);

    pred(:,m) = max(0, ...
        [ones(height(T),1),Zall]*beta);

    slopes = beta(2:end)./sigma';
    intercept = beta(1)-sum(slopes'.*mu);

    terms = ["Intercept",featureNames];
    values = [intercept;slopes];

    newRows = table( ...
        repmat(models(m),numel(terms),1), ...
        terms',values, ...
        repmat(lambda,numel(terms),1), ...
        'VariableNames', ...
        {'Model','Term','Coefficient','RidgeLambda'});

    coefficientRows = [coefficientRows;newRows];

end

% Constant model coefficient.
baselineRow = table( ...
    "constant","Intercept",trainBaseline,0, ...
    'VariableNames', ...
    {'Model','Term','Coefficient','RidgeLambda'});

coefficientRows = [baselineRow;coefficientRows];

% One prediction record per original frame and model.
predictionRows = table();
metricRows = table();

for m=1:numel(models)

    for k=1:numel(splitNames)

        mask = T.Split==splitNames(k);

        actual = y(mask);
        predicted = pred(mask,m);
        errors = actual-predicted;

        mae = mean(abs(errors));
        rmse = sqrt(mean(errors.^2));
        bias = mean(errors);
        maxAE = max(abs(errors));

        denom = sum((actual-mean(actual)).^2);

        % R2 can be misleading for near-constant test targets.
        r2 = NaN;
        if denom>1e-15
            r2 = 1-sum(errors.^2)/denom;
        end

        nRows = sum(mask);

        metric = table( ...
            models(m),splitNames(k),nRows, ...
            mae,rmse,bias,maxAE,r2, ...
            'VariableNames', ...
            {'Model','Split','Frames','MAE_Ms', ...
             'RMSE_Ms','Bias_Ms','MaxAE_Ms','R2'});

        metricRows = [metricRows;metric];

    end

    newPredictions = table( ...
        T.Frame, T.Split, ...
        repmat(models(m),height(T),1), ...
        T.LiDARInputPoints, ...
        T.LiDARFilteredPoints, ...
        T.RadarInputReturns, ...
        y,pred(:,m),y-pred(:,m), ...
        'VariableNames', ...
        {'Frame','Split','Model','LiDARInputPoints', ...
         'LiDARFilteredPoints','RadarInputReturns', ...
         'ActualMs','PredictedMs','ResidualMs'});

    predictionRows = [predictionRows;newPredictions];

end

coefPath = fullfile(dataDir, ...
    'task29_2B3_integrated_model_coefficients.csv');
metricsPath = fullfile(dataDir, ...
    'task29_2B3_integrated_model_metrics.csv');
predictionPath = fullfile(dataDir, ...
    'task29_2B3_integrated_model_predictions.csv');

writetable(coefficientRows,coefPath);
writetable(metricRows,metricsPath);
writetable(predictionRows,predictionPath);

fprintf('\n=== TASK 29.2B.3: MODEL COEFFICIENTS ===\n');
disp(coefficientRows);

fprintf('\n=== MODEL PERFORMANCE ===\n');
disp(metricRows);

fprintf('\n=== TEST DATA: MODEL COMPARISON ===\n');
disp(metricRows(metricRows.Split=="test",:));

assert(height(predictionRows)==159, ...
    'Expected 159 prediction records.');
assert(height(metricRows)==9, ...
    'Expected 9 metric records.');

fprintf('\n=== OUTPUT VALIDATION ===\n');
fprintf('Original frames: %d\n',height(T));
fprintf('Models: %d\n',numel(models));
fprintf('Prediction rows: %d\n',height(predictionRows));
fprintf('Metric records: %d\n',height(metricRows));

fprintf('\nFiles saved:\n%s\n%s\n%s\n', ...
    coefPath,metricsPath,predictionPath);

fprintf('\nTASK 29.2B.3: COMPLETE\n');
