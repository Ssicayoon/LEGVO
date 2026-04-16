/* F := C*D */
for (i = 0; i < _PB_NJ; i++)
  for (j = 0; j < _PB_NL; j++)
    F[i][j] = SCALAR_VAL(0.0);
for (i = 0; i < _PB_NJ; i++)
  for (j = 0; j < _PB_NL; j++)
    for (k = 0; k < _PB_NM; ++k)
      F[i][j] += C[i][k] * D[k][j];
