for (i = 0; i < _PB_N; i++) {
   for (j = 0; j < i; j++) {
      for (k = 0; k < j; k++) {
         A[i][j] -= A[i][k] * A[j][k];
      }
      ...
   }
   ...
}
