"""Export clean glyph/shape outlines for the Strata engine.
Font space: cap height = 72 units, baseline y=0, y grows downward."""
import json, math
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity

FONT = TTFont('/usr/share/fonts/opentype/inter/InterDisplay-Black.otf')
GS = FONT.getGlyphSet(); CMAP = FONT.getBestCmap(); HMTX = FONT['hmtx']
CAP = FONT['OS/2'].sCapHeight
K = 72 / CAP

class FlatPen(BasePen):
    def __init__(s, gs): super().__init__(gs); s.contours = []; s.cur = []
    def _moveTo(s, p): s.cur = [p]
    def _lineTo(s, p): s.cur.append(p)
    def _curveToOne(s, p1, p2, p3):
        p0 = s.cur[-1]
        for i in range(1, 17):
            t = i/16; u = 1-t
            s.cur.append((u**3*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t**3*p3[0], u**3*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t**3*p3[1]))
    def _closePath(s):
        if len(s.cur) > 2: s.contours.append(s.cur)
        s.cur = []
    _endPath = _closePath

def signed_area(c):
    return sum(c[i][0]*c[(i+1) % len(c)][1]-c[(i+1) % len(c)][0]*c[i][1] for i in range(len(c)))/2

def glyph(ch):
    name = CMAP[ord(ch)]
    pen = FlatPen(GS); GS[name].draw(pen)
    # non-zero winding: outer contours one direction, holes the other
    if not pen.contours: return Polygon(), HMTX[name][0]*K
    polys = [Polygon(c).buffer(0) for c in pen.contours]
    def depth(i):
        p = polys[i].representative_point()
        return sum(1 for j, q in enumerate(polys) if j != i and q.area > polys[i].area and q.contains(p))
    order = sorted(range(len(polys)), key=depth)
    g = Polygon()
    for i in order:
        g = g.union(polys[i]) if depth(i) % 2 == 0 else g.difference(polys[i])
    g = affinity.scale(g, K, -K, origin=(0, 0))
    return g, HMTX[name][0]*K

def star(n, r1, r2, rot=-math.pi/2):
    return Polygon([((r1 if i % 2 == 0 else r2)*math.cos(rot+i*math.pi/n), (r1 if i % 2 == 0 else r2)*math.sin(rot+i*math.pi/n)) for i in range(2*n)])

def sparkle():
    g = box(-1, -1, 1, 1)
    for cx in (-1, 1):
        for cy in (-1, 1): g = g.difference(Point(cx, cy).buffer(0.93, 128))
    return g
def cross():
    bar = box(-1, -.21, 1, .21)
    return affinity.rotate(unary_union([bar, affinity.rotate(bar, 90, origin=(0, 0))]), 45, origin=(0, 0))
def ring(): return Point(0, 0).buffer(1, 128).difference(Point(0, 0).buffer(.58, 128))
def moon(): return Point(0, 0).buffer(1, 128).difference(Point(.42, -.2).buffer(.84, 128))
def arch():
    return Point(0, .35).buffer(.85, 128).intersection(box(-1, -1, 1, .35)).union(box(-.85, .35, .85, .95)).difference(
        Point(0, .45).buffer(.4, 128).union(box(-.4, .45, .4, .96)))
def chevrons():
    c = Polygon([(-.9, -.9), (-.45, -.9), (.15, 0), (-.45, .9), (-.9, .9), (-.3, 0)])
    return unary_union([c, affinity.translate(c, .75, 0)])
def hexagon(): return Polygon([(math.cos(math.pi/6+i*math.pi/3), math.sin(math.pi/6+i*math.pi/3)) for i in range(6)])
def halfdisc(): return Point(0, .5).buffer(1, 128).intersection(box(-1, -.5, 1, .5))
def quarter(): return Point(-.5, .5).buffer(1, 128).intersection(box(-.5, -.5, .5, .5))
def capsule(): return box(-.45, -.55, .45, .55).buffer(.45, 64)
def squircle():
    n = 4.2
    return Polygon([(math.copysign(abs(math.cos(t))**(2/n), math.cos(t)), math.copysign(abs(math.sin(t))**(2/n), math.sin(t))) for t in [i*2*math.pi/240 for i in range(240)]])
def flower():
    return unary_union([Point(.5*math.cos(a), .5*math.sin(a)).buffer(.5, 96) for a in [i*math.pi/2 for i in range(4)]] + [Point(0, 0).buffer(.5, 96)])
def drop():
    c = Point(0, .35).buffer(.62, 128)
    tip = Polygon([(0, -1), (.54, .05), (-.54, .05)])
    return unary_union([c, tip]).buffer(.04).buffer(-.04)
def bolt(): return Polygon([(.15, -1), (-.62, .12), (-.05, .12), (-.2, 1), (.62, -.18), (.05, -.18), (.28, -1)])
def waves():
    pts_top = [(x/40-1, -.55+.18*math.sin((x/40-1)*math.pi*2)) for x in range(81)]
    bands = []
    for k in range(3):
        top = [(x, y+k*.55) for x, y in pts_top]
        bot = [(x, y+.3) for x, y in reversed(top)]
        bands.append(Polygon(top+bot))
    return unary_union(bands)
def plus_heavy(): return unary_union([box(-1, -.3, 1, .3), box(-.3, -1, .3, 1)])
def target(): return unary_union([ring(), Point(0, 0).buffer(.3, 96)])
def eye():
    lens = Point(0, .9).buffer(1.35, 128).intersection(Point(0, -.9).buffer(1.35, 128))
    return lens.difference(Point(0, 0).buffer(.36, 96))
def slash_circle(): return Point(0, 0).buffer(1, 128).difference(affinity.rotate(box(-1.2, -.12, 1.2, .12), -45, origin=(0, 0)))
def grid4(): return unary_union([box(x, y, x+.85, y+.85) for x in (-1, .15) for y in (-1, .15)])
def blob():
    return Polygon([((1+.18*math.sin(3*t)+.08*math.cos(5*t))*math.cos(t)*.85, (1+.18*math.sin(3*t)+.08*math.cos(5*t))*math.sin(t)*.85) for t in [i*2*math.pi/240 for i in range(240)]])

CUSTOM = dict(sparkle=sparkle, burst=lambda: star(12, 1, .62), **{'star-8': lambda: star(8, 1, .45)}, cross=cross, ring=ring,
              moon=moon, arch=arch, chevrons=chevrons, hexagon=hexagon, **{'half-disc': halfdisc, 'quarter': quarter},
              capsule=capsule, squircle=squircle, flower=flower, drop=drop, bolt=bolt, waves=waves, **{'plus-bold': plus_heavy},
              target=target, eye=eye, **{'no-entry': slash_circle}, grid=grid4, blob=blob)

SET = [
 ('Symbols', [('&','ampersand'),('@','at'),('#','hash'),('%','percent'),('‰','per-mille'),('*','asterisk'),('⁂','asterism'),('※','reference'),('§','section'),('¶','pilcrow'),('?','question'),('!','exclamation'),('¿','inverted-question'),('¡','inverted-exclamation'),('/','slash'),('\\','backslash'),('|','bar'),('~','tilde'),('¬','not'),('…','ellipsis'),('•','bullet'),('“','quote-open'),('”','quote-close'),('«','guillemet-left'),('»','guillemet-right')]),
 ('Arrows', [('→','arrow-right'),('←','arrow-left'),('↑','arrow-up'),('↓','arrow-down'),('↗','arrow-up-right'),('↘','arrow-down-right'),('↙','arrow-down-left'),('↖','arrow-up-left'),('↔','arrow-both'),('↺','rotate-left'),('↻','rotate-right'),('↵','return'),('⇧','shift'),('▶','play'),('◀','play-back'),('▼','caret-down'),('chevrons','chevrons')]),
 ('Shapes', [('●','circle'),('ring','ring'),('target','target'),('■','square'),('squircle','squircle'),('grid','grid'),('▲','triangle'),('◆','diamond'),('hexagon','hexagon'),('half-disc','half-disc'),('quarter','quarter'),('capsule','capsule'),('arch','arch'),('★','star'),('star-8','star-8'),('sparkle','sparkle'),('burst','burst'),('♥','heart'),('flower','flower'),('drop','drop'),('blob','blob'),('moon','moon'),('☀','sun'),('bolt','bolt'),('waves','waves'),('eye','eye')]),
 ('Math', [('+','plus'),('plus-bold','plus-bold'),('−','minus'),('×','multiply'),('÷','divide'),('=','equals'),('≠','not-equal'),('≈','approx'),('±','plus-minus'),('≤','less-equal'),('≥','greater-equal'),('<','less-than'),('>','greater-than'),('∞','infinity'),('√','root'),('∫','integral'),('π','pi'),('∑','sigma'),('Δ','delta'),('Ω','omega'),('µ','micro'),('∅','empty-set'),('°','degree'),('⊕','circle-plus'),('⊗','circle-times')]),
 ('Currency', [('$','dollar'),('£','pound'),('€','euro'),('¥','yen'),('¢','cent'),('₿','bitcoin'),('₹','rupee'),('₽','ruble'),('₩','won'),('₺','lira'),('₴','hryvnia'),('₱','peso')]),
 ('Marks', [('©','copyright'),('®','registered'),('™','trademark'),('✓','check'),('✗','ballot-x'),('cross','cross'),('no-entry','no-entry'),('⌘','command'),('⌥','option'),('⏎','enter')]),
 ('Brackets', [('(','paren-left'),(')','paren-right'),('[','bracket-left'),(']','bracket-right'),('{','brace-left'),('}','brace-right')]),
 ('Numbers', [(c, 'num-'+c) for c in '0123456789']),
 ('Uppercase', [(c, 'upper-'+c.lower()) for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']),
 ('Lowercase', [(c, 'lower-'+c) for c in 'abcdefghijklmnopqrstuvwxyz']),
]
# extra glyphs only for the type tester
EXTRA = list(" .,:;'\"-_()&!?/+=#@$£€%*")

def rings_of(g, simp=0.06):
    g = g.simplify(simp, preserve_topology=True)
    out = []
    for p in ([g] if g.geom_type == 'Polygon' else list(g.geoms)):
        if p.geom_type != 'Polygon' or p.area < 0.5: continue
        for r in [p.exterior, *p.interiors]:
            c = list(r.coords)[:-1]
            out.append([v for x, y in c for v in (round(x, 1), round(y, 1))])
    return out

syms = []
glyphs = {}
for cat, items in SET:
    for ch, name in items:
        if ch in CUSTOM:
            g = CUSTOM[ch](); b = g.bounds; s = 70/max(b[2]-b[0], b[3]-b[1])
            g = affinity.scale(g, s, s, origin=(0, 0)); b = g.bounds
            g = affinity.translate(g, -(b[0]+b[2])/2, -(b[1]+b[3])/2)
            syms.append({'n': name, 'c': cat, 'ch': '', 'r': rings_of(g)})
        else:
            g, adv = glyph(ch)
            syms.append({'n': name, 'c': cat, 'ch': ch, 'r': rings_of(g) if not g.is_empty else []})
            glyphs[ch] = {'a': round(adv, 1), 'r': syms[-1]['r']}
for ch in EXTRA:
    if ch in glyphs or ord(ch) not in CMAP: continue
    g, adv = glyph(ch)
    glyphs[ch] = {'a': round(adv, 1), 'r': rings_of(g) if not g.is_empty else []}
# point glyph entries for symbols at the shared glyph table to save bytes
for s in syms:
    if s['ch']: del s['r']
out = {'syms': syms, 'glyphs': glyphs}
json.dump(out, open('strata.json', 'w'), separators=(',', ':'), ensure_ascii=False)
print(len(syms), 'symbols,', len(glyphs), 'glyphs,', len(json.dumps(out, separators=(',', ':'), ensure_ascii=False).encode())//1024, 'KB')
