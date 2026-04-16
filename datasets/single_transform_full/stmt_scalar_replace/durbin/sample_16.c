   for (i=0; i<k; i++) {
      DATA_TYPE zi = y[i];
      zi = zi + alpha*y[k-i-1];
      z[i] = zi;
   }
