#pragma once
#include <string>
#include <vector>
#include <map>
#include <sstream>
#include <iomanip>
#include <cmath>
struct J {
 enum Kind {Null,Number,Boolean,String,Array,Object} kind=Null;
 double number=0;bool boolean=false;std::string string;std::vector<J> array;std::map<std::string,J> object;
 J(){} J(double v):kind(Number),number(v){} J(int v):J(double(v)){} J(long long v):J(double(v)){} J(size_t v):J(double(v)){} J(bool v):kind(Boolean),boolean(v){} J(const char*v):kind(String),string(v){} J(const std::string&v):kind(String),string(v){}
 static J a(std::initializer_list<J> v={}){J j;j.kind=Array;j.array=v;return j;}
 static J o(std::initializer_list<std::pair<const std::string,J>>v={}){J j;j.kind=Object;j.object=v;return j;}
 J& operator[](const std::string&k){kind=Object;return object[k];}
 void push(J v){kind=Array;array.push_back(std::move(v));}
 static void quote(std::ostream&o,const std::string&s){o<<'"';for(unsigned char c:s){if(c=='"'||c=='\\')o<<'\\'<<c;else if(c=='\n')o<<"\\n";else if(c=='\r')o<<"\\r";else if(c=='\t')o<<"\\t";else if(c<32)o<<'?';else o<<c;}o<<'"';}
 void dump(std::ostream&o)const{switch(kind){case Null:o<<"null";break;case Number:if(std::isfinite(number))o<<std::setprecision(17)<<number;else o<<"null";break;case Boolean:o<<(boolean?"true":"false");break;case String:quote(o,string);break;case Array:o<<'[';for(size_t i=0;i<array.size();++i){if(i)o<<',';array[i].dump(o);}o<<']';break;case Object:o<<'{';bool first=true;for(auto&v:object){if(!first)o<<',';first=false;quote(o,v.first);o<<':';v.second.dump(o);}o<<'}';break;}}
 std::string dump()const{std::ostringstream o;dump(o);return o.str();}
};
