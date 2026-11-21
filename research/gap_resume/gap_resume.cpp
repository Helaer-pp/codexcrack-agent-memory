// Builds in a separate target so the frozen source and ABI stay byte-identical.
#include "../../baseline/frozen_a/src/CrackV4.cpp"
namespace {
struct Section {
    Path pts;
    std::vector<double> scores;
};

int qualifiedRestart(const Path &ridgePath, const std::vector<double> &scores,
                     const Tile &tile, int half, int start, const Config &cfg) {
    // Look across a bounded gap only. Require directional agreement and a
    // sustained, narrow ridge; four scattered responses do not establish a path.
    constexpr int window = 16;
    for (int k=start; k+window<=int(scores.size()) && k-start<=3*cfg.maxgap; ++k) {
        if (scores[k]<=cfg.score) continue;
        P delta=ridgePath[k]-P(0,half);
        if (std::abs(delta.y)>4+.6*delta.x) continue;
        int supported=0, competing=0;
        for (int i=k;i<k+window;++i) {
            supported+=scores[i]>cfg.score;
            // A similarly strong parallel ridge, or a wide dark patch, makes
            // ownership ambiguous in the disconnected section.
            int x=int(ridgePath[i].x), y=rnd(ridgePath[i].y);
            double other=0;
            for (int yy=0;yy<tile.score.rows;++yy)
                if (std::abs(yy-y)>=5) other=std::max(other,double(tile.score.at<float>(yy,x)));
            competing+=other>std::max(cfg.score, .7*scores[i]);
        }
        P tangent=unit(ridgePath[k+window-1]-ridgePath[k]);
        if (supported>=14 && competing<=4 && tangent.x>.7 &&
            med(std::vector<double>(scores.begin()+k,scores.begin()+k+window))>=4)
            return k;
    }
    return -1;
}

std::string resume(Detector &d, const cv::Mat &im, std::vector<Section> &sections) {
    const Result &base=d.last;
    if (base.tip || base.stop!="gap_unresolved" || base.observed.size()<2 ||
        d.absolute || d.registration_ambiguous || base.texture_erased)
        return "not_eligible";
    auto toRef=[&](P p) { return d.rotation.t()*(p-d.translation); };
    P o=toRef(base.observed.back());
    P dir=unit(o-toRef(base.observed[base.observed.size()-std::min<size_t>(14,base.observed.size())]));
    const int half=std::max(20,std::min(40,rnd(.18*d.spacing)));
    const int limit=int(std::ceil(2*std::hypot(im.cols,im.rows)/d.cfg.advance));
    for (int step=0;step<limit;++step) {
        if (dot(dir,d.forward)<0) return "backward";
        Tile tile=d.tile(im,o,dir,0,d.cfg.tile,half);
        cv::Mat capped;
        cv::min(tile.score,15,capped);
        auto dp=ridge(capped,half,d.cfg.score);
        const Path &p=dp.first;
        std::vector<double> scores;
        for (P q:p) scores.push_back(mapcoord(tile.score,q.y,q.x));
        auto good=[&](int i) {return scores[i]>d.cfg.score;};
        int n=int(scores.size()),first=1;
        if (sections.empty()) {
            first=qualifiedRestart(p,scores,tile,half,1,d.cfg);
            if (first<0) return "no_unique_restart";
            // If recomputation starts directly on evidence after smoothing the
            // old endpoint, the original stop still establishes missing support.
            sections.emplace_back();
        }
        int last=first-1,missing=0;
        for (int i=first;i<n;++i) {
            if (good(i)) {last=i; missing=0;}
            else if (++missing>d.cfg.maxgap) break;
        }
        int take=std::min(last,d.cfg.advance);
        const P normal(-dir.y,dir.x);
        auto point=[&](int i) {return o+dir*p[i].x+normal*(p[i].y-half);};
        auto &seg=sections.back();
        for (int k=first;k<=take;++k) {
            seg.pts.push_back(point(k));
            seg.scores.push_back(scores[k]);
        }
        if (seg.pts.size()<2) return "short_restart";
        const P end=seg.pts.back();
        const P tangent=unit(end-seg.pts[seg.pts.size()-std::min<size_t>(14,seg.pts.size())]);
        if (take>=d.cfg.advance) {o=end;dir=tangent;continue;}
        // A second long break with renewed evidence must either start a
        // separate supported section or invalidate this tip attempt.
        int beyond=std::max(first,last+1);
        if (std::count_if(scores.begin()+std::min(beyond,n),scores.end(),
                          [&](double x){return x>d.cfg.score;})>=4) {
            int k=qualifiedRestart(p,scores,tile,half,beyond,d.cfg);
            if (k<0 || sections.size()>=3) return "unresolved_next_gap";
            Section next;
            for (int i=k;i<k+16;++i) {next.pts.push_back(point(i));next.scores.push_back(scores[i]);}
            o=next.pts.back();dir=unit(o-next.pts.front());sections.push_back(std::move(next));continue;
        }
        if (take>1) {o=end;dir=tangent;continue;} // Probe again facing the terminal segment.
        if (seg.pts.size()<16) return "short_terminal_section";
        Result audit;
        audit.raw_stop="evidence_ended";
        d.terminalAudit(seg.pts,seg.scores,{d.quality.width},tile,o,dir,half,d.last_anchors_supplied,false,audit);
        if (!audit.shadow_tip || audit.texture_erased)
            return audit.terminal_reason=="terminal_supported"?"terminal_strength":audit.terminal_reason;
        return "recovered";
    }
    return "step_limit";
}
} // namespace

// Call immediately after processing this very image on this handle. JSON is
// thread-local, valid until the next call on the same thread. A paths/validity
// stay accessible through the original APIs. No restart feeds temporal history.
extern "C" __declspec(dllexport) const char *CrackGapResume(CrackV4Handle h,
                                                const CrackV4Image *image, uint64_t frame) {
    thread_local std::string json;
    try {
        if (!h) throw std::runtime_error("null detector");
        auto &d=*static_cast<Detector*>(h);
        std::lock_guard<std::mutex> lock(d.mutex);
        cv::Mat im=view(image);
        if (frame!=d.last.frame_index || im.cols!=d.curwidth || im.rows!=d.curheight)
            throw std::runtime_error("frame mismatch");
        std::vector<Section> sections;
        std::string reason=resume(d,im,sections);
        std::ostringstream s; s.precision(17);
        s<<"{\"reason\":"<<escaped(reason)<<",\"tip_px\":";
        auto point=[&](P q){P p=d.current(q);s<<'['<<p.x<<','<<p.y<<']';};
        if (reason=="recovered") point(sections.back().pts.back()); else s<<"null";
        s<<",\"complete_length_px\":null,\"segments\":[";
        if (reason=="recovered") for (size_t j=0;j<sections.size();++j) {
            if(j) s<<','; s<<'[';
            for(size_t i=0;i<sections[j].pts.size();++i) {if(i)s<<',';point(sections[j].pts[i]);}
            s<<']';
        }
        s<<"]}";json=s.str();
    } catch(const std::exception &e) {json="{\"error\":"+escaped(e.what())+"}";}
    return json.c_str();
}
