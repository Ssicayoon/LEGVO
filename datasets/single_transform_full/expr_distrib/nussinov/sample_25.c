table[i][j] = max_score(table[i][j], 1*table[i+1][j-1]+1*match(seq[i], seq[j]));
