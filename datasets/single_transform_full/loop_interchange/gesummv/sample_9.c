for i:
  tmp[i] = 0; y[i] = 0;
  for j:
    tmp[i] += A[i][j]*x[j];
    y[i] += B[i][j]*x[j];
  y[i] = alpha*tmp[i] + beta*y[i];
