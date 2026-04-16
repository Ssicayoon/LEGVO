for (j=_PB_N-2; j>=1; j--) {
  for (i=1; i<_PB_N-1; i++) {
    v[j][i] = p[i][j] * v[j+1][i] + q[i][j];
  }
}
