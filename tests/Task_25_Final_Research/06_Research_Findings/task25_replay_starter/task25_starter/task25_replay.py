"""Task 25: repeatable, offline fault-injection study of Task 24 EKF.
No originals are modified; GT is read only for evaluation AFTER state estimation.
Requires Python 3.10+, numpy, matplotlib.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from collections import defaultdict, Counter
from pathlib import Path
from statistics import median, mean
import numpy as np

C, FREQ = 299792458., 77e9
RADAR_POS = (2., 0.)
CAM_X = .7
H_L = np.array([[1.,0.,0.,0.],[0.,1.,0.,0.]])
I4 = np.eye(4)
SCENARIOS = ['baseline','radar_dropout','camera_dropout','lidar_every4_dropout','radar_bias_6mps','camera_bias_0p20rad','joint_dropout']

def rows(path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def num(s):
    return float(s)

def writecsv(path, data):
    if not data: raise ValueError('No data to write: '+str(path))
    with path.open('w', newline='', encoding='utf-8') as f:
        writer=csv.DictWriter(f, fieldnames=list(data[0])); writer.writeheader(); writer.writerows(data)

def update(x,P,H,res,R):
    S=H@P@H.T+R
    K=np.linalg.solve(S, H@P).T
    y=x+K@res
    A=I4-K@H
    Q=A@P@A.T+K@R@K.T
    return y,(Q+Q.T)/2

def predict(x,P,dt):
    F=np.array([[1,0,dt,0],[0,1,0,dt],[0,0,1,0],[0,0,0,1]],float)
    Q=np.array([[dt**4/4,0,dt**3/2,0],[0,dt**4/4,0,dt**3/2],[dt**3/2,0,dt**2,0],[0,dt**3/2,0,dt**2]],float)
    return F@x,F@P@F.T+Q

def radial(x):
    dx=x[0]-RADAR_POS[0];dy=x[1]-RADAR_POS[1]; r=math.hypot(dx,dy)
    if r<.1: raise ValueError('Radar singularity')
    ux=dx/r;uy=dy/r;v=ux*x[2]+uy*x[3]
    H=np.array([[(x[2]-v*ux)/r,(x[3]-v*uy)/r,ux,uy]])
    return v,H

def camera(x):
    dx=x[0]-CAM_X;dy=x[1];d2=dx*dx+dy*dy
    if dx<=0 or d2<.01: raise ValueError('Camera geometry invalid')
    return math.atan2(-dy,dx),np.array([[dy/d2,-dx/d2,0.,0.]])

def wrap(v): return math.atan2(math.sin(v),math.cos(v))

def load_inputs(d):
    names=['lidar_temporal_tracks_v1.csv','radar_track_matches_v1.csv','camera_bearing_track2_frame530_v1.csv','lidar_radar_ekf_track2_v1.csv','lidar_radar_camera_ekf_track2_v1.csv','gt_robustness_per_frame_v1.csv']
    for n in names:
        if not (d/n).is_file(): raise FileNotFoundError('Missing Task 24 source: '+str(d/n))
    tracks=sorted([r for r in rows(d/names[0]) if int(r['track_id'])==2],key=lambda r:float(r['time_s']))
    if len(tracks)!=24 or len({int(r['frame']) for r in tracks})!=24: raise ValueError('Expected 24 distinct Track 2 observations')
    radar=defaultdict(list)
    for r in rows(d/names[1]):
        if int(r['track_id'])!=2: continue
        doppler=float(r['doppler_shift_raw'])
        if not math.isfinite(doppler): raise ValueError('Nonfinite Doppler')
        if abs(doppler)>1e-9: radar[int(r['frame'])].append((float(r['time_s']),doppler))
    cam=rows(d/names[2]);ref=rows(d/names[3]);refcam=rows(d/names[4]);gt=rows(d/names[5]);
    if len(cam)!=1 or int(cam[0]['frame'])!=530 or int(cam[0]['track_id'])!=2 or cam[0]['status']!='BEARING_GEOMETRICALLY_COMPATIBLE_NOT_CALIBRATED':
        raise ValueError('Camera association is not the expected experimental sample')
    if len(ref)!=24 or len(refcam)!=24: raise ValueError('Baseline mismatch')
    for a,b,c in zip(tracks,ref,refcam):
        if not (int(a['frame'])==int(b['frame'])==int(c['frame'])): raise ValueError('Reference frame misalignment')
        if abs(float(a['time_s'])-float(b['time_s']))>1e-6 or abs(float(a['time_s'])-float(c['time_s']))>1e-6: raise ValueError('Reference timestamp misalignment')
    gt_map={int(r['frame']):r for r in gt}
    # GT centers reconstructed from the Task24 output's signed radar error (evaluation only)
    centers={}
    for idx,r in enumerate(ref):
        fr=int(r['frame'])
        if fr in gt_map:
            g=gt_map[fr]
            centers[fr]=(float(r['radar_ekf_x_m'])-float(g['radar_x_error_m']),float(r['radar_ekf_y_m'])-float(g['radar_y_error_m']))
    hashes=[{'file':n,'sha256':hashlib.sha256((d/n).read_bytes()).hexdigest()} for n in names]
    return tracks,radar,cam[0],ref,refcam,centers,hashes

def replay(tracks,radar,cam,scenario):
    x0=np.array([float(tracks[0]['x_m']),float(tracks[0]['y_m']),0.,0.]);P0=np.diag([1.,1.,4.,4.])
    states=[x0.copy() for _ in range(3)];covs=[P0.copy() for _ in range(3)]
    output=[]
    for i,row in enumerate(tracks):
        frame=int(row['frame']);t=float(row['time_s']);n=int(row['point_count']);z=np.array([float(row['x_m']),float(row['y_m'])]);
        if n<=0: raise ValueError('Bad point count')
        if i:
            dt=t-float(tracks[i-1]['time_s'])
            if dt<=0: raise ValueError('Non-increasing time')
            for j in range(3): states[j],covs[j]=predict(states[j],covs[j],dt)
        drop_lidar=i>0 and ((scenario=='lidar_every4_dropout' and i%4==0) or (scenario=='joint_dropout' and 10<=i<=13))
        if i and not drop_lidar:
            R=np.eye(2)*(.60*min(2.,max(1.,12./n)))**2
            for j in range(3): states[j],covs[j]=update(states[j],covs[j],H_L,z-H_L@states[j],R)
        values=radar.get(frame,[])
        if any(abs(rt-t)>1e-4 for rt,_ in values): raise ValueError(f'Radar timestamp mismatch at {frame}')
        rad_status='NOT_AVAILABLE';nis=float('nan')
        drop_radar=scenario=='radar_dropout' or (scenario=='joint_dropout' and 10<=i<=13)
        if values and drop_radar: rad_status='INJECTED_DROPOUT'
        elif values:
            if len(values)<2:rad_status='INSUFFICIENT_RETURNS'
            else:
                measurement=float(median([fd*C/(2*FREQ) for _,fd in values]))
                if scenario=='radar_bias_6mps': measurement+=6.
                accepted=[]
                for j in (1,2):
                    pred,H=radial(states[j]);innovation=measurement-pred;R=np.array([[4.]])
                    S=float((H@covs[j]@H.T)[0,0]+4.)
                    candidate=innovation**2/S
                    if j==1:nis=candidate
                    if candidate<=9.:
                        states[j],covs[j]=update(states[j],covs[j],H,np.array([innovation]),R);accepted.append(True)
                    else: accepted.append(False)
                rad_status='ACCEPTED' if accepted[0] else 'REJECTED_BY_NIS'
                if scenario=='baseline' and accepted[0]!=accepted[1]:raise ValueError('Baseline Radar decisions differ')
        cam_status='NO_UPDATE';cam_nis=float('nan')
        if frame==530:
            if scenario=='camera_dropout' or (scenario=='joint_dropout' and 10<=i<=13):cam_status='INJECTED_DROPOUT'
            else:
                meas=float(cam['camera_bearing_rad'])
                if scenario=='camera_bias_0p20rad':meas+=.20
                pred,H=camera(states[2]);innovation=wrap(meas-pred)
                R=np.array([[max(.05,float(cam['assumed_bearing_sigma_rad']))**2]])
                S=float((H@covs[2]@H.T)[0,0]+R[0,0]);cam_nis=innovation**2/S
                if cam_nis<=9.:
                    states[2],covs[2]=update(states[2],covs[2],H,np.array([innovation]),R);cam_status='EXPERIMENTAL_ACCEPTED'
                else:cam_status='REJECTED_BY_NIS'
        output.append({'scenario':scenario,'sample':i,'frame':frame,'time_s':t,'lidar_used':int(not drop_lidar),'lidar_cluster_points':n,'radar_status':rad_status,'radar_nis':nis,'camera_status':cam_status,'camera_nis':cam_nis,'lidar_only_x_m':states[0][0],'lidar_only_y_m':states[0][1],'lidar_radar_x_m':states[1][0],'lidar_radar_y_m':states[1][1],'fusion_x_m':states[2][0],'fusion_y_m':states[2][1],'fusion_std_x_m':math.sqrt(covs[2][0,0])})
    return output

def validate_baseline(replayed,reference,camref):
    maxdiff=0.
    for a,b,c in zip(replayed,reference,camref):
        for generated,original in [('lidar_only_x_m',float(b['lidar_only_x_m'])),('lidar_only_y_m',float(b['lidar_only_y_m'])),('lidar_radar_x_m',float(b['radar_ekf_x_m'])),('lidar_radar_y_m',float(b['radar_ekf_y_m'])),('fusion_x_m',float(c['camera_aided_x_m'])),('fusion_y_m',float(c['camera_aided_y_m']))]:
            maxdiff=max(maxdiff,abs(float(a[generated])-original))
    if maxdiff>1e-5:raise AssertionError(f'Baseline replay mismatch: max difference {maxdiff:.8g} m. STOP; no fault conclusions justified.')
    return maxdiff

def summary(data,centers):
    results=[]
    for scen in SCENARIOS:
        d=[r for r in data if r['scenario']==scen]
        gt=[(r,centers[r['frame']]) for r in d if r['frame'] in centers]
        error=[math.hypot(float(r['fusion_x_m'])-c[0],float(r['fusion_y_m'])-c[1]) for r,c in gt]
        results.append({'scenario':scen,'samples':len(d),'gt_evaluation_samples':len(error),'mean_gt_center_error_m':mean(error) if error else '', 'rmse_gt_center_m':math.sqrt(mean([e*e for e in error])) if error else '', 'max_gt_center_error_m':max(error) if error else '', 'lidar_measurement_used':sum(r['lidar_used'] for r in d),'radar_updates_accepted':sum(r['radar_status']=='ACCEPTED' for r in d),'radar_nis_rejected':sum(r['radar_status']=='REJECTED_BY_NIS' for r in d),'camera_updates_accepted':sum(r['camera_status']=='EXPERIMENTAL_ACCEPTED' for r in d)})
    return results

def plot(data,summaries,centers,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    d={s:[r for r in data if r['scenario']==s] for s in SCENARIOS}
    fig,ax=plt.subplots(figsize=(10,5));
    for s in ['baseline','radar_dropout','camera_dropout','lidar_every4_dropout','joint_dropout']:
        seq=d[s];ax.plot([r['time_s'] for r in seq],[r['fusion_x_m'] for r in seq],marker='.',label=s)
    ax.set(xlabel='Time (s)',ylabel='Estimated longitudinal position (m)',title='Task25 — Fault-injection EKF replay, provisional Track 2');ax.legend(fontsize=8);ax.grid(alpha=.25);fig.tight_layout();fig.savefig(out/'04_Plots'/'task25_trajectory_x.png',dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,5)); ax.bar([r['scenario'] for r in summaries],[r['mean_gt_center_error_m'] for r in summaries]);ax.tick_params(axis='x',rotation=40);ax.set(ylabel='Mean GT center error (m)',title='Single-development-recording sensitivity (NOT generalization)');fig.tight_layout();fig.savefig(out/'04_Plots'/'task25_fault_sensitivity.png',dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,7))
    for s in ['baseline','joint_dropout']:
        a=d[s];ax.plot([r['fusion_x_m'] for r in a],[r['fusion_y_m'] for r in a],marker='.',label=s)
    cg=sorted(centers.items());ax.plot([xy[0] for _,xy in cg],[xy[1] for _,xy in cg],marker='x',linestyle='--',label='GT centers (evaluation only)')
    ax.set(xlabel='X (m) ego frame',ylabel='Y (m) ego frame',title='Geometric BEV diagnostic — not calibrated occupancy');ax.axis('equal');ax.legend();ax.grid(alpha=.25);fig.tight_layout();fig.savefig(out/'04_Plots'/'task25_bev_diagnostic.png',dpi=150);plt.close(fig)

def main():
    p=argparse.ArgumentParser();p.add_argument('--task24',type=Path,required=True,help='Task24 C02_V2_EKF_Input_53Frames_V1 folder');p.add_argument('--task25',type=Path,required=True,help='Task25_Final_Research folder');a=p.parse_args()
    d=a.task24.resolve();o=a.task25.resolve()
    for n in ('01_Code','02_CSV_Data','03_Configurations','04_Plots','05_Raw_Data_References','06_Research_Findings','07_Research_Report'):(o/n).mkdir(parents=True,exist_ok=True)
    track,rad,cam,ref,camref,gt,hashes=load_inputs(d)
    experiments=[]
    for name in SCENARIOS:experiments.extend(replay(track,rad,cam,name))
    base=[r for r in experiments if r['scenario']=='baseline'];maxdiff=validate_baseline(base,ref,camref)
    summ=summary(experiments,gt)
    writecsv(o/'02_CSV_Data'/'task25_replay_samples.csv',experiments)
    writecsv(o/'02_CSV_Data'/'task25_fault_summary.csv',summ)
    writecsv(o/'05_Raw_Data_References'/'task25_sha256_manifest.csv',hashes)
    plot(experiments,summ,gt,o)
    report=['# Task 25 — Preliminary reliability and failure-injection findings','',f'- Task 24 C02 source: `{d}`',f'- Reproduced baseline maximum coordinate mismatch: **{maxdiff:.3g} m**',f'- Task 24 GT-center evaluation frames: **{len(gt)}**','- Selected provisional Track 2: **24 samples**','- GT used only after replay, for evaluation.','- All scenarios use the same observation frames/timestamps and EKF equations.','- Radar sigma 2 m/s, LiDAR sigma 0.60 m, Camera sigma minimum 0.05 rad: **uncalibrated experimental assumptions**.','- No full covariance export/NEES, calibrated detection or association precision/recall.','- No real fog/traffic replication or hardware energy/latency measurement.','- GT center and LiDAR visible surface are not equivalent measurement references.','- Failure injections are exploratory software sensitivity experiments, **not a validated safety case**.','', '## Scenario results','', '| Scenario | Mean GT-center error (m) | RMSE (m) | Radar accepted | Camera accepted |','|---|---:|---:|---:|---:|']
    for r in summ:report.append(f"| {r['scenario']} | {r['mean_gt_center_error_m']:.6f} | {r['rmse_gt_center_m']:.6f} | {r['radar_updates_accepted']} | {r['camera_updates_accepted']} |")
    report.extend(['','## Next required for Task 25 completion','1. Verify exported figures, source hashes, replay states and failure scenarios.','2. Validate on independent clear/fog/traffic recordings; current C02 is development-only.','3. Calibrate sensor geometry and uncertainties; test association false positives and missed detections.','4. Predefine perception and p99 latency constraints before claiming acceptable fallback.','5. Document genuine end-to-end CPU cost; hardware power measurement belongs to later tasks.',''])
    (o/'06_Research_Findings'/'Task25_preliminary_findings.md').write_text('\n'.join(report),encoding='utf-8')
    print('BASELINE_REPLAY_PASS',maxdiff,'m');print('GT_FRAMES',len(gt));print('SAMPLES',len(track));
    for r in summ:print(r['scenario'],'mean_error_m=',round(r['mean_gt_center_error_m'],6),'radar=',r['radar_updates_accepted'],'camera=',r['camera_updates_accepted'])
    print('SAVED_TO',o)
if __name__=='__main__':main()
