      table[i][j] = max_score(table[i][j], 1*(table[i][k] + table[k+1][j]));
