"""Ejecutar el corpus local; no requiere Discord, DB ni proveedor IA."""
import argparse
import json
from pathlib import Path
import sys
import time
import tracemalloc

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from custodio_evaluation import evaluate


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    tracemalloc.start();start=time.perf_counter()
    report=evaluate()
    report['resources']={'elapsed_ms':round((time.perf_counter()-start)*1000),
                         'traced_peak_bytes':tracemalloc.get_traced_memory()[1]}
    tracemalloc.stop()
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({key:report[key] for key in ('cases','executions','totals','resources')}))


if __name__=='__main__':
    main()
