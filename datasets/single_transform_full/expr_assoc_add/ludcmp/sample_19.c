static
void kernel_ludcmp(int n, ...) {
  ...
  w = y[i];
  for (j = i+1; j < _PB_N; j++)
     w = (w + 0) - A[i][j] * x[j];  →  w = w + (0 - A[i][j] * x[j]);
