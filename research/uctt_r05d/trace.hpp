#pragma once
// Only the isolated D0/D1 targets include this file. No annotation fields.
namespace r05d {
using Point=cv::Point2d;
struct Peak {double gain=0;int x=0,y=0,hits=0,tail=0,shared=-1;double slope=0;std::string stage="not_visited_after_rank_stop";std::vector<Point> line;};
struct Match {cv::Rect rect;Point delta;double quality=0,second=0;std::string method;};
struct LocalTile {cv::Rect tile;int votes=0,agree=0;Point offset;std::string stage="entry";std::vector<double> correlations;};
struct Trace {
 cv::Rect roi; int turn=0;Point center,direction;bool reference=false,registration=false;
 cv::Mat current,score,registered,prior,reason,valid,gains,back;
 std::vector<Peak> peaks;std::vector<Match> matches;
 std::vector<LocalTile> local_tiles;
 std::vector<Point> local,original,mainpath;
 std::vector<std::vector<Point>> main_rois;
 std::string motion_branch="not_run",terminal="not_run";
 double solve_angle=0,solve_residual=0;int solve_inliers=0,solve_matches=0;
};
inline thread_local Trace* active=nullptr;
inline thread_local bool capture=true;
inline thread_local int offline_variant=0;
inline thread_local cv::Rect offline_fixed_roi;
struct Guard {Trace* old;Guard(Trace* p):old(active){active=p;}~Guard(){active=old;}};
inline Peak* peak(int x,int y){if(!active||!capture)return nullptr;for(auto &p:active->peaks)if(p.x==x&&p.y==y)return &p;return nullptr;}
inline void stage(Peak* p,const char* s){if(p)p->stage=s;}
}
