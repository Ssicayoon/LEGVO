for t: for i: for j:
    A[i][j] = f(A[i-1][j-1], A[i-1][j], A[i-1][j+1],
                A[i][j-1],   A[i][j],   A[i][j+1],
                A[i+1][j-1], A[i+1][j], A[i+1][j+1])
