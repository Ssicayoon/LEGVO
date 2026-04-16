#pragma scop
  for (k = 0; k < _PB_N; k++)
    {
      for(i = 0; i < _PB_N * _PB_N; i++)
	  path[i/_PB_N][i%_PB_N] = path[i/_PB_N][i%_PB_N] < path[i/_PB_N][k] + path[k][i%_PB_N] ?
	    path[i/_PB_N][i%_PB_N] : path[i/_PB_N][k] + path[k][i%_PB_N];
    }
#pragma endscop
