"""Evaluación reproducible de señales locales con etiquetas sintéticas independientes."""
from collections import defaultdict
from pathlib import Path
import json
from custodio_taxonomy import BEHAVIORS
from custodio_detection import LocalDetector

CORPUS = Path(__file__).with_name('data') / 'custodio_evaluation_cases.json'


def classify(case,sensitivity):
    behavior=BEHAVIORS[case['category']]
    if not behavior.kinds:
        return 'human_review'
    detector=LocalDetector()
    detected=False
    for number,event in enumerate(case['events'],1):
        event=dict(event)
        now=event.pop('at',float(number))
        detected=bool(detector.inspect(guild_id=1,channel_id=event.pop('channel_id',200),
            actor_id=event.pop('actor_id',100),message_id=number,now=now,
            kinds=behavior.kinds,sensitivity=sensitivity,rule_number=1,**event)) or detected
    return 'signal' if detected else 'clear'


def evaluate(data=None):
    corpus=data if data is not None else json.loads(CORPUS.read_text())
    if corpus.get('version')!=1 or corpus.get('synthetic') is not True:
        raise ValueError('synthetic_corpus_required')
    buckets=defaultdict(lambda:{'tp':0,'fp':0,'tn':0,'fn':0,'human_review':0})
    samples=[]
    for case in corpus['cases']:
        if case['category'] not in BEHAVIORS or case['gold'] not in {'signal','clear','human_review'}:
            raise ValueError('invalid_evaluation_case')
        for sensitivity in corpus['sensitivities']:
            result=classify(case,sensitivity)
            if result=='human_review':
                label='human_review'
            elif result=='signal':
                label='tp' if case['gold']=='signal' else 'fp'
            else:
                label='fn' if case['gold']=='signal' else 'tn'
            bucket=buckets[(case['category'],case['locale'],sensitivity)]
            bucket[label]+=1
            samples.append({'id':case['id'],'sensitivity':sensitivity,'predicted':result,
                            'result':label,'known_limit':case.get('known_limit')})
    groups=[]
    total={key:0 for key in ('tp','fp','tn','fn','human_review')}
    for (category,locale,sensitivity),counts in sorted(buckets.items()):
        for key,value in counts.items():total[key]+=value
        groups.append({'category':category,'locale':locale,'sensitivity':sensitivity,**counts,
            'precision':counts['tp']/(counts['tp']+counts['fp']) if counts['tp']+counts['fp'] else None,
            'recall':counts['tp']/(counts['tp']+counts['fn']) if counts['tp']+counts['fn'] else None})
    return {'version':1,'synthetic':True,'cases':len(corpus['cases']),
            'executions':len(samples),'totals':total,'by_category_locale_sensitivity':groups,
            'results':samples}
