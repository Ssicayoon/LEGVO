*alpha = 1.5;  -- init, unchanged
*beta = 1.2;   -- init, unchanged  
A[i][j] = (DATA_TYPE) ((i*j+1)%n) / n;  -- init, unchanged
C[i][j] = (DATA_TYPE) ((i*j+2)%m) / m;  -- init, unchanged
(i * n + j) % 20 -- print, unchanged
C[i][j] *= beta;  -- kernel
C[i][j] += alpha * A[i][k] * A[j][k];  -- kernel
