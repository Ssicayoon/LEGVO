   for (j = 0; j <i; j++) {
       w = A[i][j];
       for (k = 0; k < j; k++) {
          w -= A[i][k] * A[k][j];
       }
       DATA_TYPE ajj = A[j][j];  // extract, (no accumulation needed), use scalar
       A[i][j] = w / ajj;        // write back implicitly via division
    }
