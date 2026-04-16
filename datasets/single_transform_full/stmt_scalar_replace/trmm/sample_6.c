for (k = i+1; k < _PB_M; k++) {
   DATA_TYPE tmp = A[k][i];
   B[i][j] += tmp * B[k][j];
}
