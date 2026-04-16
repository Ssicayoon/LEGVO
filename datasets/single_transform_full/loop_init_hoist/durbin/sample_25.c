for (k = 1; k < _PB_N; k++) {
   beta = (1-alpha*alpha)*beta;
   sum = SCALAR_VAL(0.0);  // sum is reset to 0 each iteration of k loop
   for (i=0; i<k; i++) {
      sum += r[k-i-1]*y[i];
   }
