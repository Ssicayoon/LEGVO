#pragma scop
  for (r = 0; r < _PB_NR; r++)
    for (q = 0; q < _PB_NQ; q++)  {
      for (p = 0; p < _PB_NP; p++)  {
	DATA_TYPE tmp = SCALAR_VAL(0.0);
	for (s = 0; s < _PB_NP; s++)
	  tmp += A[r][q][s] * C4[s][p];
	sum[p] = tmp;
      }
      for (p = 0; p < _PB_NP; p++)
	A[r][q][p] = sum[p];
    }
#pragma endscop
