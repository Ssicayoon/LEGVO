for (i=0; i<k; i++) {
   z[i] = y[i] + alpha*y[k-i-1];
}
for (i=0; i<k; i++) {
   y[i] = z[i];
}
