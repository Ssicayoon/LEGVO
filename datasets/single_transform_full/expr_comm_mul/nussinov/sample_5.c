table[i][j] = max_score(table[i][j], table[i+1][j-1]+match(seq[j], seq[i]));
