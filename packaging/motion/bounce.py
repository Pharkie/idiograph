"""The bounce solver: searches for a ball's flight onto the mark, worked backward from the middle. Thrown in from the
right, one bounce on a letter, one on the right bracket's top arm, then up and steeply down into the middle, narrowing
to pass between the arms' tips. The race's ball (markplay8, 23 October 2026) came from it.

The ball's gravity is --speed squared times the mark's own dot's (the drop and bounce every way shares), so the whole
flight is --speed times quicker along the same kind of path. Each bounce keeps --e of the pace up. A candidate is kept
when the ball needs to narrow to no less than --squeeze of its width between the tips and keeps --clear units over the
letters along its first arc. Units are the lockup's (107.33 across, the letters' tops at 2.5), seconds for time.

Each candidate written: xa (where it leaves the arm), yap (its last high), x1 and y1 (the bounce on the letters), up1
and vx1 (its speed off them), vx_l and up_l (off the arm), ex_arm (the pace across the arm keeps), sq, apex_in (the high
before the arm), apexT and vyT (the throw's high and its speed down at the first bounce), t_arc1 and t_last (the two
arcs' times), clear.

usage: .venv/bin/python3 packaging/motion/bounce.py <profile.json> <out.json> [--speed 1.5] [--e 0.84]
       [--squeeze 0.8] [--clear 0.4] [--show 5]
       (profile.json from profile.mjs)
"""
import argparse
import json
import math

M_ = 15 / 24
R_BALL = 2.7 * M_
# the mark's dot: from 44.8 units above to rest in a first bounce of 0.526 s
G_MARK = 8 * (44.8 * ((6.8 / 44.8) ** 0.5)) / (0.526 ** 2) * M_
ARM_Y = 2.5 * M_
ARM_REST = ARM_Y - R_BALL
BAND = (ARM_Y + 4.5 * M_) / 2
TIPS = [(9.5 * M_, ARM_Y), (9.5 * M_, 4.5 * M_), (14.5 * M_, ARM_Y), (14.5 * M_, 4.5 * M_)]


def main():
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    p.add_argument('profile')
    p.add_argument('out')
    p.add_argument('--speed', type=float, default=1.5)
    p.add_argument('--e', type=float, default=0.84)
    p.add_argument('--squeeze', type=float, default=0.8)
    p.add_argument('--clear', type=float, default=0.4)
    p.add_argument('--show', type=int, default=5)
    a = p.parse_args()
    P = json.load(open(a.profile))
    XS, TOP = [c[0] for c in P], [c[1] for c in P]
    X0, DX = XS[0], 0.05
    r, e = R_BALL, a.e
    g = G_MARK * a.speed * a.speed

    def rest_y(x):
        best = None
        for X, T in zip(XS, TOP):
            if T is None or abs(X - x) >= r:
                continue
            y = T - math.sqrt(r * r - (X - x) ** 2)
            best = y if best is None else min(best, y)
        return best

    REST = [1e9 if rest_y(x) is None else rest_y(x) for x in XS]

    def R(x):
        i = (x - X0) / DX
        if i < 0 or i >= len(REST) - 1:
            return 1e9
        j = int(i)
        return min(REST[j], REST[j + 1])

    def squeeze(vx, yap):
        worst = 1.0
        tb = math.sqrt(2 * (BAND - yap) / g)
        for i in range(600):
            y = ARM_Y - 3 + i * (4.5 * M_ + 6 - ARM_Y) / 600
            if y < yap:
                continue
            x = 7.5 + vx * (tb - math.sqrt(2 * (y - yap) / g))
            ah = r * 1.15
            for tx, ty in TIPS:
                dy = abs(ty - y)
                if dy >= ah:
                    continue
                worst = min(worst, abs(tx - x) / (r * math.sqrt(1 - (dy / ah) ** 2)))
        return worst

    def arc_clear(x0, y0, vx, up, T, skip):
        least = 1e9
        for i in range(1, 400):
            s = T * i / 400
            x, y = x0 - vx * s, y0 - up * s + 0.5 * g * s * s
            if abs(x - skip) < r * 1.05:
                continue
            least = min(least, R(x) - y)
        return least

    out = []
    for xa in [9.8 + 0.2 * i for i in range(14)]:
        for yap in [-5 - 0.5 * i for i in range(14)]:
            up_l = math.sqrt(2 * g * (ARM_REST - yap))
            t_up = up_l / g
            vx_l = (xa - 7.5) / (t_up + math.sqrt(2 * (BAND - yap) / g))
            sq = squeeze(vx_l, yap)
            if sq < a.squeeze:
                continue
            t_mid = t_up + math.sqrt(2 * (7.5 - yap) / g)
            vin = up_l / e
            apex_in = ARM_REST - vin * vin / (2 * g)
            for x1 in [i * 0.05 for i in range(int(19 / 0.05), int(107 / 0.05))]:
                y1 = R(x1)
                if y1 > 5 or abs(R(x1 + 0.15) - R(x1 - 0.15)) / 0.3 > 0.3:
                    continue
                u1 = math.sqrt(2 * g * (y1 - apex_in))
                ta = u1 / g + vin / g
                vx1 = (x1 - xa) / ta
                c = arc_clear(x1, y1, vx1, u1, ta, x1)
                if c < a.clear:
                    continue
                vyT = u1 / e
                out.append(dict(xa=round(xa, 2), yap=yap, x1=round(x1, 2), y1=round(y1, 3), up1=round(u1, 2), vx1=round(vx1, 1),
                                vx_l=round(vx_l, 2), up_l=round(up_l, 2), ex_arm=round(vx_l / vx1, 3), sq=round(sq, 3),
                                apex_in=round(apex_in, 2), apexT=round(y1 - vyT * vyT / (2 * g), 2), vyT=round(vyT, 2),
                                t_arc1=round(ta, 3), t_last=round(t_mid, 3), clear=round(c, 2)))
    json.dump(out, open(a.out, 'w'))
    print(len(out), 'candidates, gravity', round(g, 1), 'units/s2, written to', a.out)
    # shown first: the roomiest squeeze among those whose first arc passes over the letters (clear under 1e9)
    for c in sorted(out, key=lambda c: (c['clear'] >= 1e8, -c['sq'], -c['clear']))[:a.show]:
        print(json.dumps(c))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
