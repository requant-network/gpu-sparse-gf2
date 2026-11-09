// Original Requant Network harness; links the separately licensed unmodified Block Wiedemann library.
#include "bw_solver.h"
#include "hpc_logger.h"
#include <fstream>
#include <chrono>
#include <set>
#include <sys/resource.h>

static uint32_t word(std::ifstream& in){uint32_t x;in.read((char*)&x,4);if(!in)throw std::runtime_error("Truncated matrix");return x;}
int main(int argc,char** argv){
 try{
  if(argc!=8)throw std::runtime_error("input output block tune seed serial oracle");
  std::ifstream in(argv[1],std::ios::binary);if(word(in)!=0x32464752)throw std::runtime_error("Matrix magic");
  uint32_t n=word(in);if(!n||n>1000000)throw std::runtime_error("Matrix dimension");
  HostMatrix matrix;matrix.n_rows=matrix.n_cols=n;matrix.rows.resize(n);size_t nnz=0;
  for(auto& row:matrix.rows){uint32_t count=word(in);if(count>n)throw std::runtime_error("Row size");
   for(uint32_t i=0;i<count;i++){uint32_t j=word(in);if(j>=n||(!row.empty()&&j<=row.back()))throw std::runtime_error("Column order/range");row.push_back(j);}nnz+=count;
  }
  lingen::BWSolverConfig cfg;cfg.nrows=n;cfg.m_block=cfg.n_block=std::stoi(argv[3]);cfg.block_size_pinned=true;
  cfg.solve_transposed=false;cfg.seed=std::stoi(argv[5]);cfg.autotune_tune_spmm=std::stoi(argv[4]);
  cfg.autotune_skip_if_present=false;cfg.autotune_verify_spmm=true;cfg.stage3_max_solutions=5;
  cfg.stage1_load_checkpoints=false;cfg.stage2_load_checkpoints=false;cfg.stage3_load_checkpoints=false;
  cfg.stage1_save_checkpoints=false;cfg.stage2_save_checkpoints=false;cfg.stage3_save_checkpoints=false;
  cfg.stage3_batch_mode=!std::stoi(argv[6]);cfg.enable_all_oracle_verification=std::stoi(argv[7]);
  cfg.stage2_check_annihilation_gpu=true;cfg.stage2_init_cross_check=true;
  LogConfig log;log.enable_cout=true;log.min_severity_cout=LOG_INFO;HPCLogger::Get().Init(log);
  auto begin=std::chrono::steady_clock::now();lingen::BlockWiedemannSolver solver(cfg,matrix);
  auto initialized=std::chrono::steady_clock::now();solver.Solve();auto solved=std::chrono::steady_clock::now();
  const auto& solutions=solver.get_solutions();std::set<std::vector<uint64_t>> distinct;
  for(const auto& v:solutions){
   if(v.size()!=(n+63)/64)throw std::runtime_error("Vector shape");bool nonzero=false;for(auto w:v)nonzero|=w!=0;
   if(!nonzero)throw std::runtime_error("Zero certificate");
   for(const auto& row:matrix.rows){bool sum=false;for(auto j:row)sum^=(v[j/64]>>(j%64))&1;if(sum)throw std::runtime_error("Independent A*x failed");}
   if(!distinct.insert(v).second)throw std::runtime_error("Repeated certificate");
  }
  auto verified=std::chrono::steady_clock::now();rusage usage;getrusage(RUSAGE_SELF,&usage);
  auto ms=[](auto a,auto b){return std::chrono::duration<double,std::milli>(b-a).count();};
  std::ofstream out(argv[2]);if(!out)throw std::runtime_error("Output open");out.precision(17);
  out<<"{\"n\":"<<n<<",\"nonzeros\":"<<nnz<<",\"block\":"<<cfg.n_block<<",\"tuned\":"<<(cfg.autotune_tune_spmm?"true":"false")
     <<",\"seed\":"<<cfg.seed<<",\"serial\":"<<(cfg.stage3_batch_mode?"false":"true")<<",\"oracle\":"<<(cfg.enable_all_oracle_verification?"true":"false")
     <<",\"initialization_wall_ms\":"<<ms(begin,initialized)<<",\"solve_wall_ms\":"<<ms(initialized,solved)<<",\"independent_verify_ms\":"<<ms(solved,verified)
     <<",\"complete_verified_wall_ms\":"<<ms(begin,verified)<<",\"peak_rss_kib\":"<<usage.ru_maxrss<<",\"solutions\":[";
  for(size_t i=0;i<solutions.size();i++){if(i)out<<",";out<<"[";for(size_t j=0;j<solutions[i].size();j++){if(j)out<<",";out<<solutions[i][j];}out<<"]";}
  out<<"]}\n";return solutions.empty()?3:0;
 }catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
