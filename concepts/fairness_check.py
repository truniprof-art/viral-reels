import sys, collections, random
sys.path.insert(0, '.')
import country_race as c
N = int(sys.argv[1]); S0 = int(sys.argv[2]) if len(sys.argv) > 2 else 1
team = collections.Counter(); slot = collections.Counter(); nf = []; t1 = []; lead8 = 0
for s in range(S0, S0 + N):
    fr, fin, o, _, _ = c.simulate(s); nf.append(len(fin))
    rnd = random.Random(s)
    w = o[0] if fin else max(range(len(c.TEAMS)), key=lambda k: fr[-1]['p'][k])
    team[c.TEAMS[w]] += 1; slot[c.SLOTS[w]] += 1; t1.append(round(fin[w]) if w in fin else 99)
    lead8 += max(range(len(c.TEAMS)), key=lambda k: fr[8 * 30]['p'][k]) == w
print('teams', dict(sorted(team.items())), 'slots', dict(sorted(slot.items())), 'lead@8 wins', lead8, '/', N, 'all-finish', sum(x == len(c.TEAMS) for x in nf), 't1', sorted(t1)[::3])
