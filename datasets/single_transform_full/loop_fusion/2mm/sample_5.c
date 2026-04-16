  for (i = 0; i < _PB_NI; i++) {
    for (j = 0; j < _PB_NJ; j++) { ... tmp[i][j] ... }  // writes tmp[i][:]
    for (j = 0; j < _PB_NL; j++) { ... tmp[i][k] ... }  // reads tmp[i][:]
  }
