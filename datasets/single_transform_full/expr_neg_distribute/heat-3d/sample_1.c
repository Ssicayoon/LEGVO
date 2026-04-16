// -(SCALAR_VAL(2.0) * A[i][j][k] + (-A[i][j][k-1])) → (-SCALAR_VAL(2.0) * A[i][j][k] - (-A[i][j][k-1]))
// i.e., A[i][j][k+1] - SCALAR_VAL(2.0)*A[i][j][k] + A[i][j][k-1]
//     = A[i][j][k+1] + (-SCALAR_VAL(2.0)*A[i][j][k] - (-A[i][j][k-1]))
