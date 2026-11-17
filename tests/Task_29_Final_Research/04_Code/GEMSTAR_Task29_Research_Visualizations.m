%% GEMSTAR Task 29 â€” Research visualizations
% Recreates charts from verified conversation-level summary outputs.
% IMPORTANT: This is NOT a hardware measurement or mAP computation.
% No toolboxes required (base MATLAB, R2021a+ recommended).
clear; close all; clc;
outputDir = fullfile(fileparts(fileparts(mfilename('fullpath'))),'01_Graphs','GEMSTAR_Task29_MATLAB_Graphs');
if ~exist(outputDir,'dir'), mkdir(outputDir); end
fprintf('GEMSTAR Task 29: writing figures to %s\n',outputDir);

% DATA PROVENANCE:
% 'CPU_MEASURED': workstation CPU YOLO11n/s measured inference times.
% 'ANNOTATED_SMALL_SET': 12 frames, 7 objects; preliminary model detection stats.
% 'MODELED': synthetic FPGA/ARM scaling, simulated energy, latency, scheduler.
% Values transcribed from verified Task 29 outputs in the conversation.

models = categorical({'YOLO11n','YOLO11s'}); models = reordercats(models,{'YOLO11n','YOLO11s'});
med = [25.081,49.002]; p95 = [28.258,55.374]; p99 = [30.683,60.347];
tp=[2,5]; fp=[7,5]; fn=[5,2]; prec=[22.22,50]; rec=[28.57,71.43]; f1=[0.25,0.5882];
phase={'P1','P2','P3','P4'};
camCPU=[45.260,60.347,75.434,90.520]; other=[0.491,0.494,1.098,0.501];
scenarioNames={'Baseline','Lower DMA','Restore camera FPGA','Both changes'};
miss=[19,12,7,0]; energy=[11269.131,10340.331,8245.323,7316.523];
qwait=[668.341,668.341,125.044,30.669];
speedups=[1,1.25,2,4,8]; admitted=[19,38,47,66,72]; rejected=72-admitted;
energySpeed=[3470.715,6502.881,5071.706,3649.318,2116.069];
overheads=[0,.1,.2,.5,1,2];
phase3=75.434/8+1.098+overheads;
phase4=90.520/8+.501+overheads;
robustNames={'CPU baseline','8x ideal','8x +2ms','10x +2ms','12x +2ms','8x outages','10x outages','12x outages'};
robustOnTime=[0,72,34,72,72,19,32,54];
robustLate=72-robustOnTime;
robustWait=[5610.491,0,128.936,0,0,230.071,144.077,86.748];
robustResponse=[2896.266,11.816,78.284,11.553,10.044,117.201,74.739,46.430];

% Helper to create figures with consistent appearance.
fig = @(n) figure('Name',n,'Color','w','Position',[80 80 1050 600]);

%% 01 Recorded CPU inference latency (workstation)
f=fig('01 CPU inference latency');
bar(models,[med(:),p95(:),p99(:)]); grid on;
ylabel('Latency (ms)'); legend('Median','P95','P99','Location','northwest');
title('01 | YOLO CPU inference latency â€” recorded workstation evidence');
subtitle('Does not include sensor fusion or FPGA execution'); saveF(f,outputDir,'01_CPU_Inference_Latency');

%% 02 Small dataset quality comparison
f=fig('02 Small dataset detection quality');
bar(models,[prec(:),rec(:),100*f1(:)]); grid on; ylim([0 100]);
ylabel('Percent (%)');legend('Precision','Recall','F1 Ã— 100','Location','northwest');
title('02 | Controlled 12-frame dataset â€” preliminary detection quality');
subtitle('Only seven annotated reference objects; not mAP and not deployment validation');saveF(f,outputDir,'02_Controlled_Quality');

%% 03 Confusion count components
f=fig('03 Detection counts');
bar(models,[tp(:),fp(:),fn(:)]);grid on;ylabel('Object count');
legend('TP','FP','FN','Location','northwest');title('03 | Detection accounting');
subtitle('Small controlled set; manually reviewed annotations are provisional');saveF(f,outputDir,'03_TP_FP_FN');

%% 04 Modeled pipeline stage breakdown P3 and P4
f=fig('04 Pipeline stage breakdown');
components=[0.0172,11.9974,0.3303,10.7500;71.9846+0.0207,0,0.3303,0.1500];
bar(categorical({'Phase 3','Phase 4'}),components,'stacked');grid on;
ylabel('Modeled service time (ms)');legend('CPU camera / radar','Camera FPGA','LiDAR FPGA','DMA','Location','northwest');
title('04 | Stage bottlenecks â€” hypothetical FPGA cost model');
subtitle('Modeled steady-state only; P3 camera FPGA vs P4 camera CPU'); saveF(f,outputDir,'04_Stage_Costs');

%% 05 Modeled what-if missed deadlines
f=fig('05 Deadline misses architecture scenarios');
bar(categorical(scenarioNames),miss);grid on;ylim([0 20]);
ylabel('Deadline misses (out of 72 jobs)');title('05 | Architecture what-if replay â€” deadline misses');
subtitle('Hypothetical DMA and FPGA availability changes; NOT measured hardware');saveF(f,outputDir,'05_WhatIf_DeadlineMisses');

%% 06 Modeled active energy, paired across same what-if event set
f=fig('06 What-if energy');
bar(categorical(scenarioNames),energy);grid on;
ylabel('Modeled active energy (mJ)');title('06 | Architecture what-if replay â€” active energy');
subtitle('Illustrative model, not total board energy');saveF(f,outputDir,'06_WhatIf_ActiveEnergy');

%% 07 Model requirements and capacity vs 75/12 ms
f=fig('07 Minimum service per phase');
plot(1:4,camCPU+other,'o-','LineWidth',2,'MarkerSize',8);hold on;
yline(75,'--','75 ms job deadline'); yline(12,':','12 ms burst interval');
grid on;xticks(1:4);xticklabels(phase);xlabel('Synthetic phase');ylabel('Time (ms)');
title('07 | Quality-eligible YOLO11s CPU pipeline minimum time');
subtitle('Workstation inference scaled with hypothetical ARM factors; zero queue, no switch penalty');saveF(f,outputDir,'07_Phase_Service_and_Targets');

%% 08 Required speedup for 12ms service by phase
f=fig('08 Required speedup');
target=(camCPU./(12-other));bar(categorical(phase),target);grid on;
ylabel('Minimum camera-only speedup (Ã—)');yline(8,'--','8Ã— reference');
title('08 | Required camera compute speedup for 12 ms service');
subtitle('Ignores new FPGA transfer, launch and switching overhead');saveF(f,outputDir,'08_Minimum_Speedup_Target');

%% 09 Admission outcomes for hypothetical scaling
f=fig('09 Queue admission with speedup');
bar(categorical(compose('%gx',speedups)),[admitted(:),rejected(:)],'stacked');grid on;
ylabel('Jobs (72 total)');legend('Admitted','Rejected','Location','eastoutside');
title('09 | Quality-constrained scheduler â€” hypothetical camera speedup');
subtitle('Unchanged F1 assumed, rejected jobs are NOT valid completions');saveF(f,outputDir,'09_Admitted_vs_Rejected');

%% 10 Modeled active energy per admitted job (not comparable hardware energy)
f=fig('10 Modeled energy per admitted job');
bar(categorical(compose('%gx',speedups)),energySpeed./admitted);grid on;
ylabel('Modeled active energy per admitted job (mJ)');
title('10 | Illustrative energy efficiency, conditioned on admission');
subtitle('CPU time scaling only; acceleration energy and overhead are unmeasured');saveF(f,outputDir,'10_Energy_Per_Admitted_Job');

%% 11 Overhead sensitivity at 8x
f=fig('11 Overhead sensitivity');
plot(overheads,phase3,'o-','LineWidth',2);hold on;
plot(overheads,phase4,'s-','LineWidth',2);yline(12,'k--','12 ms capacity target');
grid on;xlabel('Additional per-job overhead (ms)');ylabel('Steady-state service time (ms)');
legend('Phase 3','Phase 4','12 ms','Location','northwest');
title('11 | Why 8Ã— acceleration has a small margin');subtitle('Synthetic overhead; phase 4 exceeds 12 ms at 0.2 ms extra');saveF(f,outputDir,'11_Overhead_Sensitivity');

%% 12 Robustness: all jobs processed, late counted
f=fig('12 Robustness late jobs');
barh(categorical(robustNames),[robustOnTime(:),robustLate(:)],'stacked');grid on;
xlabel('Jobs (72 processed)');legend('On-time','Late','Location','best');
title('12 | Synthetic Phase 4 robustness (no job dropping)');
subtitle('Periodic outages force ~91 ms CPU fallback; NOT a physical failure test');saveF(f,outputDir,'12_Robustness_OnTime_Late');

%% 13 Robustness response-time vs deadline
f=fig('13 Mean response time');
bar(categorical(robustNames),robustResponse);hold on;yline(75,'--','75 ms deadline');grid on;
ylabel('Mean response time (ms)');title('13 | Mean response time across synthetic robustness scenarios');
subtitle('Mean alone does NOT establish P99 deadline performance');saveF(f,outputDir,'13_Mean_Response_Time');

%% 14 Robustness maximum queue wait
f=fig('14 Maximum queue wait');
bar(categorical(robustNames),robustWait);grid on;
ylabel('Maximum queue wait (ms)');title('14 | Queue accumulation under overhead and outages');
subtitle('72-job synthetic Phase 4 FIFO tests; includes CPU baseline');saveF(f,outputDir,'14_Max_Queue_Wait');

%% 15 Latency-energy scatter for matched architecture what-if assumptions
f=fig('15 Modeled energy vs deadline misses');
scatter(miss,energy,110,'filled');grid on;
for k=1:numel(miss), text(miss(k)+.15,energy(k),scenarioNames{k},'FontSize',9);end
xlabel('Deadline misses (lower is better)');ylabel('Modeled active energy (mJ, lower is better)');
title('15 | Modeled Pareto view: energy vs deadline misses');
subtitle('Same 72 jobs, but quality/FPGA capability not validated');saveF(f,outputDir,'15_Pareto_WhatIf');

%% 16 Visualize 8x stage budget vs 12ms arrival constraint
f=fig('16 Phase timing margin');
service8=camCPU/8+other;
bar(categorical(phase),[service8(:),12-service8(:)],'stacked');grid on;
ylabel('Time to 12 ms budget (ms)');legend('Service','Remaining margin','Location','northwest');
title('16 | 8Ã— modeled camera speedup â€” phase-specific timing margin');
subtitle('Excludes additional acceleration-specific costs');saveF(f,outputDir,'16_8x_Timing_Margin');

fprintf('\nGenerated 16 research figures (PNG and FIG each) in %s\n',outputDir);
fprintf('IMPORTANT: GEMSTAR-specific mAP50 and mAP50-95 cannot be computed from these aggregates.\n');
fprintf('To calculate mAP, supply complete per-image ground truth and scored predictions.\n');

function saveF(h,path,name)
  savefig(h,fullfile(path,[name '.fig']));
  try
     exportgraphics(h,fullfile(path,[name '.png']),'Resolution',180);
  catch
     saveas(h,fullfile(path,[name '.png']));
  end
  fprintf('Saved %s\n',name);
end

