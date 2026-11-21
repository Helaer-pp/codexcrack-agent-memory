// Included in the CrackV4 backend so legacy handle ownership, result serialization,
// validation and exported entry points stay identical across DLL builds.
Result Detector::run512(const cv::Mat& image,const std::array<P,2>* measured,bool baselineFrame) {
    auto start=Clock::now();
    if(image.size()!=reference.size())throw std::runtime_error("Image size differs from reference");
    Result r;
    r.frame_index=frame_index+(baselineFrame?0:1);
    r.policy=policy;
    r.reference_state=reference_state;
    r.reference_reason=reference_reason;
    motion(image,measured,baselineFrame,r.response,r.patches);
    v510::Pair cp=measured?*measured:v510::Pair{current(anchors[0]),current(anchors[1])};
    if(cp[1].y<=cp[0].y)throw std::runtime_error("V5.12 requires upper P1 and lower P2");
    cv::Rect box=v510::sceneBounds(image.size(),cp);
    if(box.width<20||box.height<20)throw std::runtime_error("Empty acquisition area");
    cv::Mat mapped=v510::registerFrame(reference,image,anchors,cp,box);
    const auto upstream=box;
    v510::Pair rp=anchors;
    if(materialPolicy)v512::material(*materialPolicy,reference,image,upstream,rp,cp,box);
    auto found=v512::detect512(image(box),reference(box),mapped(cv::Rect(box.tl()-upstream.tl(),box.size())),
                              v510::midpoint(cp)-P(box.tl()),v510::midpoint(rp)-P(box.tl()));
    r.rotation=rotation;r.shift=translation;
    r.initial=baseline_length;
    r.basis="v5_12_full";r.method="notch_dp";r.stop=r.raw_stop=r.terminal_reason=found.notch?"no_tip":"no_notch";
    r.tip_measure_reason=r.stop;
    if(!found.path.empty()){
        for(auto p:found.path)r.path.emplace_back(p+box.tl());
        r.observed.assign(r.path.begin(),r.path.end()-found.bridge);
        r.has=r.tip=r.root=r.length=r.terminal=r.path_valid=r.legacy_tip=r.shadow_tip=true;
        r.first=r.rootxy=r.path.front();r.tipxy=r.endpoint=r.path.back();
        auto toRef=[&](P p){P q=p-translation;return P(rotation(0,0)*q.x+rotation(1,0)*q.y,rotation(0,1)*q.x+rotation(1,1)*q.y);};
        r.tipref=toRef(r.tipxy);r.rootref=toRef(r.rootxy);
        r.total=arc(r.path);r.visible=arc(r.observed);r.bridge=r.total-r.visible;
        r.gaps=found.bridge?1:0;
        r.stop=r.raw_stop=r.terminal_reason=r.tip_measure_reason="accepted_peak";
        r.status="main_segment_detected";r.hits=r.endpoint_hits=1;
        has_last_confirmed=true;last_confirmed_original=r.tipxy;last_confirmed_frame=r.frame_index;
    }
    if(!baselineFrame)frame_index=r.frame_index;
    r.detector_ms=elapsed(start);
    return r;
}
