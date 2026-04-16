for (j = 0; j < _PB_M; j++)
{
    stddev[j] = SCALAR_VAL(0.0);  // this is inside the j-loop, initialized before inner i-loop
    for (i = 0; i < _PB_N; i++)
        stddev[j] += ...;
    ...
}
