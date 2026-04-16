   for (k=i+1; k<_PB_N-1; k++) {
    for (j=k+1; j<_PB_N; j++) {
      table[i][j] = max_score(table[i][j], table[i][k] + table[k+1][j]);
    }
   }
