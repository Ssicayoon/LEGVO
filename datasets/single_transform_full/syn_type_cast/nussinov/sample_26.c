table[i][j] = max_score(table[i][j], table[i+1][j-1]+(DATA_TYPE)match(seq[i], seq[j]));
