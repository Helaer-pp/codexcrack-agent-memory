// Indexed segments retain the unmeasured spaces between observations.
__declspec(dllexport) int CrackV4SegmentCount(CrackV4Handle h) {
    if(!h) return -1;
    auto &d=*static_cast<Detector*>(h);
    std::lock_guard<std::mutex> lock(d.mutex);
    if(!d.gate_started) return d.last.tip && !d.last.path.empty() ? 1 : 0;
    return int(d.segments.size());
}
__declspec(dllexport) int CrackV4CopySegment(CrackV4Handle h,int index,CrackV4Point *out,int cap) {
    if(!h || index<0 || cap<0) return -1;
    auto &d=*static_cast<Detector*>(h);
    std::lock_guard<std::mutex> lock(d.mutex);
    const Path *p=nullptr;
    if(!d.gate_started && index==0 && d.last.tip) p=&d.last.path;
    else if(index<int(d.segments.size())) p=&d.segments[index];
    if(!p) return -1;
    if(out) for(int i=0;i<std::min(cap,int(p->size()));++i) out[i]={(*p)[i].x,(*p)[i].y};
    return int(p->size());
}
