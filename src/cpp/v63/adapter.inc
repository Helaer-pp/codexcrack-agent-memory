// Included in the CrackV4 backend so legacy handle ownership, result serialization,
// validation and exported entry points stay identical across DLL builds.
Result Detector::run512(const cv::Mat &image, const std::array<P, 2> *measured, bool baselineFrame) {
    auto start = Clock::now();
    if (image.size() != reference.size())
        throw std::runtime_error("Image size differs from reference");
    Result r;
    r.frame_index = frame_index + (baselineFrame ? 0 : 1);
    r.policy = policy;
    r.reference_state = reference_state;
    r.reference_reason = reference_reason;
    motion(image, measured, baselineFrame, r.response, r.patches);
    v510::Pair cp = measured ? *measured : v510::Pair{current(anchors[0]), current(anchors[1])};
    if (cp[1].y <= cp[0].y)
        throw std::runtime_error("V6.3 requires upper P1 and lower P2");
    cv::Rect box = v510::sceneBounds(image.size(), cp);
    if (box.width < 20 || box.height < 20)
        throw std::runtime_error("Empty acquisition area");

    const auto upstream = box;
    v510::Pair rp = anchors;
    if (materialPolicy)
        v512::material(*materialPolicy, reference, image, upstream, rp, cp, box);
    auto found = v63::detect(image, reference, box, cp, rp);
    r.rotation = rotation;
    r.shift = translation;
    r.initial = baseline_length;
    r.basis = "v6_3_s2";
    r.method = "notch_dp";
    r.stop = r.raw_stop = r.terminal_reason = found.notch ? "no_tip" : "no_notch";
    r.tip_measure_reason = r.stop;
    if (!found.path.empty()) {
        r.path = std::move(found.path);
        r.observed = r.path;
        r.has = r.tip = r.root = r.length = r.terminal = r.path_valid = r.legacy_tip = r.shadow_tip = true;
        r.first = r.rootxy = r.path.front();
        r.tipxy = r.endpoint = r.path.back();
        r.tipref = found.mapping.referencePoint(r.tipxy);
        r.rootref = found.mapping.referencePoint(r.rootxy);
        r.total = arc(r.path);
        r.visible = arc(r.observed);
        r.bridge = r.total - r.visible;
        r.gaps = 0;
        r.stop = r.raw_stop = r.terminal_reason = r.tip_measure_reason = "accepted_peak";
        r.status = "main_segment_detected";
        r.hits = r.endpoint_hits = 1;
        has_last_confirmed = true;
        last_confirmed_original = r.tipxy;
        last_confirmed_frame = r.frame_index;
    }
    if (!baselineFrame)
        frame_index = r.frame_index;
    r.detector_ms = elapsed(start);
    return r;
}
