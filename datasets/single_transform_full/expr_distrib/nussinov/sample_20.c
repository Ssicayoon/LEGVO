if (i<j-1)
   table[i][j] = max_score(table[i][j], table[i+1][j-1]+(((1*seq[i]+1*seq[j])==3)?1:0));
