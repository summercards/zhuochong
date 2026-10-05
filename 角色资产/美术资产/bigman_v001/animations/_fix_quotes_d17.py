import ast

p = 'anim_getup_f.py'
KEEP_NEXT = set('),+ \t]%:}')


def cjk(ch):
    if len(ch) != 1:
        return False
    o = ord(ch)
    return 0x3000 <= o <= 0x9fff or 0xf900 <= o <= 0xfaff or 0xff00 <= o <= 0xffef


lines = open(p, encoding='utf-8').read().split('\n')
out = []
intri = False
fixed = 0
for l in lines:
    n = l.count('"""')
    if '"""' in l:
        out.append(l)
        if n % 2 == 1:
            intri = not intri
        continue
    if intri:
        out.append(l)
        continue
    if l.lstrip().startswith('#'):
        out.append(l)
        continue
    res = list(l)
    for j, ch in enumerate(l):
        if ch != '"':
            continue
        b = l[j - 1] if j > 0 else ''
        a = l[j + 1] if j + 1 < len(l) else ''
        if cjk(b) and a != '' and a not in KEEP_NEXT:
            res[j] = '\u300c' if fixed % 2 == 0 else '\u300d'
            fixed += 1
    out.append(''.join(res))

open(p, 'w', encoding='utf-8').write('\n'.join(out))
print('fixed:', fixed)

src = open(p, encoding='utf-8').read()
try:
    ast.parse(src)
    print('SYNTAX OK')
except SyntaxError as e:
    print('ERR line', e.lineno, ':', e.msg)
    print('   ', repr(e.text))
