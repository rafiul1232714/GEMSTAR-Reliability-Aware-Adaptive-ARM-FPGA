# Task 25.9D - Cross-Language Integrity and Discrepancy Resolution

## Numerical reproducibility

Python and MATLAB independently recalculated 18 metrics.

- Integer count metrics: 11
- Floating-point metrics: 7
- Comparisons passed: 18
- Comparisons failed after correction: 0
- Maximum absolute difference: 2.2204460492503101E-16

The comparison used absolute tolerance 1e-10 and
relative tolerance 1e-9 for floating-point metrics.
Integer count metrics required exact equality.

## Original discrepancy

The initial MATLAB analysis passed 11 integer metrics,
but failed seven floating-point comparisons.

The initial maximum difference was approximately 1.31e-5.

The discrepancy was consistent with unnecessary conversion
of numeric MATLAB columns into strings and back.

## Correction

A precision-preserving conversion helper was introduced.

Numeric columns remain double values.
Text columns are converted using str2double.

The original research CSV inputs and numerical comparison
tolerances were not changed to obtain agreement.

## Data integrity

- Dataset hashes verified: 11
- Dataset row counts verified: 11
- Original MATLAB script backup present: True
- Initial failed-comparison backup present: True

## Research interpretation

The Python and MATLAB calculations now agree for all
18 selected numerical metrics.

This supports computational reproducibility.

It does not independently validate sensor calibration,
target identity, perception accuracy or EKF uncertainty.

QUALITY_AUTHORIZATION: UNVERIFIED

ENERGY_SAVINGS_CLAIMED: NO

## Next task

Task 25.9E: final numerical cross-validation research report.
