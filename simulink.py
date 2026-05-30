import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D

# =========================
# 1. 创建H型钢（简化模型）
# =========================
def draw_h_beam(ax, L=300, H=100, W=60, t=10):

    # 下翼缘
    X = np.array([[0, L], [0, L]])
    Y = np.array([[0, 0], [W, W]])
    Z = np.array([[0, 0], [0, 0]])
    ax.plot_surface(X, Y, Z, color='gray', alpha=0.5)

    # 上翼缘
    Z2 = np.array([[H, H], [H, H]])
    ax.plot_surface(X, Y, Z2, color='gray', alpha=0.5)

    # 腹板
    X3 = np.array([[0, L], [0, L]])
    Y3 = np.array([[W/2 - t/2, W/2 - t/2],
                   [W/2 + t/2, W/2 + t/2]])
    Z3 = np.array([[0, 0], [H, H]])
    ax.plot_surface(X3, Y3, Z3, color='gray', alpha=0.5)

# =========================
# 2. 焊缝路径（腹板中间一条直线）
# =========================
t = np.linspace(0, 1, 150)

L = 300
H = 100
W = 60

x = L * t
y = np.ones_like(t) * (W / 2)
z = H * t  # 竖向焊缝（腹板）

# =========================
# 3. 画布
# =========================
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

ax.set_xlim(0, L)
ax.set_ylim(0, W)
ax.set_zlim(0, H)

ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("H-Beam Welding Simulation")

# =========================
# 4. 画H型钢
# =========================
draw_h_beam(ax)

# =========================
# 5. 焊接轨迹 & 焊枪
# =========================
line, = ax.plot([], [], [], 'r-', linewidth=2, label="Weld Path")
point, = ax.plot([], [], [], 'bo', markersize=5, label="Torch")

ax.legend()

# =========================
# 6. 动画更新
# =========================
def update(frame):

    if frame >= len(x):
        frame = len(x) - 1

    # 焊缝轨迹
    line.set_data(x[:frame], y[:frame])
    line.set_3d_properties(z[:frame]) # type: ignore

    # 焊枪位置
    point.set_data([x[frame]], [y[frame]])
    point.set_3d_properties([z[frame]]) # type: ignore

    return line, point

# =========================
# 7. 动画
# =========================
ani = FuncAnimation(
    fig,
    update,
    frames=len(t),
    interval=40,
    blit=False
)

plt.show()