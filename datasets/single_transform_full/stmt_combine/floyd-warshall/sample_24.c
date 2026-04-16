static
void kernel_floyd_warshall(int n,
			   DATA_TYPE POLYBENCH_2D(path,N,N,n,n))
{
  int i, j, k;
  DATA_TYPE t;

#pragma scop
  for (k = 0; k < _PB_N; k++)
    {
      for(i = 0; i < _PB_N; i++)
	for (j = 0; j < _PB_N; j++) {
	  t = path[i][k] + path[k][j];
	  path[i][j] = path[i][j] < t ? path[i][j] : t;
	}
    }
#pragma endscop

}
