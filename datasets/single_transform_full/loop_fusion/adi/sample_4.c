// Merge the two `for i` loops in Row Sweep into one
for (i=1; i<_PB_N-1; i++) {
    // body of first i-loop (forward j)
    // body of second i-loop (backward j)  -- but these depend on ALL i of first loop
