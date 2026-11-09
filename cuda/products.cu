// Original GF(2) sparse block products, MIT. Requant Network: https://requant.network
#include <cuda_runtime.h>
typedef unsigned long long word;
extern "C" __global__ void csr(const int* offsets,const int* columns,const word* x,word* y,int n,int words){
 int at=blockIdx.x*blockDim.x+threadIdx.x;if(at>=n*words)return;
 int r=at/words,w=at%words;word sum=0;
 for(int p=offsets[r];p<offsets[r+1];p++)sum^=x[(size_t)columns[p]*words+w];
 y[at]=sum;
}
extern "C" __global__ void warp_csr(const int* offsets,const int* columns,const word* x,word* y,int n,int words){
 int t=blockIdx.x*blockDim.x+threadIdx.x,at=t/32,lane=t%32;if(at>=n*words)return;
 int r=at/words,w=at%words;word sum=0;
 for(int p=offsets[r]+lane;p<offsets[r+1];p+=32)sum^=x[(size_t)columns[p]*words+w];
 for(int d=16;d;d/=2)sum^=__shfl_down_sync(0xffffffff,sum,d);
 if(!lane)y[at]=sum;
}
extern "C" __global__ void ell(const int* columns,const word* x,word* y,int n,int width,int words){
 int at=blockIdx.x*blockDim.x+threadIdx.x;if(at>=n*words)return;
 int r=at/words,w=at%words;word sum=0;
 for(int p=0;p<width;p++){int c=columns[(size_t)p*n+r];if(c>=0)sum^=x[(size_t)c*words+w];}
 y[at]=sum;
}
