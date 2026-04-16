for (j = k + 1; j < _PB_N; j++)
{
  R[k][j] = SCALAR_VAL(0.0);  // This is inside the j-loop
  for (i = 0; i < _PB_M; i++)
    R[k][j] += Q[i][k] * A[i][j];
  ...
}
