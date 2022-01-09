from mpi4py import MPI
import numpy as np
import math

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
p_num = size - 1
f = open("input5.txt", "r")
Lines = f.readlines()

args = Lines[0].split(' ')

N = int(args[0])
wave = int(args[1])
tower = int(args[2])
nof_processor_per_row = math.sqrt(p_num)
n = int(N // nof_processor_per_row)  # küçük karelerin boyutu


def isSafe(index):
    global nof_processor_per_row
    return 0 <= index < nof_processor_per_row


if rank == 0:
    line_idx = 1
    health = np.zeros(shape=(N, N), dtype=np.ndarray)
    board = np.zeros(shape=(N, N), dtype=np.ndarray)

    while (wave != 0):
        wave = wave - 1
        o_coords = [o.split() for o in Lines[line_idx].split(',')]
        for coord in o_coords:
            if board[int(coord[0])][int(coord[1])] == 0:
                board[int(coord[0])][int(coord[1])] = 1
                health[int(coord[0])][int(coord[1])] = 6
        line_idx += 1
        x_coords = [x.split() for x in Lines[line_idx].split(',')]
        for coord in x_coords:
            if board[int(coord[0])][int(coord[1])] == 0:
                board[int(coord[0])][int(coord[1])] = 2
                health[int(coord[0])][int(coord[1])] = 8
        line_idx += 1

        for round in range(8):

            col_start = 0
            col_end = n
            row_start = 0
            row_end = n
            for i in range(1, p_num + 1):
                board_data = board[row_start:row_end, col_start:col_end]
                health_data = health[row_start:row_end, col_start:col_end]
                if (col_end == N):
                    col_start = 0
                    col_end = n
                    row_start += n
                    row_end += n
                else:
                    col_start += n
                    col_end += n

                comm.send(wave, dest=i, tag=20)
                for k in range(n):
                    comm.send(board_data[k].tolist(), dest=i,
                              tag=(5 * k))  # Burada n tane row gönderiliyor, farklı taglerle
                    comm.send(health_data[k].tolist(), dest=i, tag=14 * k)

            col_start = 0
            col_end = n
            row_start = 0
            row_end = n
            for i in range(1, p_num + 1):
                b_partition = comm.recv(source=i, tag=5)
                h_partition = comm.recv(source=i, tag=14)
                board[row_start:row_end, col_start:col_end] = b_partition
                health[row_start:row_end, col_start:col_end] = h_partition
                if (col_end == N):
                    col_start = 0
                    col_end = n
                    row_start += n
                    row_end += n
                else:
                    col_start += n
                    col_end += n

    
    for i in range(N):
        for k in range(N):
            if k == N-1:
                s = ""
            else:
                s = " "
            if board[i][k] == 1:
                print("o", end = s)
            elif board[i][k] == 2:
                print("+", end = s)
            else:
                print(".", end = s)
        print()

else:

    while (wave > 0):
        for round in range(8):
            wave = comm.recv(source=0, tag=20)
            board = []
            health = []
            for k in range(n):
                b_data = comm.recv(source=0, tag=(5 * k))
                h_data = comm.recv(source=0, tag=14 * k)
                board.append(b_data)
                health.append(h_data)

            board = np.array(board)

            health = np.array(health)

            wide_board = np.zeros(shape=(n + 2, n + 2), dtype=np.ndarray)

            col_idx = (rank - 1) % nof_processor_per_row
            row_idx = (rank - 1) // nof_processor_per_row

            if (rank % 2 == 1):  # önce tekler çift komşularına gönderecek

                if isSafe(col_idx + 1):  # sağa
            
                    comm.send(board[:, n - 1], dest=rank + 1, tag=0)

                if isSafe(col_idx - 1):  # sola
                
                    comm.send(board[:, 0], dest=rank - 1, tag=1)

                if isSafe(row_idx - 1):  # yukarı
                    # comm.send(board[0, :], dest=rank - nof_processor_per_row, tag=2)
                    if isSafe(col_idx + 1):  # yukarı sağ
                    
                        comm.send(board[0, n - 1], dest=rank - nof_processor_per_row + 1, tag=4)
                    if isSafe(col_idx - 1):  # yukarı sol
                     
                        comm.send(board[0, 0], dest=rank - nof_processor_per_row - 1, tag=5)

                if isSafe(row_idx + 1):  # aşağı
                    # comm.send(board[n-1, :], dest=rank + nof_processor_per_row, tag=3)
                    if isSafe(col_idx + 1):  # aşağı sağ
                    
                        comm.send(board[n - 1, n - 1], dest=int(rank + nof_processor_per_row + 1), tag=6)

                    if isSafe(col_idx - 1):  # aşağı sol
    
                        comm.send(board[n - 1, 0], dest=rank + nof_processor_per_row - 1, tag=7)

                # şimdi tekler çift komşularından alcak

                if isSafe(col_idx - 1):  # soldan
                    wide_board[1:n + 1, 0] = comm.recv(source=rank - 1, tag=0)
                if isSafe(col_idx + 1):  # sağdan
                    wide_board[1:n + 1, n + 1] = comm.recv(source=rank + 1, tag=1)

                if isSafe(row_idx + 1):  # aşağıdan
                    # wide_board[n,1:n] = comm.recv(source=rank + nof_processor_per_row, tag=3)
                    if isSafe(col_idx - 1):  # aşağı sol

                        wide_board[n + 1, 0] = comm.recv(source=rank + nof_processor_per_row - 1, tag=4)
                     
                    if isSafe(col_idx + 1):  # aşağı sağ

                        wide_board[n + 1, n + 1] = comm.recv(source=rank + nof_processor_per_row + 1, tag=5)
                     

                if isSafe(row_idx - 1):  # yukarıdan
                    # wide_board[0, 1:n] = comm.recv(source=rank - nof_processor_per_row, tag=2)
                    if isSafe(col_idx + 1):  # yukarı sağ

                        wide_board[0, n + 1] = comm.recv(source=rank - nof_processor_per_row + 1, tag=7)
                 
                    if isSafe(col_idx - 1):  # yukarı sol

                        wide_board[0, 0] = comm.recv(source=rank - nof_processor_per_row - 1, tag=6)
                   

                wide_board[1:n + 1, 1:n + 1] = board

         

            else:  # çiftler tek komşularından alacak

                if isSafe(col_idx - 1):  # soldan
                    wide_board[1:n + 1, 0] = comm.recv(source=rank - 1, tag=0)

                if isSafe(col_idx + 1):  # sağdan
          
                    wide_board[1:n + 1, n + 1] = comm.recv(source=rank + 1, tag=1)
                 

                if isSafe(row_idx + 1):  # aşağıdan
                    # wide_board[n,1:n] = comm.recv(source=rank + nof_processor_per_row, tag=3)
                    if isSafe(col_idx - 1):  # aşağı sol
                    
                        wide_board[n + 1, 0] = comm.recv(source=int(rank + nof_processor_per_row - 1), tag=4)
                    
                    if isSafe(col_idx + 1):  # aşağı sağ

                        wide_board[n + 1, n + 1] = comm.recv(source=rank + nof_processor_per_row + 1, tag=5)
                     

                if isSafe(row_idx - 1):  # yukarıdan
                    # wide_board[0, 1:n] = comm.recv(source=rank - nof_processor_per_row, tag=2)
                    if isSafe(col_idx + 1):  # yukarı sağ

                        wide_board[0, n + 1] = comm.recv(source=rank - nof_processor_per_row + 1, tag=7)
                    
                    if isSafe(col_idx - 1):  # yukarı sol

                        wide_board[0, 0] = comm.recv(source=rank - nof_processor_per_row - 1, tag=6)
                     

                wide_board[1:n + 1, 1:n + 1] = board

                #### çiftler teklere yollucak
                if isSafe(col_idx + 1):  # sağa
                
                    comm.send(board[:, n - 1], dest=rank + 1, tag=0)

                if isSafe(col_idx - 1):  # sola
                
                    comm.send(board[:, 0], dest=rank - 1, tag=1)

                if isSafe(row_idx - 1):  # yukarı
                    # comm.send(board[0, :], dest=rank - nof_processor_per_row, tag=2)
                    if isSafe(col_idx + 1):  # yukarı sağ
                    
                        comm.send(board[0, n - 1], dest=rank - nof_processor_per_row + 1, tag=4)
                    if isSafe(col_idx - 1):  # yukarı sol
                    
                        comm.send(board[0, 0], dest=rank - nof_processor_per_row - 1, tag=5)

                if isSafe(row_idx + 1):  # aşağı
                    # comm.send(board[n-1, :], dest=rank + nof_processor_per_row, tag=3)
                    if isSafe(col_idx + 1):  # aşağı sağ
                    
                        comm.send(board[n - 1, n - 1], dest=rank + nof_processor_per_row + 1, tag=6)
                    if isSafe(col_idx - 1):  # aşağı sol
                    
                        comm.send(board[n - 1, 0], dest=rank + nof_processor_per_row - 1, tag=7)

            if (row_idx % 2 == 0):

                if isSafe(row_idx - 1):  # yukarı
                    comm.send(board[0, :], dest=rank - nof_processor_per_row, tag=2)

                if isSafe(row_idx + 1):  # aşağı
                    comm.send(board[n - 1, :], dest=rank + nof_processor_per_row, tag=3)

                if isSafe(row_idx + 1):  # aşağıdan
                    wide_board[n + 1, 1:n + 1] = comm.recv(source=rank + nof_processor_per_row, tag=2)

                if isSafe(row_idx - 1):  # yukarıdan
                    wide_board[0, 1:n + 1] = comm.recv(source=rank - nof_processor_per_row, tag=3)

            

            else:
                if isSafe(row_idx + 1):  # aşağıdan
                    wide_board[n + 1, 1:n + 1] = comm.recv(source=rank + nof_processor_per_row, tag=2)

                if isSafe(row_idx - 1):  # yukarıdan
                    wide_board[0, 1:n + 1] = comm.recv(source=rank - nof_processor_per_row, tag=3)

                if isSafe(row_idx - 1):  # yukarı
                    comm.send(board[0, :], dest=rank - nof_processor_per_row, tag=2)

                if isSafe(row_idx + 1):  # aşağı
                    comm.send(board[n - 1, :], dest=rank + nof_processor_per_row, tag=3)

           
            dead_towers = []
            for i in range(1, n + 1):
                for k in range(1, n + 1):
                    name = wide_board[i][k]
                    enemy = 0
                    if (name == 0):
                        continue
                    elif (name == 1):  # o's
                        enemy = 2

                    else:  # +'s
                        enemy = 1

                        if (wide_board[i - 1][k - 1] == enemy):
                            health[i - 1][k - 1] -= enemy

                        if (wide_board[i + 1][k + 1] == enemy):
                            health[i - 1][k - 1] -= enemy

                        if (wide_board[i - 1][k + 1] == enemy):
                            health[i - 1][k - 1] -= enemy

                        if (wide_board[i + 1][k - 1] == enemy):
                            health[i - 1][k - 1] -= enemy

                    if (wide_board[i - 1][k] == enemy):
                        health[i - 1][k - 1] -= enemy
                    if (wide_board[i + 1][k] == enemy):
                        health[i - 1][k - 1] -= enemy
                    if (wide_board[i][k - 1] == enemy):
                        health[i - 1][k - 1] -= enemy
                    if (wide_board[i][k + 1] == enemy):
                        health[i - 1][k - 1] -= enemy

                    if (health[i - 1][k - 1] <= 0):
                        dead_towers.append((i-1,k-1))

            for towers in dead_towers:
                health[towers[0]][towers[1]] = 0
                board[towers[0]][towers[1]] = 0
                wide_board[towers[0] + 1][towers[1] + 1] = 0
                

            comm.send(board.tolist(), dest=0, tag=5)  # Burada n tane row gönderiliyor, farklı taglerle
            comm.send(health.tolist(), dest=0, tag=14)
            

           