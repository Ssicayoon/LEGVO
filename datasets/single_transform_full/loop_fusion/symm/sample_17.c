// Before merge (conceptually):
for (j = 0; j < _PB_N; j++) temp2 = 0; // init
for (j = 0; j < _PB_N; j++) { ... }    // compute
// After merge: single j loop
