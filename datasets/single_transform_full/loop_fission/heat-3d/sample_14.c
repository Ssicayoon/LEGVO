/* Split the i-loop of the A-update into two independent i-loops */
for (i = 1; i < (_PB_N-1)/2; i++) { ... }
for (i = (_PB_N-1)/2; i < _PB_N-1; i++) { ... }
