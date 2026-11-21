"""Uncluttered display derivatives; original scientific layers are retained."""
from PIL import Image, ImageDraw
from .common import np, cv2, put, get, sha


def clean_card(folder, row, result):
    seal = folder / 'clean_presentation.json'
    if seal.exists():
        return get(seal)
    raw = Image.open(folder / 'raw.png').convert('L')
    width, height = raw.size
    xa, ya, _, _ = result['scene']['bounds']
    off = np.array([xa, ya])
    marker = np.zeros((height, width, 4), np.uint8)
    if result['tip']:
        xy = tuple(np.rint(np.array(result['tip']) - off).astype(int))
        cv2.drawMarker(marker, xy, (255, 255, 255, 255), cv2.MARKER_CROSS, 20, 2)
    Image.fromarray(marker).save(folder / 'official.png')
    overlay = Image.alpha_composite(raw.convert('RGBA'), Image.open(folder / 'verified.png').convert('RGBA'))
    overlay = Image.alpha_composite(overlay, Image.fromarray(marker)).convert('RGB')
    center = np.array(result['tip'] or result['preferred_uncertain_tip'] or result['scene']['root'] or result['scene']['center']) - off
    lx = max(0, min(width - 1, int(center[0]) - 400))
    ly = max(0, min(height - 1, int(center[1]) - 180))
    rx, by = min(width, lx + 800), min(height, ly + 360)
    lx, ly = max(0, rx - 800), max(0, by - 360)
    crop = (lx, ly, rx, by)
    local = overlay.crop(crop)
    local.save(folder / 'local_result_clean.png')
    card = Image.new('RGB', (1800, 800), (17, 24, 39))
    draw = ImageDraw.Draw(card)
    draw.text((20, 16), f"{row['group']} frame {row['frame_id']} | {result['status']} | official tip={result['tip']}", fill='white')
    draw.text((20, 40), 'RAW ROI (resized display; full pixels retained separately)', fill='white')
    draw.text((920, 40), 'Current verified segments / official endpoint (NO GT)', fill='white')
    for x, im in [(20, raw.convert('RGB')), (920, overlay.copy())]:
        im.thumbnail((860, 210)); card.paste(im, (x, 70))
    context = 'OFFICIAL TIP' if result['tip'] else 'UNCERTAIN CANDIDATE / ORIGIN; NO OFFICIAL TIP'
    draw.text((20, 310), f'LOCAL RAW | {context} | {[lx+xa, ly+ya, rx+xa, by+ya]}', fill='white')
    draw.text((920, 310), 'LOCAL RESULT | same original-coordinate crop', fill='white')
    for x, im in [(20, raw.crop(crop).convert('RGB')), (920, local.copy())]:
        im.thumbnail((860, 420)); card.paste(im, (x, 340))
    draw.text((20, 770), 'Green: algorithm-verified observed segments | White cross: official tip | Track IDs and inferred gaps: interactive layers', fill='white')
    card.save(folder / 'comparison_clean.jpg', quality=90)
    record = dict(version=1, gt_used=False, native_predictions_changed=False,
                  files={name: sha(folder/name) for name in ['official.png', 'local_result_clean.png', 'comparison_clean.jpg']})
    put(seal, record)
    return record
