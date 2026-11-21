// The endpoints are measured in current image pixels. The markers only place
// the search window and track its approximate displacement. Registration tiles
// are anchored to the image grid so moving a window does not resample a ridge.
int windowQuarterTurn(P direction) {
    if(std::abs(direction.x)>=std::abs(direction.y)) return direction.x>=0?0:2;
    return direction.y>=0?1:3;
}
cv::Rect tipWindow(P center,double spacing,int turn,cv::Size image) {
    int behind=std::clamp(rnd(.38*spacing),24,192);
    int ahead=std::clamp(rnd(4.5*spacing),256,1536);
    int half=std::clamp(rnd(1.4*spacing),96,384);
    int left=turn==0?behind:turn==2?ahead:half;
    int right=turn==0?ahead:turn==2?behind:half;
    int top=turn==1?behind:turn==3?ahead:half;
    int bottom=turn==1?ahead:turn==3?behind:half;
    return cv::Rect(rnd(center.x)-left,rnd(center.y)-top,left+right+1,top+bottom+1)&cv::Rect({},image);
}
void orientWindow(cv::Mat &m,int turn) {
    if(turn && !m.empty())cv::rotate(m,m,turn==1?cv::ROTATE_90_COUNTERCLOCKWISE:
                                           turn==2?cv::ROTATE_180:cv::ROTATE_90_CLOCKWISE);
}

// Estimate an integer local displacement by template matching fixed image
// tiles. Reject unmatchable patches; missing reference support is not evidence.
cv::Mat1b localReference(const cv::Mat &ref,const cv::Mat &im,cv::Rect roi,
                         cv::Point drift,cv::Mat1b &knownCrack,const cv::Mat &mask) {
    cv::Mat1b aligned(roi.size(),uchar(0));
    knownCrack=cv::Mat1b(roi.size(),uchar(0));
    const cv::Rect rb({},ref.size()),ib({},im.size());
    constexpr int side=64, search=12;
    for(int y=roi.y/side*side;y<roi.br().y;y+=side)
        for(int x=roi.x/side*side;x<roi.br().x;x+=side) {
            cv::Rect tile=cv::Rect(x,y,side,side)&ib;
            cv::Rect pattern=tile-drift;
            cv::Rect box=(pattern+cv::Size(search*2,search*2)-cv::Point(search,search))&rb;
            if(box.width<tile.width || box.height<tile.height) continue;
            std::vector<double> dx,dy;
            // The crack can dominate a whole-tile correlation. Register from
            // surrounding small material patches, accepting consistent votes.
            for(int v:{0,20,40}) for(int u:{0,20,40}) {
                cv::Rect small=cv::Rect(x+u,y+v,24,24)&tile;
                if(small.width<16 || small.height<16) continue;
                cv::Rect area=(small-drift+cv::Size(2*search,2*search)-cv::Point(search,search))&rb;
                if(area.width<small.width || area.height<small.height)continue;
                cv::Mat1f map;
                cv::matchTemplate(ref(area),im(small),map,cv::TM_CCOEFF_NORMED);
                double corr;cv::Point match;
                cv::minMaxLoc(map,nullptr,&corr,nullptr,&match);
                if(corr<.62)continue;
                cv::Point delta=area.tl()+match-small.tl();
                dx.push_back(delta.x);dy.push_back(delta.y);
            }
            if(dx.size()<2)continue;
            cv::Point offset(rnd(med(dx)),rnd(med(dy)));
            int agree=0;
            for(size_t i=0;i<dx.size();++i) agree+=std::hypot(dx[i]-offset.x,dy[i]-offset.y)<=2;
            if(agree<2)continue;
            cv::Rect patch=tile&roi;
            if((patch+offset & rb)!=(patch+offset))continue;
            ref(patch+offset).copyTo(aligned(patch-roi.tl()));
            if(!mask.empty()) mask(patch+offset).copyTo(knownCrack(patch-roi.tl()));
        }
    return aligned;
}

// Local alignment DP: a new supported line may begin in any column. Gaps and
// turns cost evidence. A peak needs a resolved dark tail and material beyond it.
Path distalLine(const cv::Mat1f &score,const cv::Mat1f &intensity,bool absolute) {
    int h=score.rows,w=score.cols;
    if(h<16 || w<20) return {};
    cv::Mat1f gains(h,w,0.f);
    cv::Mat1b gaps(h,w,uchar(0));
    cv::Mat_<signed char> back(h,w,static_cast<signed char>(2));
    for(int x=4;x<w-4;++x) for(int y=5;y<h-5;++y) {
        double best=0;
        for(int k:{0,-1,1}) {
            if(score(y,x)<3.f && gaps(y+k,x-1)>=3) continue;
            double g=gains(y+k,x-1)-(k ? .6 : 0.);
            if(g>best) {best=g;back(y,x)=static_cast<signed char>(k);}
        }
        gains(y,x)=float(std::max(0.,best+std::clamp(double(score(y,x))/3.-1.,-2.,4.)));
        if(score(y,x)<3 && back(y,x)!=2) gaps(y,x)=1+gaps(y+back(y,x),x-1);
    }
    struct Peak {float gain;int x,y;};
    std::vector<Peak> peaks;
    for(int x=4;x<w-10;++x) for(int y=5;y<h-5;++y) {
        float g=gains(y,x);
        if(g<(absolute?55:12) || score(y,x)<3.f) continue;
        if(g<gains(y-1,x) || g<gains(y+1,x) ||
           g<=std::max({gains(y-1,x+1),gains(y,x+1),gains(y+1,x+1)})) continue;
        peaks.push_back({g,x,y});
    }
    std::sort(peaks.begin(),peaks.end(),[](Peak a,Peak b){return a.gain>b.gain;});
    Path best;
    float bestGain=0;
    for(Peak peak:peaks) {
        if(!best.empty() && peak.gain<.8f*bestGain) break;
        if(!best.empty() && norm(best.back()-P(peak.x,peak.y))<4) continue;
        int x=peak.x,y=peak.y,hits=0;
        Path line;
        while(x>=4 && gains(y,x)>0) {
            line.emplace_back(x,y);
            hits+=score(y,x)>=3;
            int k=back(y,x);if(k==2)break;
            y+=k;--x;
        }
        if(line.size()<size_t(absolute?24:5) || hits<.72*line.size()) continue;
        const int tailCount=std::min(8,int(line.size()));
        int tailHits=0;
        for(int j=0;j<tailCount;++j)tailHits+=score(rnd(line[j].y),rnd(line[j].x))>=3;
        if(tailHits<.65*tailCount)continue;
        // A nearby peak on the same sampled line is an interior shoulder.
        if(!best.empty() && std::any_of(best.begin(),best.end(),[&](P p){
            return norm(p-line.front())<6;
        })) continue;
        P t=line.front()-line[std::min<size_t>(7,line.size()-1)];
        if(t.x<=0)continue;
        double slope=t.y/t.x;
        bool material=true;
        int run=0;
        for(int i=1;i<=9;++i) {
            int yy=rnd(peak.y+slope*i),xx=peak.x+i;
            if(yy<3 || yy>=h-3 || intensity(yy,xx)<55) {material=false;break;}
            run=score(yy,xx)>3.f ? run+1 : 0;
            if(i>=4 && run>=4){material=false;break;}
        }
        if(!material) continue;
        std::reverse(line.begin(),line.end());
        if(!best.empty()) {
            // Local maxima on a fading tail may be several columns apart.
            // Compare traces at their overlapping end, before declaring two
            // independent candidates. Never bridge an unseen gap here.
            int xend=int(std::min(best.back().x,line.back().x));
            int shared=0;
            for(int xx=xend-5;xx<=xend;++xx) {
                int a=xx-int(best.front().x),b=xx-int(line.front().x);
                if(a>=0 && b>=0 && std::abs(best[a].y-line[b].y)<=2)++shared;
            }
            if(shared<4)return {};
            if(line.back().x>best.back().x) best=std::move(line);
        } else {best=std::move(line);bestGain=peak.gain;}
    }
    return best;
}

void Detector::measureTip(Result &r,const cv::Mat &im,P center,P roiDirection,bool isReference) {
    // Preserve a usable chronological path if the independent endpoint search
    // has no local evidence in this frame.
    const Path processPath=r.path;
    const bool processTip=r.tip;
    const bool processLength=r.length;
    const double processTotal=r.total;
    const double processVisible=r.visible;
    const double processBridge=r.bridge;
    const bool processRoot=r.root;
    const P processRootXY=r.rootxy;
    const P processRootRef=r.rootref;
    int turn=windowQuarterTurn(roiDirection);
    tip_roi=tipWindow(center,spacing,turn,im.size());
    if(isReference && cfg.mode==0)return;
    Path path;
    if(tip_roi.width>=20 && tip_roi.height>=16) {
        cv::Mat1f current,registered,eroded,refMin,refMax;
        cv::Mat1b prior;
        im(tip_roi).convertTo(current,CV_32F);
        cv::GaussianBlur(current,current,{3,3},.8);
        if(!isReference) {
            auto aligned=localReference(reference,im,tip_roi,
                cv::Point(rnd(center.x-origin.x),rnd(center.y-origin.y)),prior,baseline_mask);
            aligned.convertTo(registered,CV_32F);
            cv::GaussianBlur(registered,registered,{3,3},.8);
            cv::erode(registered,eroded,cv::Mat::ones(3,3,CV_8U));
            cv::erode(registered,refMin,cv::Mat::ones(7,7,CV_8U));
            cv::dilate(registered,refMax,cv::Mat::ones(7,7,CV_8U));
        }
        orientWindow(current,turn);orientWindow(registered,turn);orientWindow(eroded,turn);
        orientWindow(refMin,turn);orientWindow(refMax,turn);orientWindow(prior,turn);
        cv::Mat1f score(current.size(),-3.f);
        for(int y=5;y<current.rows-5;++y) for(int x=4;x<current.cols-4;++x) {
            float flank=std::min(current(y-4,x),current(y+4,x));
            if(flank<75) continue;
            float valley=flank-current(y,x);
            if(isReference) {
                // Require a thin dark line surrounded by material on both sides.
                float upper=current(y-4,x),lower=current(y+4,x);
                if(std::abs(upper-lower)<15 && flank>105)score(y,x)=valley-12;
            } else if(eroded(y,x)>75) {
                float refRidge=std::min(registered(y-4,x),registered(y+4,x))-registered(y,x);
                float novel=std::min(eroded(y,x)-current(y,x),valley-std::max(0.f,refRidge));
                if(refMin(y,x)>85 && refMax(y,x)-refMin(y,x)<40)
                    score(y,x)=std::min(valley,novel);
                if(prior(y,x)) score(y,x)=std::max(score(y,x),valley-5.f);
            }
        }
        path=distalLine(score,current,isReference);
        for(P &p:path) {
            if(turn==1)p=P(tip_roi.width-1-p.y,p.x);
            else if(turn==2)p=P(tip_roi.width-1-p.x,tip_roi.height-1-p.y);
            else if(turn==3)p=P(p.y,tip_roi.height-1-p.x);
            p+=P(tip_roi.tl());
        }
    }
    if(path.empty() && processTip && !processPath.empty() && !isReference) {
        r.path=processPath;
        r.observed=processPath;
        r.total=processTotal;
        r.visible=processVisible;
        r.bridge=processBridge;
        r.root=processRoot;
        r.rootxy=processRootXY;
        r.rootref=processRootRef;
        r.length=processLength;
        r.tip=r.has=r.path_valid=r.terminal=true;
        r.endpoint=r.tipxy=processPath.back();
        r.first=processPath.front();
        r.tip_measure_reason=path.empty()
            ? "roi_no_path_process_fallback"
            : "process_path_preferred";
        r.terminal_reason=r.basis=r.raw_stop="process_path_fallback";
        r.status=processLength?"main_segment_detected":"tip_only_detected";
        return;
    }
    r.tip_measure_reason=path.empty()
        ? (isReference?"reference_roi_no_path":"roi_no_path")
        : "roi_path_confirmed";
    // Root-connected tracking may certify a length only after an independent
    // endpoint agrees. It never votes on whether a tip exists or where it lies.
    bool full=!path.empty() && r.length && r.root && r.path.size()>1 &&
              norm(path.back()-r.path.back())<=2;
    if(full) {
        auto nearest=r.path.begin();
        for(auto it=path.end()-std::min<size_t>(6,path.size());it!=path.end();++it) {
            nearest=std::min_element(nearest,r.path.end(),[&](P a,P b){
                return norm(a-*it)<norm(b-*it);
            });
            if(norm(*nearest-*it)>3){full=false;break;}
        }
    }
    if(full) {
        r.path.back()=path.back();
        r.total=arc(r.path);
    } else {
        r.path=path;r.total=r.bridge=0;r.root=false;r.rootxy={};r.rootref={};
    }
    r.observed=path;r.visible=arc(path);r.length=full;
    r.tip=r.has=r.path_valid=r.terminal=!path.empty();
    r.endpoint=r.tipxy=r.tip?path.back():P();
    r.first=r.tip?path.front():P();
    r.terminal_reason=r.basis=r.raw_stop=r.stop=r.tip?"roi_terminal_supported":"roi_terminal_unconfirmed";
    r.status=full?"main_segment_detected":r.tip?"tip_only_detected":"no_new_candidate";
}
