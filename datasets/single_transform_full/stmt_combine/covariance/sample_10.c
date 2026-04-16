mean[j] = SCALAR_VAL(0.0);
for (i = 0; i < _PB_N; i++)
    mean[j] += data[i][j];
mean[j] /= float_n;
