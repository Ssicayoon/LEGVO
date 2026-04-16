  /* E := A*B and G := E*F (merged i-loop, after F is computed) */
  /* F := C*D first */
  for (i = 0; i < _PB_NJ; i++)
    for (j = 0; j < _PB_NL; j++) { F[i][j] = ...; }
  /* merged E and G over i */
  for (i = 0; i < _PB_NI; i++) { E rows, then G rows }
