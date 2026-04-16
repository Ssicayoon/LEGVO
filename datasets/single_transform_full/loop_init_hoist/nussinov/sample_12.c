static
void kernel_nussinov(int n, base POLYBENCH_1D(seq,N,n),
			   DATA_TYPE POLYBENCH_2D(table,N,N,n,n))
{
  int i, j, k;

#pragma scop
 for (i = _PB_N-1; i >= 0; i--) {
  table[i][i] = 0;
  for (j=i+1; j<_PB_N; j++) {
   table[i][j] = 0;

   if (j-1>=0)
      table[i][j] = max_score(table[i][j], table[i][j-1]);
   if (i+1<_PB_N)
      table[i][j] = max_score(table[i][j], table[i+1][j]);

   if (j-1>=0 && i+1<_PB_N) {
     if (i<j-1)
        table[i][j] = max_score(table[i][j], table[i+1][j-1]+match(seq[i], seq[j]));
     else
        table[i][j] = max_score(table[i][j], table[i+1][j-1]);
   }

   for (k=i+1; k<j; k++) {
      table[i][j] = max_score(table[i][j], table[i][k] + table[k+1][j]);
   }
  }
 }
#pragma endscop
}
