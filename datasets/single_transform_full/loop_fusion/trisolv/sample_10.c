// Before merge (conceptual split):
for (i = 0; i < _PB_N; i++) x[i] = b[i];
for (i = 0; i < _PB_N; i++) { for (j=0;j<i;j++) x[i]-=L[i][j]*x[j]; x[i]/=L[i][i]; }
// After merge:
for (i = 0; i < _PB_N; i++) { x[i] = b[i]; for (j=0;j<i;j++) x[i]-=L[i][j]*x[j]; x[i]/=L[i][i]; }
