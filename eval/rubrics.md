# Rubrics

## Verdict
- **NO-GO**: any G0 FAIL; or core G1/G2/G3/G4 FAIL
- **GO-WITH-FIXES**: phase1 GO line met, but enhancements missing (ready probe, json export, target fields)
- **GO**: phase1 minimum line green; remaining items N/A-phase1 or SKIP with reason

## Weights (ordering only)
G0 > G1 core > G2 process up > G3 plumbing > G4 parity > G5 coverage

## Evidence rules
Every PASS/FAIL needs: file path, test name, or HTTP status + body snippet. No prose-only acceptance.
