table[i][j] = max_score(table[i][j], table[i+1][j-1]+(((seq[i]+seq[j]) == 3) ? 1 : 0));
