/* E := A*B */
for (i = 0; i < _PB_NI; i++)
  for (j = 0; j < _PB_NJ; j++) { E[i][j]=...; for k... }
/* F := C*D */  
for (i = 0; i < _PB_NJ; i++)   <- same bound as j above but different loop var
