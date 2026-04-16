#pragma scop

  for (i = 0; i < _PB_NX; i++)
    ex[i][0] = ex[i][0];

  for(t = 0; t < _PB_TMAX; t++)
    {
