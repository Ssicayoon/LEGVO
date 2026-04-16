for i:
  for j (0..i):      ← outer
    for k (0..j):    ← inner
      A[i][j] -= A[i][k]*A[j][k]
    A[i][j] /= A[j][j]
  for k (0..i):
    A[i][i] -= A[i][k]*A[i][k]
