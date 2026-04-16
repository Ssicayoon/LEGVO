void kernel(int N, double A[N][N], double B[N][N], double C[N][N]) {
#pragma scop
    for (int j = 0; j < N; j++)
        for (int i = 0; i < N; i++)
            A[i][j] = B[i][j] + C[i][j];
#pragma endscop
}
