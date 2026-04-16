for (j = 0; j <i; j++) {
   w = A[i][j];
   for (k = 0; k < j; k++) {
      w -= A[i][k] * A[k][j];
   }
   DATA_TYPE tmp_ajj = A[j][j];
   A[i][j] = w / tmp_ajj;
}
