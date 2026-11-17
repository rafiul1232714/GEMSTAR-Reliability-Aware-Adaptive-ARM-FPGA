ARRIVAL_MS = 12.0
DEADLINE_MS = 75.0
CAMERA_REFERENCE_MS = 90.520
OTHER_MS = 0.501
JOBS = 72

def simulate(speedup, overhead, outage_every=0):
    server_free = 0.0
    late = 0
    max_wait = 0.0
    total_response = 0.0
    outage_count = 0

    for i in range(JOBS):
        arrival = i * ARRIVAL_MS
        outage = outage_every > 0 and (i + 1) % outage_every == 0

        if outage:
            outage_count += 1
            service = CAMERA_REFERENCE_MS + OTHER_MS + overhead
        else:
            service = CAMERA_REFERENCE_MS / speedup + OTHER_MS + overhead

        start = max(arrival, server_free)
        finish = start + service
        response = finish - arrival

        late += int(response > DEADLINE_MS)
        max_wait = max(max_wait, start - arrival)
        total_response += response
        server_free = finish

    return {
        "late": late,
        "on_time": JOBS - late,
        "max_wait": max_wait,
        "mean_response": total_response / JOBS,
        "outages": outage_count
    }

cases = [
    ("CPU_BASELINE", 1.0, 0.0, 0),
    ("ACCEL_8X", 8.0, 0.0, 0),
    ("ACCEL_8X_OVERHEAD_2", 8.0, 2.0, 0),
    ("ACCEL_10X_OVERHEAD_2", 10.0, 2.0, 0),
    ("ACCEL_12X_OVERHEAD_2", 12.0, 2.0, 0),
    ("ACCEL_8X_OUTAGE", 8.0, 0.0, 20),
    ("ACCEL_10X_OUTAGE", 10.0, 0.0, 20),
    ("ACCEL_12X_OUTAGE", 12.0, 0.0, 20),
]

print("=== COMPARATIVE RESULTS ===")
print(
    f"{'Configuration':24s} {'OnTime':>6s} "
    f"{'Late':>5s} {'Outages':>7s} "
    f"{'MaxWait':>9s} {'MeanResponse':>12s}"
)

for name, speedup, overhead, outage_every in cases:
    r = simulate(speedup, overhead, outage_every)

    print(
        f"{name:24s} "
        f"{r['on_time']:6d} "
        f"{r['late']:5d} "
        f"{r['outages']:7d} "
        f"{r['max_wait']:9.3f} "
        f"{r['mean_response']:12.3f}"
    )

print()
print("JOBS PER CONFIGURATION:", JOBS)
print("JOBS DROPPED: 0")
print("QUALITY: ASSUMED UNCHANGED")
print("SYNTHETIC PHASE 4 MODEL: YES")
print("COMPLETE SCHEDULER POLICIES COMPARED: NO")
print("POWER AND FPGA PERFORMANCE MEASURED: NO")
print("EXISTING FILES MODIFIED: NO")
print("STATUS: TASK 29.5E.9X COMPARISON COMPLETE")