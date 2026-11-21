"""Shared native-image preparation and rendering for versioned research runners."""
from dataclasses import dataclass
from types import ModuleType
import numpy as np
from research.unified_crack_tip_60q.features import CONFIG, scene_geometry

@dataclass(frozen=True)
class CrackTipRelease:
    version: str
    stage: str
    batch: ModuleType
    domain: ModuleType
    views: ModuleType

    @property
    def default_scale(self):
        return self.batch.SCALE

    def analyze(self, image, reference, current_points, reference_points, *, scale, roi, bright):
        scene = scene_geometry(image, current_points, reference, reference_points, None, CONFIG)
        box = scene["bounds"]
        cp, rp = current_points, reference_points
        if bright:
            x, y, right, bottom = box
            geometry = self.batch.geometry(image[y:bottom, x:right], [x, y], reference,
                                      dict(current_points=cp, fixed_points=rp), bright)
            if geometry is None:
                raise ValueError("当前图和参考图没有可用的共同亮区基准点")
            cp, rp = np.asarray(geometry["cur_points"]), np.asarray(geometry["ref_points"])
            box = geometry["box"]
        if roi is not None:
            x, y, right, bottom = roi
            if bright:
                x, y = max(x, box[0]), max(y, box[1])
                right, bottom = min(right, box[2]), min(bottom, box[3])
            if right-x < 20 or bottom-y < 20:
                raise ValueError("所给 ROI 没有足够的有效材料区域")
            box = [x, y, right, bottom]
        x, y, right, bottom = box
        origin = np.array([x, y])
        raw = image[y:bottom, x:right]
        fixed = reference[y:bottom, x:right]
        prep = self.batch.terminal.prepare(raw, cp.mean(0)-origin, scale, self.stage, fixed, rp.mean(0)-origin)
        mapping = self.domain.ReferenceMap(image, reference, cp, rp, box, prep, self.stage)
        model, _ = self.batch.run_mode(raw, fixed, cp, rp, origin, self.stage, "full", aligned=mapping, prepared=prep)
        return self.batch.old.clean(model), box, cp, rp, mapping


    def render(self, result, image, reference, source_sha, reference_file, reference_sha, frame, total, title):
        model, box, cp, rp, mapping = result
        x, y, right, bottom = box
        tile = self.domain.replay(reference, cp, rp, mapping.bounds, mapping.info) if mapping.bounds else None
        aligned = self.domain.embed(tile, mapping.bounds, box)
        meta = dict(input=dict(reference=str(reference_file), ref_sha=reference_sha, image_sha=source_sha,
                               height=image.shape[0], width=image.shape[1]),
                    current_points=cp, fixed_points=rp,
                    evidence=dict(scene=dict(center=cp.mean(0)), reference_info=dict(fixed=mapping.info)))
        rec = dict(frame=frame, group="custom", title=title, total=total, version=self.version, stage=self.stage,
                   box=box, placement="original", models={self.stage: {"full": model}})
        return self.views.build_card(rec, meta, image[y:bottom, x:right], reference, aligned, None, None)
