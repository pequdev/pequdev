#!/usr/bin/env python3
"""Outlined ASCII portrait from a BMP: the figure is separated from the red
background, then edges become line characters (- / | \\) by direction.
Usage: python3 outline.py pic.bmp > ascii.txt"""
import math, struct, sys

data = open(sys.argv[1], "rb").read()
off = struct.unpack_from("<I", data, 10)[0]
W, H = struct.unpack_from("<ii", data, 18)
bpp = struct.unpack_from("<H", data, 28)[0] // 8
row = ((bpp * 8 * W + 31) // 32) * 4
flip = H > 0
H = abs(H)

def px(x, y):
    i = off + ((H - 1 - y) if flip else y) * row + x * bpp
    return data[i + 2], data[i + 1], data[i]

lum = [[0.0] * W for _ in range(H)]
fig = [[False] * W for _ in range(H)]
for y in range(H):
    for x in range(W):
        r, g, b = px(x, y)
        lum[y][x] = (0.3 * r + 0.59 * g + 0.11 * b) / 255
        fig[y][x] = not (r - max(g, b) > 45)       # not red sky

def erode(m, n):
    for _ in range(n):
        m = [[m[y][x] and all(m[yy][xx] for yy in (y - 1, y, y + 1) for xx in (x - 1, x, x + 1)
              if 0 <= yy < H and 0 <= xx < W) for x in range(W)] for y in range(H)]
    return m

def dilate(m, n):
    for _ in range(n):
        m = [[any(m[yy][xx] for yy in (y - 1, y, y + 1) for xx in (x - 1, x, x + 1)
              if 0 <= yy < H and 0 <= xx < W) for x in range(W)] for y in range(H)]
    return m

# drop thin power lines and the tower lattice: erode, keep the largest blob, grow back
core = erode(fig, 2)
seen = [[False] * W for _ in range(H)]
best = []
for sy in range(H):
    for sx in range(W):
        if core[sy][sx] and not seen[sy][sx]:
            stack, comp = [(sx, sy)], []
            seen[sy][sx] = True
            while stack:
                x, y = stack.pop()
                comp.append((x, y))
                for xx, yy in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= xx < W and 0 <= yy < H and core[yy][xx] and not seen[yy][xx]:
                        seen[yy][xx] = True
                        stack.append((xx, yy))
            if len(comp) > len(best):
                best = comp
blob = [[False] * W for _ in range(H)]
for x, y in best:
    blob[y][x] = True
blob = dilate(blob, 2)
mask = [[blob[y][x] and fig[y][x] for x in range(W)] for y in range(H)]
# outside the figure counts as black, so the silhouette itself becomes an edge
L = [[lum[y][x] if mask[y][x] else 0.0 for x in range(W)] for y in range(H)]

def sobel(x, y):
    g = lambda xx, yy: L[min(H - 1, max(0, yy))][min(W - 1, max(0, xx))]
    gx = (g(x + 1, y - 1) + 2 * g(x + 1, y) + g(x + 1, y + 1)) - (g(x - 1, y - 1) + 2 * g(x - 1, y) + g(x - 1, y + 1))
    gy = (g(x - 1, y + 1) + 2 * g(x, y + 1) + g(x + 1, y + 1)) - (g(x - 1, y - 1) + 2 * g(x, y - 1) + g(x + 1, y - 1))
    return gx, gy

CW, CH = 2, 4                       # a character is about twice as tall as wide
out = []
for cy in range(0, H - CH + 1, CH):
    line = ""
    for cx in range(0, W - CW + 1, CW):
        best_m, gx_s, gy_s, inside = 0.0, 0.0, 0.0, 0
        for y in range(cy, cy + CH):
            for x in range(cx, cx + CW):
                gx, gy = sobel(x, y)
                m = math.hypot(gx, gy)
                inside += mask[y][x]
                if m > best_m:
                    best_m, gx_s, gy_s = m, gx, gy
        if best_m < 0.7 or inside == 0 and best_m < 1.6:
            line += " "
            continue
        # edge runs perpendicular to the gradient; y grows downwards
        a = (math.degrees(math.atan2(-gy_s, gx_s)) + 90) % 180
        line += "-" if a < 22.5 or a >= 157.5 else "/" if a < 67.5 else "|" if a < 112.5 else "\\"
    out.append(line.rstrip())
while out and not out[0]:
    out.pop(0)
print("\n".join(out))
