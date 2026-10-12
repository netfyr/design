#!/usr/bin/env python3
"""Build the 28-style netfyr expansion from a user-supplied original source kit.

The distribution deliberately contains software and proof material, not font
binaries. The original 0.401 reference kit is required. No network access,
license assignment or Google Fonts submission is performed.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, os, shutil, stat
import subprocess, sys, time, zipfile
from pathlib import Path

WEIGHTS=(300,400,500,600,700,800,900)
ROOT=Path(__file__).resolve().parents[1]
INPUT_SHA="380134d54c9d51461d7c2d13069044bf5d5e47075e585add28e478f8ff017e47"

def sha(path: Path) -> str:
    with path.open("rb") as f:
        h=hashlib.sha256()
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def find_kit(path: Path) -> Path:
    for candidate in [path,path/"netfyr-type-kit"]:
        if (candidate/"fonts/netfyr-sans-Regular.ttf").is_file():
            return candidate
    raise ValueError("Reference must contain fonts/netfyr-sans-Regular.ttf and the other 0.401 styles.")

def reference(source: Path, output: Path, allow_other: bool) -> Path:
    if source.is_dir():kit=find_kit(source)
    else:
        if not source.is_file():raise FileNotFoundError(source)
        digest=sha(source)
        if digest!=INPUT_SHA and not allow_other:
            raise ValueError("Reference ZIP does not match the tested 0.401 kit. "
                             "Use --allow-other-reference only after reviewing compatibility.")
        dest=output/"reference";dest.mkdir(exist_ok=True)
        with zipfile.ZipFile(source) as z:
            if sum(v.file_size for v in z.infolist())>2_000_000_000:
                raise ValueError("Reference archive exceeds the extraction limit.")
            for item in z.infolist():
                relative=Path(item.filename)
                if relative.is_absolute() or ".." in relative.parts or "\\" in item.filename:
                    raise ValueError("Unsafe archive path")
                if stat.S_ISLNK(item.external_attr>>16):raise ValueError("Archive symlinks are not accepted")
                target=dest/relative
                if item.is_dir():target.mkdir(parents=True,exist_ok=True);continue
                target.parent.mkdir(parents=True,exist_ok=True)
                with z.open(item) as src,target.open("wb") as dst:shutil.copyfileobj(src,dst)
        kit=find_kit(dest)
    manifest=kit/"SHA256SUMS.txt"
    if manifest.is_file():
        for line in manifest.read_text().splitlines():
            if not line.strip():continue
            digest,relative=line.split(maxsplit=1);relative=relative.lstrip("*")
            q=Path(relative)
            if q.is_absolute() or ".." in q.parts:raise ValueError("Unsafe manifest path")
            path=kit/q
            if not path.is_file() or sha(path)!=digest:raise ValueError("Reference checksum mismatch: "+relative)
    for family in ("sans","mono"):
        for style in ("Regular","Semibold"):
            if not (kit/f"fonts/netfyr-{family}-{style}.ttf").is_file():
                raise FileNotFoundError(f"Missing protected reference style {family}/{style}")
    return kit

def run(command: list[str], log: Path, env: dict[str,str]) -> dict:
    started=time.time()
    with log.open("w") as stream:
        result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,env=env)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}); inspect {log}")
    return {"command":command,"log":str(log),"started":started,"ended":time.time(),
            "returncode":result.returncode}

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reference",required=True,type=Path,help="Original 0.401 ZIP or extracted kit")
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--jobs",type=int,default=4)
    p.add_argument("--boolean",choices=["inkscape","pathops"],default="inkscape")
    p.add_argument("--allow-other-reference",action="store_true")
    p.add_argument("--documents",action="store_true")
    p.add_argument("--validate",action="store_true")
    args=p.parse_args()
    if not 1<=args.jobs<=16:p.error("--jobs must be between 1 and 16")
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    if any((output/"fonts").glob("*.ttf")):
        p.error("Choose an output without existing fonts; pair corrections must not be applied twice.")
    env=os.environ.copy();env["NETFYR_BOOLEAN"]=args.boolean
    if args.boolean=="inkscape" and not shutil.which("inkscape"):
        p.error("Inkscape is required for the tested native Bézier union path.")
    if args.boolean=="pathops":
        try:import pathops
        except ImportError:p.error("Install skia-pathops or select --boolean inkscape")
    kit=reference(args.reference.resolve(),output,args.allow_other_reference)
    logs=output/"logs";logs.mkdir(exist_ok=True)
    recipe=ROOT/"sources/recipes";records=[]
    tasks=[]
    for family in ("sans","mono"):
        for weight in WEIGHTS:
            for italic in (False,True):
                cmd=[sys.executable,str(recipe/"expand_family.py"),"--family",family,
                     "--weight",str(weight),"--output",str(output),"--reference",str(kit),
                     "--logo",str(ROOT/"assets/netfyr-mark.svg")]
                if italic:cmd.append("--italic")
                tasks.append((cmd,logs/f"{family}-{weight}-{'italic' if italic else 'upright'}.log"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures=[pool.submit(run,cmd,log,env) for cmd,log in tasks]
        for future in concurrent.futures.as_completed(futures):
            records.append(future.result());print(f"Built {len(records)}/28 styles",flush=True)
    for script,arguments in [
        ("finish_family.py",[str(output/"fonts")]),
        ("apply_clearance.py",[str(output/"fonts"),str(ROOT/"sources/clearance-adjustments.json")])
    ]:
        records.append(run([sys.executable,str(recipe/script)]+arguments,logs/(script+".log"),env))
    if args.validate:
        from concurrent.futures import ThreadPoolExecutor,as_completed
        audit=output/"validation";audit.mkdir(exist_ok=True)
        with ThreadPoolExecutor(max_workers=min(4,args.jobs)) as pool:
            futures=[]
            for track in ("metadata","shaping","geometry","cells"):
                cmd=[sys.executable,str(ROOT/"sources/validation/validate.py"),
                     "--track",track,"--fonts",str(output/"fonts"),
                     "--reference",str(kit),"--output",str(audit/f"{track}.json")]
                futures.append(pool.submit(run,cmd,logs/(track+".log"),env))
            records.extend(f.result() for f in as_completed(futures))
        for report in audit.glob("*.json"):
            result=json.loads(report.read_text())
            if not result.get("passed",False):
                raise RuntimeError(f"Validation did not pass; inspect {report}")

    if args.documents:
        docs=output/"documents";docs.mkdir(exist_ok=True)
        env["NETFYR_BUILD"]=str(output);env["NETFYR_DELIVERY"]=str(docs)
        for script in ("build_brand.py","build_specimen.py","build_type_guide.py"):
            records.append(run([sys.executable,str(ROOT/"sources/documents"/script)],
                               logs/(script+".log"),env))
    actual={path.name:sha(path) for path in sorted((output/"fonts").glob("*.ttf"))}
    expected_path=ROOT/"validation/final-font-hashes.json"
    expected=json.loads(expected_path.read_text()) if expected_path.exists() else {}
    summary={"styles":len(actual),"hashes":actual,"reference":str(kit),
             "boolean_backend":args.boolean,
             "identical_to_recorded_environment":actual==expected,
             "records":records}
    (output/"build-report.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps({"styles":len(actual),"output":str(output),
          "byte_identical_to_recorded_build":actual==expected},indent=2))
    if actual!=expected and expected:
        print("Byte differences do not prove a design failure. Inspect tool versions and run local QA.",file=sys.stderr)

if __name__=="__main__":
    main()
