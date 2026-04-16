  /* E := A*B and G := E*F in merged i-loop (F must be computed first) */
  /* F := C*D */
  for (i = 0; i < _PB_NJ; i++)
    for (j = 0; j < _PB_NL; j++) { ... }
  /* Merged E and G */
  for (i = 0; i < _PB_NI; i++) { E[i][j] ... G[i][j] ... }
