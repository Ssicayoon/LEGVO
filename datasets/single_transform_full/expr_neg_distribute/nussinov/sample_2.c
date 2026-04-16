   if (j-1>=0 && i+1<_PB_N) {
     /* don't allow adjacent elements to bond */
     if (i<(-1-(-j)))
        table[i][j] = max_score(table[i][j], table[i+1][(-1-(-j))]+match(seq[i], seq[j]));
     else
        table[i][j] = max_score(table[i][j], table[i+1][(-1-(-j))]);
   }
