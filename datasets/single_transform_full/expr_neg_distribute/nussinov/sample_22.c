table[i][j] = max_score(table[i][j], table[i+1][(-1+j)]+match(seq[i], seq[j]));
