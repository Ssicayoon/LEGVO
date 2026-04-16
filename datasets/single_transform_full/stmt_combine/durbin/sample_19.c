   alpha = -r[k]/beta;
   for (i=0; i<k; i++) {
      alpha -= r[k-i-1]*y[i]/beta;
   }
