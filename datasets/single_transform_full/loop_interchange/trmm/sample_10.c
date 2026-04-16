for i:
  for j:
    for k: B[i][j] += A[k][i] * B[k][j]
    B[i][j] = alpha * B[i][j]
