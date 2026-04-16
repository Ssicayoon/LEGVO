   for (j = i; j < _PB_N; j++) {
       w = A[i][j];
       for (k = 0; k < i; k++) {
          DATA_TYPE akj = A[k][j];  // extract, accumulate, write back
          w -= A[i][k] * akj;
       }
       A[i][j] = w;
    }
