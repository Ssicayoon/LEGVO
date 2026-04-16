/* Main computational kernel. */
static
void kernel_gemm(...)
{
  ...
  for (i ...) {
    for (j ...) C[i][j] *= beta;
    for (k ...) {
       for (j ...)
          C[i][j] += alpha * A[i][k] * B[k][j];
    }
  }
