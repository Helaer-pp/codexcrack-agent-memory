"""One global, image-coordinate protocol. No dataset-specific values."""
import copy,hashlib,json
CONFIG=dict(version='UCTIP-60Q-r01',normal_offsets=[2,4,7],orientation_sigma=1.,linearity_min=1.5,noise_factor=2.2,weak_min=3.,weak_max=14.,material_min=75.,
    safe_y_margin=.35,safe_left_margin=.6,origin_extent=.65,notch_black=65,notch_min_width=8,
    max_roi_pixels=3500000,max_skeleton_pixels=250000,max_segments=120000,ref_tile=96,ref_halfheight=16,
    ref_search=5,ref_std=2.,ref_ncc=.78,ref_bias_max=22.,ref_material_fraction=.65,ref_max_windows=400,
    short_gap=5,gap_scale=.065,gap_min=8,gap_max=24,max_turn_degrees=105.,long_gap_turn=30.,
    min_segment_pixels=2,min_component_pixels=9,component_linearity=2.5,min_path_observed=9,weak_tail_pixels=3,root_soft_scale=.3,strong_factor=1.3,
    max_graph_pairs=4000000,max_edges=250000,max_roots=512,max_route_states=60000,max_candidates=4096,
    max_tracks=128,track_lost_ttl=8,track_match_scale=.45,main_hysteresis=.15,
    roi_step=224,roi_initial_steps=2,roi_initial_halfwidth=.25,roi_max_expansions=48,roi_scout_min_pixels=7,
    max_rechecks=128,jump_scale=.35,tip_context=8,tip_material_fraction=.5,
    surface_cols=110,surface_rows=60,signed_display=40.,random_seed=6013)
ARMS={'FULL':[], 'NO_FIXED':['fixed'], 'NO_PREV':['prev'], 'NO_TRACKING':['tracking'], 'NO_GAP':['gap'],
      'NO_DYNAMIC_ROI':['dynamic_roi'], 'NO_MULTITRACK':['multitrack'], 'NO_OPENING':['opening'],
      'NO_BOTH_REF':['fixed','prev'], 'NO_TRACK_MULTI':['tracking','multitrack'], 'NO_GAP_ROI':['gap','dynamic_roi']}
def validate(c):
    if not isinstance(c,dict) or set(c)!=set(CONFIG):raise ValueError('Unknown or missing global config fields')
    for k,v in c.items():
        if isinstance(v,(int,float)) and (not 0<=v<1e10):raise ValueError('Invalid global bound '+k)
    if not c['normal_offsets'] or min(c['normal_offsets'])<1:raise ValueError('Invalid scales')
def digest(c):return hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest()
