for (i = 0; i < _PB_N; i++)    // outer loop
{
    tmp[i] = 0.0;
    y[i] = 0.0;
    for (j = 0; j < _PB_N; j++)  // inner loop
    {
        tmp[i] = A[i][j] * x[j] + tmp[i];
        y[i] = B[i][j] * x[j] + y[i];
    }
    y[i] = alpha * tmp[i] + beta * y[i];
}
