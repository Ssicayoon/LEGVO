// A[i][j] -= A[i][k] * A[k][j]  (second loop)
// = (A[i][j] + (- A[i][k]*A[k][j]))  -- change to explicit form showing associativity
A[i][j] = A[i][j] + (-(A[i][k] * A[k][j]));
