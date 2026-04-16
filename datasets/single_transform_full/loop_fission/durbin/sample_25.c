   for (i=0; i<k; i++) {
      sum += r[k-i-1]*y[i];
      z[i] = y[i] + alpha*y[k-i-1];  // NOT independent - depends on alpha computed after
   }
