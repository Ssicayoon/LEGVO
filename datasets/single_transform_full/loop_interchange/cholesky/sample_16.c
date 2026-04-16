for (t = 0; t < n; ++t)
    for (r = 0; r < n; ++r)
      for (s = 0; s < n; ++s)
        B[r][s] += A[r][t] * A[s][t];
