beta = (1-alpha*alpha)*beta;
sum = SCALAR_VAL(0.0);
for (i=0; i<k; i++) {
   sum += r[k-i-1]*y[i];
}
alpha = - (r[k] + sum)/beta;

for (i=0; i<k; i++) {
   z[i] = y[i] + alpha*y[k-i-1];
}
for (i=0; i<k; i++) {
  y[i] = z[i];
}
y[k] = alpha;
