for (k = 0; k < _PB_NK; k++) {
   for (j = 0; j < _PB_NJ; j++) {
      DATA_TYPE cij = C[i][j];
      cij += alpha * A[i][k] * B[k][j];
      C[i][j] = cij;
   }
}
