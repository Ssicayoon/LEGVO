static
void kernel_atax(...)
{
  ...
#pragma scop
  for (i = 0; i < _PB_N; i++)
    y[i] = 0 + 0;  // was: y[i] = 0  (2*0 → 0+0)
  ...
#pragma endscop
}
