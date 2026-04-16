for (j = 0; j < _PB_NL; j++)
{
    G[i][j] = SCALAR_VAL(0.0);  // init inside inner loop
    for (k = 0; k < _PB_NJ; ++k)
        G[i][j] += E[i][k] * F[k][j];
}
