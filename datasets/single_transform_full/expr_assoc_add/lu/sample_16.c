// (A[i][j] + (-A[i][k]*A[k][j])) with regrouping
A[i][j] = (A[i][j] - A[i][k] * A[k][j]); // original grouping in loop 1
// In loop 2, apply a+(b+c) style:
A[i][j] = A[i][j] + (- A[i][k] * A[k][j]);
