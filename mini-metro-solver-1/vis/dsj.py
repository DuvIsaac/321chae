import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

# 초기 설정
n = 50  # 점의 개수
num_routes = 3  # 경로의 개수
pltN = 10

# 고정된 점의 위치를 랜덤하게 생성
np.random.seed(1)  # 재현성을 위해 시드 설정
x = np.random.uniform(0, 20, n)
y = np.random.uniform(0, 10, n)
shapes = np.random.choice(['^', 's', 'o'], n)

lw = 1
ms = 10

plt.figure(1)
plt.clf()
for i in range(n):
    plt.plot(x[i], y[i], shapes[i], linewidth=lw, markersize=ms)
plt.box(True)
plt.axis('equal')
plt.axis([0, 20, 0, 10])
plt.pause(1)

# 거리 행렬 계산
dmat = np.zeros((n, n))
for i in range(n):
    for j in range(n):
        dmat[i, j] = np.sqrt((x[i] - x[j])**2 + (y[i] - y[j])**2)

# k-means 클러스터링을 사용하여 중심점 찾기
kmeans = KMeans(n_clusters=num_routes, random_state=42)
kmeans.fit(np.column_stack((x, y)))
centroids = kmeans.cluster_centers_

# 각 점에 가장 가까운 중심점에 할당
assignments = np.argmin(np.sqrt((x[:, np.newaxis] - centroids[:, 0])**2 + (y[:, np.newaxis] - centroids[:, 1])**2), axis=1)

# 각 경로에 할당된 점들 모으기
cluster_points = [[] for _ in range(num_routes)]
for i, cluster_idx in enumerate(assignments):
    cluster_points[cluster_idx].append(i)

# 초기 경로 설정
Routes = [np.array(points) for points in cluster_points]

# 초기 경로를 그리기
plt.figure(1)
plt.clf()
for p in range(num_routes):
    rte = Routes[p]
    xx = np.append(x[rte], x[rte[0]])
    yy = np.append(y[rte], y[rte[0]])
    plt.plot(xx, yy, '-', linewidth=lw)  # 점을 그리지 않도록 '-' 스타일 사용
for i in range(n):
    plt.plot(x[i], y[i], shapes[i], markersize=ms)  # 점을 다시 그리기
plt.box(True)
plt.axis('equal')
plt.axis([0, 20, 0, 10])
plt.pause(1)

# 메인 최적화 루프
flag = True
dold = 1e12
iter = 0
distHistory = []

while flag:
    iter += 1
    totalDist = np.zeros(num_routes)
    
    for p in range(num_routes):
        route = Routes[p]
        d = dmat[route[-1], route[0]]
        for k in range(1, len(route)):
            d += dmat[route[k-1], route[k]]
        totalDist[p] = d
    
    minDist = np.sum(totalDist)
    distHistory.append(minDist)

    if iter % 200 == 0:
        if distHistory[-1] < dold:
            dold = distHistory[-1]
        else:
            flag = False

    if iter % pltN == 0:
        plt.figure(1)
        plt.clf()
        for p in range(num_routes):
            rte = Routes[p]
            xx = np.append(x[rte], x[rte[0]])
            yy = np.append(y[rte], y[rte[0]])
            plt.plot(xx, yy, '-', linewidth=lw)  # 점을 그리지 않도록 '-' 스타일 사용
        for i in range(n):
            plt.plot(x[i], y[i], shapes[i], markersize=ms)  # 점을 다시 그리기
        plt.title(f'Total Distance = {minDist:.4f}, Iteration = {iter}')
        plt.box(True)
        plt.axis('equal')
        plt.axis([0, 20, 0, 10])
        plt.pause(0.02)

    # 최적의 경로 찾기 및 업데이트
    for p in range(num_routes):
        BestRoute = Routes[p]
        n_sub = len(BestRoute)
        randomIJ = np.sort(np.random.randint(0, n_sub, 2))
        I, J = randomIJ
        new_routes = [BestRoute.copy() for _ in range(4)]
        
        if I < J:
            new_routes[1][I:J+1] = BestRoute[I:J+1][::-1]  # 2-opt
        new_routes[2][[I, J]] = BestRoute[[J, I]]  # Swap
        if I+1 <= J:
            new_routes[3][I:J+1] = np.append(BestRoute[I+1:J+1], BestRoute[I])  # Shift
        
        # 3-opt 추가
        for _ in range(2):  # 3-opt 연산을 두 번 실행하여 변이 확률 증가
            randomIJK = np.sort(np.random.randint(0, n_sub, 3))
            i, j, k = randomIJK
            if i < j < k:
                new_routes[3] = np.concatenate([BestRoute[:i+1], BestRoute[j:k+1], BestRoute[i+1:j], BestRoute[k+1:]])
        
        # 새로운 경로들 중 최적 경로 선택
        new_dists = np.zeros(4)
        for r in range(4):
            d = dmat[new_routes[r][-1], new_routes[r][0]]
            for k in range(1, n_sub):
                d += dmat[new_routes[r][k-1], new_routes[r][k]]
            new_dists[r] = d
        
        best_new_route_idx = np.argmin(new_dists)
        Routes[p] = new_routes[best_new_route_idx]

