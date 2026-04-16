for (p = 0; p < _PB_NP; p++)
    A[r][q][p] = sum[p];
for (p = 0; p < _PB_NP; p++)  {
    sum[p] = SCALAR_VAL(0.0);
    for (s = 0; s < _PB_NP; s++)
      sum[p] += A[r][q][s] * C4[s][p];
}
