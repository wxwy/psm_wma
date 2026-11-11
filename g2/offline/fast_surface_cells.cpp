// F21 bounded direct triangle -> 1cm cell-center rasterizer.
// Same face-projection/barycentric coverage as F16 Python pilot.
// Geometry only: MuJoCo UV/material and view processing stay in original G2.
// No core nav_sg changes. Compiled on the user's authorized data server.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <new>
#include <vector>
#include <stdexcept>
extern "C" {
struct RasterResult {
    uint32_t* face_ids;
    double* barycentric;  // N x 3
    uint64_t count;
    int status;
};
static RasterResult raster_cells(const double* triangles, const uint8_t* keep, uint32_t nf,
                               double leaf, uint64_t max_points) noexcept {
    RasterResult result{nullptr,nullptr,0,0};
    if(!triangles || !keep || !std::isfinite(leaf) || leaf<=0 || leaf>.05 ||
       nf>1000000 || max_points<1 || max_points>100000000) {
        result.status=-1;return result;
    }
    try {
        std::vector<uint32_t> indices;
        std::vector<double> bary;
        indices.reserve(std::min<uint64_t>(max_points,200000));
        bary.reserve(3*std::min<uint64_t>(max_points,200000));
        for(uint32_t f=0;f<nf;f++) {
            if(!keep[f])continue;
            const double* t=triangles+uint64_t(f)*9;
            double dx0=t[3]-t[0],dy0=t[4]-t[1],dz0=t[5]-t[2];
            double dx1=t[6]-t[0],dy1=t[7]-t[1],dz1=t[8]-t[2];
            const double normals[3]={dy0*dz1-dz0*dy1,
                                      dz0*dx1-dx0*dz1,
                                      dx0*dy1-dy0*dx1};
            double length=std::sqrt(normals[0]*normals[0]+normals[1]*normals[1]+normals[2]*normals[2]);
            if(!(length>1.e-13))continue;
            int dominant=0;
            if(std::fabs(normals[1])>std::fabs(normals[dominant]))dominant=1;
            if(std::fabs(normals[2])>std::fabs(normals[dominant]))dominant=2;
            int a=(dominant==0)?1:0;
            int b=(dominant==2)?1:2;
            // For dominant=1 the other axes must be (0,2). dominant=0 => (1,2).
            if (dominant==0){a=1;b=2;}
            else if(dominant==1){a=0;b=2;}
            else {a=0;b=1;}
            const double u0=t[a],v0=t[b],u1=t[3+a],v1=t[3+b],u2=t[6+a],v2=t[6+b];
            const double det=(u1-u0)*(v2-v0)-(v1-v0)*(u2-u0);
            if(std::fabs(det)<1.e-14)continue;
            const double minu=std::min({u0,u1,u2}), maxu=std::max({u0,u1,u2});
            const double minv=std::min({v0,v1,v2}), maxv=std::max({v0,v1,v2});
            double firstU=std::floor(minu/leaf),lastU=std::ceil(maxu/leaf),
                   firstV=std::floor(minv/leaf),lastV=std::ceil(maxv/leaf);
            if(!std::isfinite(firstU) || !std::isfinite(lastU) ||
               !std::isfinite(firstV) || !std::isfinite(lastV))continue;
            const double nU=lastU-firstU,nV=lastV-firstV;
            if(nU<=0 || nV<=0 || nU*nV>4000000)continue;
            const int64_t loU=static_cast<int64_t>(firstU),hiU=static_cast<int64_t>(lastU),
                          loV=static_cast<int64_t>(firstV),hiV=static_cast<int64_t>(lastV);
            for(int64_t iu=loU;iu<hiU;iu++) {
                const double xx=(iu+0.5)*leaf-u0;
                for(int64_t iv=loV;iv<hiV;iv++) {
                    const double yy=(iv+0.5)*leaf-v0;
                    const double w1=(xx*(v2-v0)-yy*(u2-u0))/det;
                    const double w2=((u1-u0)*yy-(v1-v0)*xx)/det;
                    const double w0=1.-w1-w2;
                    if(w0>=-1.e-9 && w1>=-1.e-9 && w2>=-1.e-9) {
                        if(indices.size()==max_points) {
                            result.status=-2;return result;
                        }
                        indices.push_back(f);
                        bary.push_back(w0);bary.push_back(w1);bary.push_back(w2);
                    }
                }
            }
        }
        result.count=indices.size();
        if(result.count==0)return result;
        result.face_ids=static_cast<uint32_t*>(std::malloc(result.count*sizeof(uint32_t)));
        result.barycentric=static_cast<double*>(std::malloc(result.count*3*sizeof(double)));
        if(!result.face_ids || !result.barycentric) {
            std::free(result.face_ids);std::free(result.barycentric);
            result={nullptr,nullptr,0,-3};return result;
        }
        std::memcpy(result.face_ids,indices.data(),result.count*sizeof(uint32_t));
        std::memcpy(result.barycentric,bary.data(),result.count*3*sizeof(double));
        return result;
    } catch(...) {
        result.status=-4;return result;
    }
}
RasterResult f21_raster_cells(const double*triangles,const uint8_t*keep,uint32_t nf,
                             double leaf,uint64_t max_points) noexcept {
    return raster_cells(triangles,keep,nf,leaf,max_points);
}
void f21_free_result(RasterResult* p) noexcept {
    if(!p)return;
    std::free(p->face_ids);
    std::free(p->barycentric);
    p->face_ids=nullptr;p->barycentric=nullptr;p->count=0;
}
}
