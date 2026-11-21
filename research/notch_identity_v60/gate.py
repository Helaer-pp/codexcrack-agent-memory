"""Frozen S3 admission. A labeled joint loss on either placement vetoes S3."""
def select(fp, bridges, before, after, p6_before, p6_after):
    losses=sorted(before-after)
    improved=sum(p6_after)>sum(p6_before) and all(b>=a for a,b in zip(p6_before,p6_after))
    admitted=not losses and fp==0 and bridges==36 and improved
    return dict(stage='S3' if admitted else 'S2',admitted=admitted,
                lost_joints=losses,p6_net_gain=improved,fp=fp,weak_material_bridge=bridges)
