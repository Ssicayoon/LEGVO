static
void kernel_floyd_warshall(int n,
			   DATA_TYPE POLYBENCH_2D(path,N,N,n,n))
{
  int i, j, k;

#pragma scop
  for (k = 0; k < _PB_N; k++)
    {
      for(i = 0; i < _PB_N; i++) {
        DATA_TYPE path_ik = path[i][k];
	for (j = 0; j < _PB_N; j++)
	  path[i][j] = path[i][j] < path_ik + path[k][j] ?
	    path[i][j] : path_ik + path[k][j];
      }
    }
#pragma endscop
}
