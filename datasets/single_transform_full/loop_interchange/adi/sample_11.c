// Original:
for (i=1; i<_PB_N-1; i++) {
  ...
  for (j=_PB_N-2; j>=1; j--) {
    v[j][i] = p[i][j] * v[j+1][i] + q[i][j];
  }
}
// Swapped: j outer, i inner
