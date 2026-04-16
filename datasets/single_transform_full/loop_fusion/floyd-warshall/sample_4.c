static
void kernel_floyd_warshall(int n,
			   DATA_TYPE POLYBENCH_2D(path,N,N,n,n))
{
  int i, j, k, ij;

#pragma scop
  for (k = 0; k < _PB_N; k++)
    {
      for(ij = 0; ij < _PB_N * _PB_N; ij++)
      {
        i = ij / _PB_N;
        j = ij % _PB_N;
	path[i][j] = path[i][j] < path[i][k] + path[k][j] ?
	  path[i][j] : path[i][k] + path[k][j];
      }
    }
#pragma endscop
}
