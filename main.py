"""학습 구간에서 예측 편향 보정값을 구하고 별도의 시간 후행 검증 구간에서 개선·오차·보정 한도를 모두 통과해야 후보를 승인합니다."""
import argparse, json, math, html
from pathlib import Path

def finite(value, name, minimum=None):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(name + ': finite number required')
    if minimum is not None and value < minimum:
        raise ValueError(name + ': below minimum')
    return value

def report(result, title):
    payload=html.escape(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
    return '<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>body{font:16px/1.6 system-ui;max-width:1000px;margin:32px auto;padding:20px;background:#101b2b;color:#ecf4ff}pre{padding:24px;background:#192b40;border-radius:12px;white-space:pre-wrap;overflow-wrap:anywhere}h1{color:#80e4c5}</style><h1>'+html.escape(title)+'</h1><p>오프라인 샘플 계산 결과 · 실물 장비 연결 없음</p><pre>'+payload+'</pre></html>'

def cli(run,title):
    parser=argparse.ArgumentParser(description=title)
    parser.add_argument('--input',default=str(Path(__file__).with_name('sample-input.json')))
    parser.add_argument('--html',help='optional standalone HTML result path')
    args=parser.parse_args()
    try:
        data=json.loads(Path(args.input).read_text(encoding='utf-8'))
        result=run(data)
        if args.html: Path(args.html).write_text(report(result,title),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
    except (ValueError,KeyError,TypeError) as exc:
        parser.exit(2, 'input error: '+str(exc)+'\n')

import statistics

def check_rows(rows):
    if len(rows)<2:raise ValueError('at least two samples per split')
    times=[]
    for r in rows:
        times.append(finite(r['time_s'],'time_s',0));finite(r['observed'],'observed');finite(r['predicted'],'predicted')
    if any(a>=b for a,b in zip(times,times[1:])):raise ValueError('strictly increasing timestamps required')
    return times

def run(data):
    train=data['train'];validation=data['validation'];tt=check_rows(train);vt=check_rows(validation)
    if max(tt)>=min(vt):raise ValueError('training/validation temporal leakage')
    max_offset=finite(data['max_offset'],'max_offset',0);max_mae=finite(data['max_validation_mae'],'max_validation_mae',0)
    minimum=finite(data['min_improvement'],'min_improvement',0)
    offset=statistics.median(r['observed']-r['predicted'] for r in train)
    baseline=sum(abs(r['observed']-r['predicted']) for r in validation)/len(validation)
    candidate=sum(abs(r['observed']-r['predicted']-offset) for r in validation)/len(validation)
    improvement=baseline-candidate;reasons=[]
    if abs(offset)>max_offset:reasons.append('offset_limit_exceeded')
    if candidate>max_mae:reasons.append('validation_error_exceeded')
    if improvement<minimum or improvement<=0:reasons.append('insufficient_improvement')
    return {'approved':not reasons,'reasons':reasons,'proposed_offset':round(offset,6),
            'baseline_validation_mae':round(baseline,6),'candidate_validation_mae':round(candidate,6),
            'absolute_improvement':round(improvement,6),'training_samples':len(train),'validation_samples':len(validation),
            'applied_to_production':False,'method':'training_median_residual_offset'}

if __name__ == "__main__": cli(run,'트윈 보정 배포 검증기')
