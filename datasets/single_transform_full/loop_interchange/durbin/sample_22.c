for (k = 1; k < _PB_N; k++) {
   ...
   for (i=0; i<k; i++) { sum += r[k-i-1]*y[i]; }  // loop A
   ...
   for (i=0; i<k; i++) { z[i] = y[i] + alpha*y[k-i-1]; }  // loop B
   for (i=0; i<k; i++) { y[i] = z[i]; }  // loop C
   y[k] = alpha;
}
