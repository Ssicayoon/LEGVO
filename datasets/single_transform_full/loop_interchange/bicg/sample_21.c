for i in N:
  q[i] = 0
  for j in M:
    s[j] += r[i] * A[i][j]
    q[i] += A[i][j] * p[j]
