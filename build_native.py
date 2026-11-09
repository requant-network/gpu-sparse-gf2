"""Build an attributed stage-three correction without editing the upstream checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

PIN='ebfe814b759803f61771b36d1fd197b71b751d1d'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('upstream',type=Path)
    parser.add_argument('upstream_build',type=Path)
    parser.add_argument('--nvcc',default='nvcc')
    args=parser.parse_args();up=args.upstream.resolve();ub=args.upstream_build.resolve()
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=up,text=True).strip()==PIN
    assert not subprocess.check_output(['git','diff','--name-only'],cwd=up,text=True).strip(), 'Keep upstream sources immutable'
    target=Path('build/patched-stage3');assert not target.exists(),'Use a new build directory'
    relative=Path('src/lingen/stage3/solution_reconstructor.cu')
    (target/relative).parent.mkdir(parents=True)
    shutil.copy2(up/relative,target/relative)
    patch=Path('patches/batch-reconstruction.patch').resolve()
    # --directory applies only to our copied source; the pinned upstream remains untouched.
    subprocess.run(['git','apply','--check','--directory='+str(target),str(patch)],check=True)
    subprocess.run(['git','apply','--directory='+str(target),str(patch)],check=True)
    flags=['-O3','-std=c++17','-arch=sm_120','-rdc=true','-Xcompiler=-fopenmp']
    includes=['-I'+str(up/p) for p in ('include','src','cuda_spmm/include','utils')]+['-I'+str(ub/'generated')]
    commands=[]
    def run(command):
        subprocess.run(command,check=True)
        commands.append([str(x).replace(str(up),'UPSTREAM').replace(str(ub),'UPSTREAM_BUILD') for x in command])
    object_file=Path('build/solution-corrected.o')
    run([args.nvcc,*flags,*includes,'-c',str(target/relative),'-o',str(object_file)])
    archive=Path('build/liblingen-corrected.a');shutil.copy2(ub/'liblingen_ops.a',archive)
    run(['ar','d',str(archive),'solution_reconstructor.cu.o'])
    libraries=[str(archive),str(ub/'cuda_spmm/libspmm_core.a'),str(ub/'cuda_spmm/libhpc_logger.a')]
    common=[*flags,*includes,str(object_file),*libraries,'-lcudart','-lgomp','-lpthread','-ldl']
    run([args.nvcc,'native/solve.cpp',*common,'-o','build/solve-corrected'])
    run([args.nvcc,str(up/'benchmarks/bw_lingen_smoke.cu'),*common,'-o','build/smoke-corrected'])
    files=['build_native.py','native/solve.cpp','patches/batch-reconstruction.patch']
    record=dict(upstream_revision=PIN,commands=commands,
        nvcc_version=subprocess.check_output([args.nvcc,'--version'],text=True),
        source_sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in files},
        patched_source_sha256=hashlib.sha256((target/relative).read_bytes()).hexdigest(),
        binary_sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ('build/solve-corrected','build/smoke-corrected')},
        upstream_libraries_sha256={str(p.relative_to(ub)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ub/'liblingen_ops.a',ub/'cuda_spmm/libspmm_core.a',ub/'cuda_spmm/libhpc_logger.a')},
        scope='Keep all native oracle, annihilation and SpMM checks. Replace only stage-three object, because nvcc device linking loads all archive device objects.')
    Path('results/native-build.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
