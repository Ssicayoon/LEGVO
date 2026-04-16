#pragma scop
 for (i = _PB_N-1; i >= 0; i--) {
  for (j=i+1; j<_PB_N; j++) {
   table[i][j] = 0;
  }
  for (j=i+1; j<_PB_N; j++) {

   if (j-1>=0)
      table[i][j] = max_score(table[i][j], table[i][j-1]);
