// Read-only access to the V1 path when its final gate abstains.
#include "../gap_resume/gap_resume.cpp"
extern "C" __declspec(dllexport) const char *CrackGateProbe(
        CrackV4Handle h, const CrackV4Image *im, uint64_t frame) {
    thread_local std::string json;
    try {
        if (!h) throw std::runtime_error("null handle");
        auto &d=*static_cast<Detector*>(h);
        std::lock_guard<std::mutex> lock(d.mutex);
        cv::Mat image=view(im);
        if (frame!=d.last.frame_index || image.size()!=cv::Size(d.curwidth,d.curheight))
            throw std::runtime_error("frame mismatch");
        std::vector<Section> sections;
        std::string reason=resume(d,image,sections);
        std::ostringstream s;
        s.precision(17);
        s<<"{\"reason\":"<<escaped(reason)<<",\"segments\":[";
        for (size_t j=0;j<sections.size();++j) {
            if(j)s<<',';s<<'[';
            for(size_t k=0;k<sections[j].pts.size();++k) {
                if(k)s<<',';
                P p=d.current(sections[j].pts[k]);
                s<<'['<<p.x<<','<<p.y<<']';
            }
            s<<']';
        }
        s<<"]}";json=s.str();
    } catch(const std::exception &e) {json="{\"error\":"+escaped(e.what())+"}";}
    return json.c_str();
}
