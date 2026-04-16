   for (j = 0; j <i; j++) {
       w = A[i][j];
       for (k = 0; k < j; k++) {
          w -= A[i][k] * A[k][j];
       }
       DATA_TYPE ajj = A[j][j];  // extract, accumulate (no change), write back via division
       A[i][j] = w / ajj;
    }
