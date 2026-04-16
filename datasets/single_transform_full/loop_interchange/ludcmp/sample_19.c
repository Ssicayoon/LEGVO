for (i = _PB_N-1; i >=0; i--) {
   w = b[i];
   for (j = 0; j < i; j++)
      w -= A[i][j] * y[j];
   y[i] = w;
}
