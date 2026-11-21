// Helpers use the same column order as the dynamic programming traces.
struct Runs {
    int count=0, current=0, longest=0, gap=0, maxGap=0;
    void add(bool v) {
        count+=v;
        current=v?current+1:0;
        gap=v?0:gap+1;
        longest=std::max(longest,current);
        maxGap=std::max(maxGap,gap);
    }
};
static bool blankCrossing(Point initial,const Path& path,const Mat& dual) {
    Point d=path.back()-initial;
    if(d.x<=25 && std::abs(d.y)<=15) return false;
    Runs r;
    for(Point p:path) if(p.x>initial.x) r.add(dual.at<uchar>(p)!=0);
    return r.longest<8 || r.maxGap>std::min(16,std::max(8,rnd(.20*d.x)));
}
static Path recovery(const Evidence &f,const Mat &field,const Path& initial,const Lattice& dp) {
    if(initial.size()<25) return initial;
    Point end=initial.back();
    Path best=initial;
    for(int x=end.x+8;x<std::min(field.cols-1,end.x+25);++x) {
        double val,left,right; Point peak;
        cv::minMaxLoc(dp.values.col(x),nullptr,&val,nullptr,&peak);
        cv::minMaxLoc(dp.values.col(x-1),nullptr,&left);
        cv::minMaxLoc(dp.values.col(x+1),nullptr,&right);
        if(!std::isfinite(val)||val<std::max(left,right)||std::abs(peak.y-end.y)>15) continue;
        Path alt=dp.trace({x,peak.y});
        if(alt.size()<=initial.size() || !std::equal(initial.begin(),initial.end(),alt.begin())) continue;
        Runs support; int core=0;
        auto inc=increments(field,alt);
        double sum=0,low=INFINITY;
        for(size_t j=initial.size();j<alt.size();++j) {
            Point p=alt[j];
            support.add(cv::countNonZero(f.dual.col(p.x).rowRange(std::max(0,p.y-1),std::min(f.dual.rows,p.y+2)))!=0);
            core+=bool(f.core.at<uchar>(p));
            sum+=inc[j]; low=std::min(low,sum);
        }
        int n=x-end.x;
        if(support.count>=6 && 3*support.count>=n && support.maxGap<=6 && core>=.65*n &&
           sum-low>=1.5 && *std::min_element(inc.end()-3,inc.end())>0 &&
           std::accumulate(inc.end()-3,inc.end(),0.)>.60) best=std::move(alt);
    }
    return best;
}
static int bridge(const Evidence &f,const Scene &s,const Mat &field,Path &path) {
    Point end=path.back(); int rad=std::max(8,px(.13)),lo=std::max(0,end.y-rad);
    int n=std::min(field.cols-end.x,std::max(24,px(.52)));
    auto safe=[&](int y){return y+s.sl.y>=s.top+px(.035) && y+s.sl.y<s.bottom-px(.035);};
    if(n<=8||!safe(end.y))return 0;
    Rect box(end.x,lo,n,std::min(field.rows,end.y+rad+1)-lo);
    Mat raw=field(box),lift(raw.size(),CV_32F),seed=Mat::zeros(box.height,1,CV_8U);
    seed.at<uchar>(end.y-lo)=1;
    for(int row=std::max(lo,end.y-std::min(4,px(.012)));row<=std::min(box.br().y-1,end.y+std::min(4,px(.012)));++row) {
        bool supported=safe(row);
        for(int x=1;x<=3;++x) supported &= cv::countNonZero(f.dual.col(end.x+x).rowRange(std::max(lo,row-1),std::min(box.br().y,row+2)))>0;
        if(supported)seed.at<uchar>(row-lo)=1;
    }
    for(int y=0;y<box.height;++y) for(int x=0;x<n;++x) {
        Point p=box.tl()+Point(x,y); double v=raw.at<float>(y,x);
        bool red=f.red.at<uchar>(p)!=0;
        double z=red?std::max(v,std::min(1.4,.32+.38*f.strength.at<float>(p))):
                 f.core.at<uchar>(p)?clip(v,-.14,.12):std::min(v,-.38);
        lift.at<float>(y,x)=!x?0.f:(!std::isfinite(v)||!safe(p.y)||(!red&&f.fine.at<uchar>(p))||f.dip.at<uchar>(p))?-INFINITY:float(z);
    }
    Lattice dp(lift,seed,false); Path tail=dp.trace(dp.best);
    if(tail.size()<=8)return 0;
    int witness=0;
    for(int j=0;j<std::min<int>(path.size(),std::max(6,px(.10)));++j)witness+=f.red.at<uchar>(path[j]) && f.core.at<uchar>(path[j]);
    auto steps=increments(raw,tail),nets=increments(lift,tail);
    double curve=0,low=0,gain=nets[0]; Runs dual,red;
    bool early=false,prev=false;int best=0;
    for(int j=1;j<int(tail.size());++j) {
        Point p=tail[j]+box.tl();bool measured=f.dual.at<uchar>(p)!=0;
        dual.add(measured);red.add(f.red.at<uchar>(p)!=0);
        if(j<=4)early|=measured;
        curve+=steps[j]; low=std::min(low,curve);gain+=nets[j];
        bool shortRun=dual.longest>=8 && dual.count>=.70*j && early;
        bool rising=witness>=2 && j>=15 && red.longest>=6 && curve-low>=1. && steps[j]+steps[j-1]+steps[j-2]>.15;
        if(j>=8 && (shortRun||rising) && gain>.12*j && prev && measured)best=j;
        prev=measured;
    }
    if(!best)return 0;
    Path extended=path;
    for(int j=1;j<=best;++j)extended.push_back(tail[j]+box.tl());
    if(blankCrossing(end,extended,f.dual))return 0;
    if(path.size()>.18*scale) {
        auto stepsAll=increments(field,extended);
        if(std::accumulate(stepsAll.begin()+path.size(),stepsAll.end(),0.)<=0 &&
           std::accumulate(stepsAll.end()-std::min(5,best),stepsAll.end(),0.)<=0)return 0;
    }
    path.swap(extended);return best;
}
static Path rescue(const Evidence &f,const Scene &s,const Mat& field,const Mat &entry,bool fork,double& score) {
    int n=std::min(field.cols,px(.55)); if(n<8)return {};
    Mat mask=f.dual.colRange(0,n).clone();
    for(int y=0;y<mask.rows;++y)
        if(y+s.sl.y<s.top+px(.035)||y+s.sl.y>=s.bottom-px(.035)) mask.row(y).setTo(0);
    if(cv::countNonZero(mask)<8)return {};
    Mat start=entry;
    std::vector<Point> roots;
    auto connected=[&](int x,int y,int row){
        for(int a=std::min(y,row);a<=std::max(y,row);++a)if(!f.core.at<uchar>(a,x))return false;
        return true;
    };
    if(fork) {
        start=Mat::zeros(entry.size(),CV_8U);cv::findNonZero(entry,roots);
        for(Point p:roots)for(int y=std::max(0,p.y-px(.012));y<=std::min(entry.rows-1,p.y+px(.012));++y) {
            if(p.x+3<n && cv::countNonZero(f.dual.row(y).colRange(p.x+1,p.x+4))==3 && connected(p.x,p.y,y))start.at<uchar>(y,p.x)=1;
        }
        if(!cv::countNonZero(start))return {};
    }
    Mat lift=field.colRange(0,n).clone();
    for(int y=0;y<lift.rows;++y)for(int x=0;x<n;++x) {
        auto &v=lift.at<float>(y,x);
        if(std::isfinite(v))v=mask.at<uchar>(y,x)?std::max(v,1.4f):std::min(v,-.35f);
    }
    Lattice dp(lift,start,true); Path path=dp.trace(dp.best);if(path.size()<8)return {};
    Runs r;for(Point p:path)r.add(mask.at<uchar>(p)!=0);
    if(r.longest<8 || r.count<.55*path.size() || !mask.at<uchar>(path.back()))return {};
    if(fork) {
        Point &first=path.front();int best=-1,dist=INT_MAX;
        for(Point p:roots)if(p.x==first.x && std::abs(p.y-first.y)<=px(.012) && std::abs(p.y-first.y)<dist && connected(p.x,p.y,first.y)) {
            dist=std::abs(p.y-first.y);best=p.y;
        }
        if(best<0)return {};
        first.y=best;
    }
    score=dp.values.at<float>(dp.best);return path;
}
