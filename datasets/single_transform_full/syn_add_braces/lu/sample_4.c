for (j = 0; j <i; j++) {
   for (k = 0; k < j; k++) {
      A[i][j] -= A[i][k] * A[k][j];
   }
    A[i][j] /= A[j][j];
}
