#pragma once
namespace fprofile {
struct Times {double local=0,matching=0,score=0,dp=0,audit=0;int calls=0;};
inline thread_local Times* active=nullptr;
struct Guard {Times* old;Guard(Times*p):old(active){active=p;}~Guard(){active=old;}};
struct Scope {double* target;std::chrono::steady_clock::time_point start;Scope(double*p):target(p),start(std::chrono::steady_clock::now()){}~Scope(){if(target)*target+=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();}};
}
