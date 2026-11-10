# Task 25.8C - Quality Gate Evidence Audit

## Status

Offline evidence inventory completed.
No gate has received validated authorization.

## Source dataset verification

- Gate definitions: 6
- Historical scenario summaries: 7
- Historical GT evaluations: 161 scenario-evaluation entries
- Fallback decisions: 168
- Provisional output permissions: 159
- Hold or alert decisions: 9
- Association records: 162
- Provisional Radar spatial matches: 65
- EKF residual audit entries: 23
- Accepted finite Radar NIS values: 4
- Full-rate sensor-health frames: 2122
- Frames with unknown acquisition age: 2122

The GT evaluation entries share underlying recordings and
must not be treated as independent experimental trials.

## G01 - GT-center accuracy

Historical error measurements exist, but no prespecified,
justified numerical acceptance limit has been established.

Cluster-median versus geometric-center differences and
coordinate assumptions remain important limitations.

## G02 - Valid-output coverage

159 provisional and 9 hold classifications are available.

These are not 159 validated perception outputs.
Independent correctness evidence and a prespecified coverage
minimum are missing.

## G03 - Association integrity

Spatial and temporal association evidence is available,
but association correctness is not independently certified.

A small Radar-to-LiDAR box gap does not establish identity.

## G04 - Uncertainty consistency

Residuals and a small number of finite Radar NIS values
are available, but statistical calibration has not been
demonstrated.

## G05 - p99 latency

The current fault-replay dataset has no measured
end-to-end processing latency per decision.

A p99 latency requirement cannot be evaluated.

## G06 - Overall valid result

Overall quality authorization remains UNVERIFIED because
the required hard quality and latency gates have not passed
independent validation.

## Scientific interpretation

UNVERIFIED does not mean a measured gate failure.
Insufficient evidence, missing thresholds and measured
violations must remain distinct.

The fallback controller is internally consistent with its
rules, but it has not established accurate, safe or
deadline-compliant replacement perception.

No energy reduction is claimed.

## Next step

Task 25.8D: document the missing validation measurements
and establish a test-ready quality-evaluation protocol
without fitting acceptance thresholds to historical errors.
