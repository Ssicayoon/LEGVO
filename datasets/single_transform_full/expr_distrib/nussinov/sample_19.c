   for (k=i+1; k<j; k++) {
      table[i][j] = max_score(table[i][j], 1*table[i][k] + 1*table[k+1][j]);
   }
