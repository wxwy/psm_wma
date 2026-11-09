"""Reject changed native surface-owner certificates using actual source meshes.

This validates supplied native entity IDs, with the same leaf*.9 proximity and
unique-owner rule as the native Full Map exporter. It produces no new IDs,
Rooms, affiliations or Islands. A BVH bounds the triangle work per source mesh.
"""
import numpy as np

from g2.io import ContractError


def triangle_near(points,triangles,tolerance):
    p=points[:,None,:];a,b,c=triangles[:,0],triangles[:,1],triangles[:,2]
    distance=np.full((len(points),len(triangles)),np.inf);remaining=np.ones(distance.shape,bool)
    # Exact branch order of native triangleDistance, including a non-finite
    # result on some repeated-vertex faces. Native std::min ignores NaN rather
    # than treating a degenerate triangle as a separate finite line segment.
    def take(condition,delta):
        mask=condition&remaining;values=np.linalg.norm(delta,axis=2)
        distance[mask]=values[mask];remaining[mask]=False
    with np.errstate(divide='ignore',invalid='ignore',over='ignore'):
        ab=b-a;ac=c-a;ap=p-a;d1=(ab*ap).sum(axis=2);d2=(ac*ap).sum(axis=2)
        take((d1<=0)&(d2<=0),ap)
        bp=p-b;d3=(ab*bp).sum(axis=2);d4=(ac*bp).sum(axis=2)
        take((d3>=0)&(d4<=d3),bp)
        vc=d1*d4-d3*d2
        take((vc<=0)&(d1>=0)&(d3<=0),p-(a+(d1/(d1-d3))[...,None]*ab))
        cp=p-c;d5=(ab*cp).sum(axis=2);d6=(ac*cp).sum(axis=2)
        take((d6>=0)&(d5<=d6),cp)
        vb=d5*d2-d1*d6
        take((vb<=0)&(d2>=0)&(d6<=0),p-(a+(d2/(d2-d6))[...,None]*ac))
        va=d3*d6-d5*d4
        take((va<=0)&(d4-d3>=0)&(d5-d6>=0),p-(b+((d4-d3)/((d4-d3)+(d5-d6)))[...,None]*(c-b)))
        take(remaining,p-(a+(vb[...,None]*ab+vc[...,None]*ac)/(va+vb+vc)[...,None]))
    return np.any(np.isfinite(distance)&(distance<=tolerance),axis=1)


class SurfaceOwnerVerifier:
    def __init__(self,entities,tolerance):
        self.tolerance=tolerance;self.meshes=[]
        def tree(triangles):
            lo=triangles.min(axis=(0,1));hi=triangles.max(axis=(0,1))
            if len(triangles)<=16:return (lo,hi,triangles,None)
            centers=triangles.mean(axis=1);dim=int(np.argmax(np.ptp(centers,axis=0)))
            order=np.argsort(centers[:,dim],kind='stable');mid=len(order)//2
            return (lo,hi,tree(triangles[order[:mid]]),tree(triangles[order[mid:]]))
        for e in entities:
            if e['triangles']:
                tri=np.asarray(e['vertices'],float)[np.asarray(e['triangles'],int)]
                self.meshes.append((e['id'],np.asarray(e['bbox_min']),np.asarray(e['bbox_max']),tree(tri)))

    def verify(self,points,declared):
        points=np.asarray(points,float);declared=np.asarray(declared);n=len(points)
        counts=np.zeros(n,np.int32);matches=np.zeros(n,bool);tol=self.tolerance
        def visit(node,indices,hit):
            if not len(indices):return
            lo,hi,left,right=node
            delta=np.maximum(np.maximum(lo-points[indices],points[indices]-hi),0)
            indices=indices[(delta*delta).sum(axis=1)<=(tol+1e-12)**2]
            indices=indices[~hit[indices]]
            if right is None:
                for start in range(0,len(indices),1024):
                    selected=indices[start:start+1024]
                    hit[selected]=triangle_near(points[selected],left,tol)
            else:visit(left,indices,hit);visit(right,indices,hit)
        for key,lo,hi,node in self.meshes:
            indices=np.flatnonzero(np.all((points>=lo-tol)&(points<=hi+tol),axis=1))
            if not len(indices):continue
            hit=np.zeros(n,bool);visit(node,indices,hit)
            counts[hit]+=1;matches[hit]|=declared[hit]==key
        correct=np.where(counts==1,matches,declared=='unknown')
        if not np.all(correct):raise ContractError('Full Map surface entity owner differs from actual native source geometry')
