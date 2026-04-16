// (A[i][j] + (-A[i][k] * A[j][k])) — change associativity of the addition
A[i][j] = A[i][j] + (-A[i][k] * A[j][k]);
// vs original effectively: A[i][j] -= A[i][k] * A[j][k]
