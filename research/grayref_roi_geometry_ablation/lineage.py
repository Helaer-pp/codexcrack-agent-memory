"""Read-only instrumentation of frozen graph ranking; no evaluation dependencies."""
import ast,inspect
from .geometry import frozen

def routes(segs,E,g,notch):
    captured=[]
    def capture(ranked):captured.extend(ranked)
    tree=ast.parse(inspect.getsource(frozen.graph_paths));fn=tree.body[0]
    index=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.For) and isinstance(n.iter,ast.Name) and n.iter.id=='ranked')
    fn.body.insert(index,ast.parse('_capture(ranked)').body[0]);ast.fix_missing_locations(tree)
    ns=dict(vars(frozen));ns['_capture']=capture;exec(compile(tree,'<read-only-route-lineage>','exec'),ns)
    paths,edges,counts=ns['graph_paths'](segs,E,g,notch,frozen.CONFIG)
    kept=[];out=[]
    for rank,(score,k,chain,component) in enumerate(captured):
        keeper=None
        if len(kept)>=frozen.CONFIG['paths_cap']:reason='NOT_VISITED_PATH_BUDGET'
        else:
            keeper=next((p[1] for p in kept if set(chain).issubset(p[2]) or set(p[2]).issubset(chain)),None)
            if keeper is not None:reason='FRAGMENT_CONTAINMENT'
            else:reason='KEPT';kept.append((score,k,chain))
        out.append(dict(rank=rank,id=k,score=score,fragment_ids=chain,reason=reason,keeper=keeper))
    assert [r['id'] for r in paths]==[p[1] for p in kept]
    return out,edges,counts
