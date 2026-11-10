"""The frame checker. Reads frames.mjs's output and prints, frame by frame, anything passing through a letter
(a bracket's strokes or the dot inside IDIOGRAPH's ink), the dot passing through a bracket, a piece nearer the toolbar's
icons or the notice than --near pixels, a piece cut at the window's left, top or right edge, and a page wider than the
window. Then a summary: each piece's first frame inside the window and how far in it is drawn, its least room from the
toolbar and the notice in pixels, when each piece last moved, the page's errors. --path adds the dot's highs and lows.

A piece's first frames crossing the edge it comes in from are expected (the race's run from beyond the right edge), so
read the cut lines against the way. The spin has no frames to check (frames.mjs says why).

usage: .venv/bin/python3 packaging/motion/check.py <frames.json> [--near 8] [--path]
"""
import argparse
import json
import math

M_ = 15 / 24          # the mark's path units (24 a side) to the lockup's units (15 a side)
R_DOT = 2.7 * M_      # the dot's radius in the lockup's units
# each bracket's three strokes in path units
RECTS = {'lb': [(3.5, 2.5, 9.5, 4.5), (3.5, 2.5, 5.5, 21.5), (3.5, 19.5, 9.5, 21.5)],
         'rb': [(14.5, 2.5, 20.5, 4.5), (18.5, 2.5, 20.5, 21.5), (14.5, 19.5, 20.5, 21.5)]}


def ap(M, x, y):
    return (M[0] * x + M[2] * y + M[4], M[1] * x + M[3] * y + M[5])


def rect_pts(M, rc, step=0.25, shrink=0.06):
    s = shrink / M_
    x0, y0, x1, y1 = rc[0] + s, rc[1] + s, rc[2] - s, rc[3] - s
    nx, ny = max(2, int((x1 - x0) / step) + 1), max(2, int((y1 - y0) / step) + 1)
    return [ap(M, x0 + (x1 - x0) * i / (nx - 1), y0 + (y1 - y0) * j / (ny - 1)) for i in range(nx) for j in range(ny)]


def in_rect(M, rc, p):
    a, b, c, d, e, f = M[:6]
    det = a * d - b * c
    x, y = p[0] - e, p[1] - f
    u, v = (d * x - c * y) / det, (-b * x + a * y) / det
    return rc[0] < u < rc[2] and rc[1] < v < rc[3]


def dot_pts(M, shrink=0.03, n=48):
    rr = R_DOT - shrink
    return [ap(M, rr * math.cos(2 * math.pi * k / n), rr * math.sin(2 * math.pi * k / n)) for k in range(n)]


def bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def gap(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0)
    dy = max(b[1] - a[3], a[1] - b[3], 0)
    return math.hypot(dx, dy) if (dx or dy) else 0.0


def main():
    ap_ = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap_.add_argument('frames')
    ap_.add_argument('--near', type=float, default=8, help='least room in px from the toolbar and the notice (default 8)')
    ap_.add_argument('--path', action='store_true', help="print the dot's highs and lows")
    a = ap_.parse_args()
    D = json.load(open(a.frames))
    info, F, P = D['info'], D['frames'], D['profile']
    if not F:
        print('no frames: the way never drew its scene', D.get('errors'))
        return 1
    u = info['u']
    X0, DX = P[0][0], 0.05

    def ink(x, y, pad):
        i = round((x - X0) / DX)
        if i < 0 or i >= len(P):
            return False
        t, b = P[i][1], P[i][2]
        return t is not None and t + pad < y < b - pad

    issues, rest, last, first, least = [], {}, {}, {}, {}
    for f in F:
        t = f['t']
        out, pieces = [], {}
        for k in ('lb', 'rb'):
            if f[k][6] < 0.3:
                continue
            pts = [p for rc in RECTS[k] for p in rect_pts(f[k], rc)]
            pieces[k] = pts
            bad = [p for p in pts if ink(p[0], p[1], 0.06)]
            if bad:
                out.append(f"{k}-letter({len(bad)} pts at x~{bad[0][0]:.1f})")
        if f['dot'][6] > 0.3:
            dp = dot_pts(f['dot'])
            pieces['dot'] = dp
            bad = [p for p in dp if ink(p[0], p[1], 0.03)]
            if bad:
                out.append(f"dot-letter({len(bad)} at x~{bad[0][0]:.1f},{bad[0][1]:.1f})")
            for k in ('lb', 'rb'):
                if k in pieces:
                    hit = [p for p in dp for rc in RECTS[k] if in_rect(f[k], rc, p)]
                    if hit:
                        out.append(f"dot-{k}({len(hit)})")
        for k, pts in pieces.items():
            bx = bbox(pts)
            if bx[0] >= info['winR'] or bx[2] <= info['winL']:
                continue
            if k not in first:
                first[k] = (t, (info['winR'] - bx[0]) * u)
            for name, others in (('toolbar', info['bars']), ('notice', [info['note']])):
                g = min((gap(bx, b) * u for b in others), default=1e9)
                if g < least.get((k, name), (1e9,))[0]:
                    least[(k, name)] = (g, t)
                if g < a.near:
                    out.append(f"{k}-{name} {g:.1f}px")
            cut = ('L' if bx[0] < info['winL'] < bx[2] else '') + ('T' if bx[1] < info['winT'] < bx[3] else '') + ('R' if bx[0] < info['winR'] < bx[2] else '')
            if cut:
                out.append(f"{k}-cut{cut}")
        if f['sw'] > f['iw']:
            out.append(f"scroll {f['sw']}>{f['iw']}")
        for k in ('lb', 'rb', 'dot'):
            key = tuple(round(v, 4) for v in f[k][:6])
            if last.get(k) != key:
                rest[k] = t
            last[k] = key
        if out:
            issues.append(f"{t:.3f} " + " ".join(out))
    for line in issues:
        print(line)
    print(f"{D.get('way', '?')} at {D.get('width', '?')}: {len(F)} frames to {F[-1]['t']:.3f} s, {len(issues)} with something to look at")
    for k in ('rb', 'lb', 'dot'):
        if k in first:
            print(f"{k} first inside the window at {first[k][0]:.3f} s, drawn {first[k][1]:.1f} px in from the right edge")
    for (k, name), (g, t) in sorted(least.items()):
        print(f"{k} least room from the {name}: {g:.1f} px at {t:.3f} s")
    print('last moved', {k: round(v, 3) for k, v in rest.items()})
    if a.path:
        vis = [(f['t'], f['dot'][4], f['dot'][5]) for f in F if f['dot'][6] > 0.3]
        for i in range(1, len(vis) - 1):
            p, q, r = vis[i - 1][2], vis[i][2], vis[i + 1][2]
            if q < p and q <= r:
                print('dot high t %.3f x %.2f y %.2f' % vis[i])
            if q > p and q >= r:
                print('dot low  t %.3f x %.2f y %.2f' % vis[i])
    print('page errors', D.get('errors') or 'none')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
