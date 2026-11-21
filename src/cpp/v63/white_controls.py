"""Replay V6.3's sealed white-primer controls through the shipping DLL."""
import ctypes as C
import json
import numpy as np
from .verify import OUT, b, library, Config, Result, pair, image, write_csv
from .package import SDK

def main():
    import os
    os.environ.pop('CRACKV4_V512_MATERIAL_POLICY', None)
    dll = library(SDK)
    anchors = pair([(70, 5), (70, 155)])
    yy, xx = np.indices((160, 310))
    notch = (xx <= 70) & (abs(yy - 80) <= 8 + .28 * (70 - xx))
    rows = []
    for case in b.read_csv(b.OUT / 'primer_controls.csv'):
        k = int(case['length'])
        mask = (xx > 70) & (xx <= 70 + k)
        ref = np.where(notch, float(case['fixture_gray']), 255.)
        cur = ref.copy()
        if case['mode'] != 'unchanged':
            cur -= mask * 125 * np.exp(-.5 * ((yy - 80) / .85) ** 2)
        if case['mode'] == 'displaced_line':
            ref -= mask * 125 * np.exp(-.5 * ((yy - 83) / .85) ** 2)
        raw, fixed = cur.astype('uint8'), ref.astype('uint8')
        cfg = Config()
        dll.GrayDetectionV2DefaultConfig(C.byref(cfg))
        cfg.mode = 0
        handle = C.c_void_p()
        msg = C.create_string_buffer(512)
        assert dll.GrayDetectionV2Create(C.byref(image(fixed)), anchors, C.byref(cfg),
                                 C.byref(handle), None, msg, len(msg)) == 0, msg.value
        try:
            out = Result(size=C.sizeof(Result))
            assert dll.GrayDetectionV2Process(handle, C.byref(image(raw)), anchors, C.byref(out)) == 0
            tip = [out.tip.x, out.tip.y] if out.tip_ok else None
            expect = json.loads(case['tip']) if case['tip'] else None
            rows.append(dict(fixture_gray=case['fixture_gray'], length=k, mode=case['mode'],
                             tip=tip, expected=expect, equal=tip == expect))
        finally:
            dll.GrayDetectionV2Destroy(handle)
    write_csv(OUT / 'white_controls.csv', rows)
    print(len(rows), sum(r['equal'] for r in rows))

if __name__ == '__main__':
    main()
