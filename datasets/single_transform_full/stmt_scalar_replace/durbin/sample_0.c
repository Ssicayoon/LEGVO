   for (i=0; i<k; i++) {
      DATA_TYPE yi = y[i];
      z[i] = yi + alpha*y[k-i-1];
   }
