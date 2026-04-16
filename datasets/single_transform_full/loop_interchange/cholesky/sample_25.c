for (i = 0; i < _PB_N; i++) {
   for (j = 0; j < i; j++) {        // j loop
      for (k = 0; k < j; k++) {     // k loop (innermost of j)
         A[i][j] -= A[i][k] * A[j][k];
      }
      A[i][j] /= A[j][j];
   }
   for (k = 0; k < i; k++) {        // k loop (diagonal)
      A[i][i] -= A[i][k] * A[i][k];
   }
   A[i][i] = SQRT_FUN(A[i][i]);
}
