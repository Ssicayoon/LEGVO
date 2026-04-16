static
void kernel_mvt(int n, ...)
{
  // second loop: hoist x2[i] accumulation
  for (i = 0; i < _PB_N; i++) {
    DATA_TYPE tmp = x2[i];  // hoisted init
    for (j = 0; j < _PB_N; j++)
      tmp = tmp + A[j][i] * y_2[j];
    x2[i] = tmp;
  }
}
