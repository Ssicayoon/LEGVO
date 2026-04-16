for (j = 0; j < _PB_M; j++)
{
  s[j] = s[j] + r[i] * A[i][j];
  q[i] = q[i] + A[i][j] * p[j];
}
