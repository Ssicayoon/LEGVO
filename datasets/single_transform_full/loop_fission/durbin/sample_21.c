   for (i=0; i<k; i++) {
      z[i] = y[i] + alpha*y[k-i-1];
      y[i] = z[i];  /* split here */
   }
