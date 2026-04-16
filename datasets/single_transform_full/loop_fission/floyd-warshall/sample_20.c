#pragma scop
  for (k = 0; k < _PB_N; k++)
    {
      for(i = 0; i < _PB_N; i++)
        for (j = 0; j < _PB_N/2; j++)
          path[i][j] = path[i][j] < path[i][k] + path[k][j] ?
            path[i][j] : path[i][k] + path[k][j];
      for(i = 0; i < _PB_N; i++)
        for (j = _PB_N/2; j < _PB_N; j++)
          path[i][j] = path[i][j] < path[i][k] + path[k][j] ?
            path[i][j] : path[i][k] + path[k][j];
    }
#pragma endscop
