for (i = ...)
  for (j = ...)
  {
    temp2 = 0;        // initialized here, inside both i and j loops
    for (k = 0; k < i; k++) {
      ...
      temp2 += B[k][j] * A[i][k];
    }
    C[i][j] = ... + alpha * temp2;
  }
