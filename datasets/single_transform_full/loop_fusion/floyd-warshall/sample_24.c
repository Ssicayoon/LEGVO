static
void kernel_floyd_warshall(int n,
			   DATA_TYPE POLYBENCH_2D(path,N,N,n,n))
{
  int i, j, k;

#pragma scop
  for (k = 0; k < _PB_N; k++)
    {
      for(i = 0; i < _PB_N * _PB_N; i++)
	  path[i/_PB_N][i%_PB_N] = path[i/_PB_N][i%_PB_N] < path[i/_PB_N][k] + path[k][i%_PB_N] ?
	    path[i/_PB_N][i%_PB_N] : path[i/_PB_N][k] + path[k][i%_PB_N];
    }
#pragma endscop

}
