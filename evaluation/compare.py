"""Compare saved, independent inference with attributed accessibility references."""
import argparse,csv,hashlib,html,json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
KO={'Music':'음악','Snoring':'코 고는 소리','Sniff':'킁킁거림','Sigh':'한숨','Breathing':'숨소리','Snort':'코로 거칠게 숨 내쉬는 소리','Burst, pop':'뽁·펑 소리','Plop':'툭·퐁 소리','Crack':'뚝 소리','Thump, thud':'쿵·툭 충격음','Groan':'신음','Grunt':'끙 하는 소리','Animal':'동물 소리','Speech':'말소리','Male speech, man speaking':'남성 말소리','Gasp':'헉 하는 숨소리','Wheeze':'쌕쌕거림','Growling':'으르렁거림','Roar':'포효','Purr':'가르랑 소리','Rustle':'바스락 소리','Rustling leaves':'나뭇잎 바스락 소리','Wind':'바람 소리','Bird vocalization, bird call, bird song':'새소리','Chirp, tweet':'짹짹 소리','Cough':'기침','Laughter':'웃음소리','Snicker':'낄낄거림'}
STATUS={'matched':'같은 종류 감지','related':'비슷한 종류만 감지','different':'다른 종류로 분류','missing':'해당 효과음 후보 없음','unsupported':'모델에 하품 분류 없음'}
def clock(t):
 n=round(t*1000);m,n=divmod(n,60000);s,ms=divmod(n,1000)
 return f'{m:02}:{s:02}.{ms:03}'
def overlap(a,b):return max(0,min(a['end'],b['end'])-max(a['start'],b['start']))
def show(e):return KO.get(e['label'],e['text'].removeprefix('소리 후보: '))+' ('+e['label']+')'
def main(raw_path):
 raw=json.loads(Path(raw_path).read_text(encoding='utf-8'))
 refs=json.loads((ROOT/'data/caption-sources.json').read_text(encoding='utf-8'))
 rules=json.loads((ROOT/'evaluation/comparison-rules.json').read_text(encoding='utf-8'))
 assert hashlib.sha256((ROOT/'assets/movie-clip.mp4').read_bytes()).hexdigest()==raw['input_sha256'],'Not the same film clip'
 assert len(refs['events'])==len(rules['reference_categories'])==11
 events=raw['events']; rows=[]
 for i,(ref,rule) in enumerate(zip(refs['events'],rules['reference_categories'])):
  nearby=[(j,e) for j,e in enumerate(events) if overlap(ref,e)>=rules['minimum_overlap_seconds']]
  exact=[(j,e) for j,e in nearby if e['label'] in rule['accepted']]
  related=[(j,e) for j,e in nearby if e['label'] in rule['related']]
  other=[(j,e) for j,e in nearby if e['label']!='Music']
  state='unsupported' if rule.get('unsupported') else 'matched' if exact else 'related' if related else 'different' if other else 'missing'
  best=max(exact,key=lambda x:overlap(ref,x[1])) if exact else None
  row={'reference_id':i+1,**ref,'category':rule['category'],'status':state,'status_ko':STATUS[state],
   'overlapping_ai':[{'event_id':j+1,'label':e['label'],'text_ko':show(e),'start':e['start'],'end':e['end'],'score':e['score']} for j,e in nearby],
   'matched_event_ids':[j+1 for j,e in exact]}
  if best:
   e=best[1];row['start_error_seconds']=round(e['start']-ref['start'],3);row['end_error_seconds']=round(e['end']-ref['end'],3)
   row['both_boundaries_within_1s']=abs(row['start_error_seconds'])<=1 and abs(row['end_error_seconds'])<=1
  rows.append(row)
 counts={k:sum(r['status']==k for r in rows) for k in STATUS}
 matched_ids={n for r in rows for n in r['matched_event_ids']}
 additional=[dict(event_id=i+1,**e,text_ko=show(e)) for i,e in enumerate(events) if i+1 not in matched_ids and e['label']!='Music']
 result={'clip_start_in_movie':30,'duration':raw['duration'],'reference_count':11,'ai_event_count':len(events),'ai_effect_event_count':sum(e['label']!='Music' for e in events),'counts':counts,'timing_within_1s_count':sum(r.get('both_boundaries_within_1s',False) for r in rows),'rules':rules,'comparison':rows,'additional_candidates':additional,'model':raw['model'],'elapsed_seconds':raw['elapsed_seconds'],'input_sha256':raw['input_sha256']}
 (ROOT/'data/ai-raw-result.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (ROOT/'data/ai-comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/'data/ai-comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(['원본_시작','원본_끝','참고자막','AI가_같은구간에서_출력한_후보','비교결과','시작오차초_동종후보만','끝오차초_동종후보만'])
  for r in rows:w.writerow([clock(r['source_start']),clock(r['source_end']),r['text'],' / '.join(x['text_ko']+' '+clock(x['start']+30)+'~'+clock(x['end']+30) for x in r['overlapping_ai']) or '출력 없음',r['status_ko'],r.get('start_error_seconds',''),r.get('end_error_seconds','')])
 headline=f"참고 자막 11개 구간 중 같은 소리 종류가 겹친 구간은 {counts['matched']}개입니다."
 note='이는 공개 자막과의 구간별 비교이며 정확도 점수가 아닙니다. 소리 원인과 세밀한 시작·끝까지 맞았다는 뜻도 아닙니다. 같은 AI 후보가 여러 참고 구간과 겹칠 수 있습니다.'
 tr=[]
 for r in rows:
  found='<br>'.join(html.escape(x['text_ko'])+'<br><small>원본 '+clock(x['start']+30)+'–'+clock(x['end']+30)+'</small>' for x in r['overlapping_ai']) or '출력 없음'
  timing=('시작 '+str(r['start_error_seconds'])+'초 / 끝 '+str(r['end_error_seconds'])+'초') if 'start_error_seconds' in r else '동종 후보 없음'
  tr.append(f'<tr><td>{clock(r["source_start"])}–{clock(r["source_end"])}</td><td>{html.escape(r["text"])}</td><td>{found}</td><td><b>{r["status_ko"]}</b><br><small>{timing}</small></td><td><button onclick="seek({r["start"]})">비교 재생</button></td></tr>')
 extra=''.join(f'<tr><td>{clock(e["start"]+30)}–{clock(e["end"]+30)}</td><td>{html.escape(show(e))}</td><td>{e["score"]:.3f}</td></tr>' for e in events)
 report='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>실제 AI 효과음 인식 비교 결과</title><link rel="stylesheet" href="styles.css"><style>.stats{display:flex;gap:18px;flex-wrap:wrap}.stats p{margin:0}.stats strong{font-size:28px;display:block}.ref{background:#edf4ef;color:#17382c;font-size:20px;padding:14px}.ai{background:#17282e;color:white;font-size:20px;padding:14px;min-height:65px}td{vertical-align:top}.scroll table{min-width:850px}details{margin:20px 0}summary{cursor:pointer}</style><main><p><a href="index.html">영화 소리 시간표로 돌아가기</a></p><h1>AI가 실제 영화 소리를 찾아냈을까요?</h1><p>Big Buck Bunny · 원본 00:30~01:30 · 같은 영화 파일의 소리를 AST 모델로 실제 분석했습니다. 참고 자막을 모델에 입력하지 않았습니다.</p><section><h2>__HEADLINE__</h2><div class="stats">__STATS__</div><p>__NOTE__</p><p>같은 종류가 겹치고 시작·끝이 모두 참고 자막의 ±1초 안에 든 구간: <b>__TIMING__개</b>.</p></section><section><video id="comparisonVideo" controls playsinline preload="metadata" src="assets/movie-clip.mp4"></video><div class="ref" id="referenceCaption">참고 자막: 재생하면 표시됩니다.</div><div class="ai" id="aiCaption">AI 출력: 재생하면 표시됩니다.</div><p id="comparisonPosition">원본 영화 00:30.000 · 구간 00:00.000</p><small>위는 공개 접근성 자막, 아래는 이번 AI의 실제 출력입니다. 두 결과를 섞어 수정하지 않았습니다.</small></section><section><h2>11개 참고 구간과 AI 출력 비교</h2><div class="scroll"><table><thead><tr><th>참고 자막의 원본 시간</th><th>참고 소리 설명</th><th>같은 구간의 AI 출력</th><th>판정 / 시각 오차</th><th>확인</th></tr></thead><tbody id="comparisonRows">__ROWS__</tbody></table></div><p>‘다른 종류로 분류’는 참고 자막과 이름이 다르다는 뜻입니다. 동시에 다른 소리가 있을 수 있으므로 청취 검수 없이 오탐이라고 확정하지 않습니다. 참고 자막도 모든 소리를 적은 정답표는 아닙니다.</p><p><a href="data/ai-comparison.csv" download>비교표 CSV 저장</a> · <a href="data/ai-raw-result.json">전체 AI 원본 결과</a> · <a href="data/ai-comparison.json">비교 근거 JSON</a> · <a href="docs/ai-evaluation.md">팀 공유용 결과 설명</a></p></section><section><h2>AI가 출력한 전체 후보</h2><p>음악을 포함한 전체 출력입니다. 참고 자막에 없는 후보는 별도의 청취 확인이 필요합니다.</p><div class="scroll"><table><thead><tr><th>원본 영화 시간</th><th>AI 소리 분류</th><th>모델 점수</th></tr></thead><tbody>__AIROWS__</tbody></table></div></section><section><h2>이번 시험에서 알 수 있는 범위</h2><ul><li>모델: AST / AudioSet. 2초 길이로 분석하고 1초씩 이동했습니다. 각 구간의 최상위 분류가 0.24 이상일 때 후보를 남겼습니다.</li><li>배경음악이 최상위로 나오면 겹친 효과음을 놓칠 수 있습니다. 하품은 이 모델에 독립 분류 항목이 없습니다.</li><li>같은 종류의 AI 후보와 참고 자막이 0.1초 이상 겹치면 유형 감지로 기록했습니다. 동일 소리 종류를 먼저 정하고 비교했으며, 결과를 맞추려고 점수 기준을 낮추지 않았습니다.</li><li>모델 점수는 정답 확률이 아닙니다. 이 결과로 전체 영화나 다른 모델의 성능을 단정할 수 없습니다.</li><li>참고 자막은 사람의 독립 청취 검수를 마친 정답표가 아닙니다. 최종 접근성 자막으로 사용하기 전 검수가 필요합니다.</li></ul><details><summary>실행 정보</summary><pre>__INFO__</pre></details><p>영화 © 2008 Blender Foundation / www.bigbuckbunny.org · <a href="https://peach.blender.org/about/">CC BY 3.0</a>. 참고 소리 자막: <a href="https://github.com/demuxed/big-buck-captions">Demuxed / Big Buck Captions</a>, CC BY 3.0.</p></section></main><script>const reference=__REF__,ai=__AI__;const player=document.querySelector('#comparisonVideo');function clock(t){const n=Math.round(t*1000);return String(Math.floor(n/60000)).padStart(2,'0')+':'+String(Math.floor(n%60000/1000)).padStart(2,'0')+'.'+String(n%1000).padStart(3,'0')}function update(){const t=player.currentTime;document.querySelector('#referenceCaption').textContent='참고 자막: '+(reference.filter(e=>t>=e.start&&t<e.end).map(e=>'['+e.text+']').join(' · ')||'표시 없음');document.querySelector('#aiCaption').textContent='AI 출력: '+(ai.filter(e=>t>=e.start&&t<e.end).map(e=>'['+e.text_ko+']').join(' · ')||'후보 없음');document.querySelector('#comparisonPosition').textContent='원본 영화 '+clock(t+30)+' · 구간 '+clock(t)}function seek(t){player.currentTime=t;player.play().catch(()=>{});player.scrollIntoView({behavior:'smooth',block:'center'});update()}player.addEventListener('timeupdate',update);</script></html>'''
 stats=''.join(f'<p><strong>{counts[k]}</strong>{STATUS[k]}</p>' for k in STATUS)
 info=json.dumps({k:result[k] for k in ['model','duration','elapsed_seconds','input_sha256']},ensure_ascii=False,indent=2)
 values={'__HEADLINE__':headline,'__STATS__':stats,'__NOTE__':'이번 AI 출력: 음악 '+str(sum(e['label']=='Music' for e in events))+'개 구간, 효과음 후보 '+str(sum(e['label']!='Music' for e in events))+'개. '+note,'__TIMING__':str(result['timing_within_1s_count']),'__ROWS__':''.join(tr),'__AIROWS__':extra,'__INFO__':html.escape(info),'__REF__':json.dumps(refs['events'],ensure_ascii=False).replace('<','\\u003c'),'__AI__':json.dumps([dict(e,text_ko=show(e)) for e in events],ensure_ascii=False).replace('<','\\u003c')}
 for key,val in values.items():report=report.replace(key,val)
 (ROOT/'evaluation.html').write_text(report,encoding='utf-8')
 summary=f'<section id="ai-evaluation-summary"><h2>같은 영화를 AI로 분석한 결과</h2><p><b>{headline}</b></p><p>'+ ' · '.join(f'{STATUS[k]} {counts[k]}개' for k in STATUS)+'</p><p><a href="evaluation.html"><b>AI가 맞힌 소리·놓친 소리·다르게 분류한 소리 비교 보기 →</b></a></p><small>자동 인식 시험 결과입니다. 아래 영상의 자막은 비교용 기존 자막입니다.</small></section>'
 index=(ROOT/'index.html').read_text(encoding='utf-8')
 import re
 index=re.sub(r'<section id="ai-evaluation-summary">.*?</section>','',index,flags=re.S)
 index=index.replace('<section><video',summary+'<section><video',1)
 (ROOT/'index.html').write_text(index,encoding='utf-8')
 md=f'# 실제 AI 효과음 인식 시험 결과\n\n{headline}\n\n'
 md+='\n'.join(f'- {STATUS[k]}: {counts[k]}개' for k in STATUS)+f'\n- 같은 종류이며 양 끝 시각이 참고 자막의 ±1초 안: {result["timing_within_1s_count"]}개\n\n'
 md+='## 시험 방법\n\n공개 영화 Big Buck Bunny의 원본 00:30~01:30 구간을 기존 AST 모델로 실제 분석했습니다. 참고 자막은 모델 입력에 넣지 않았습니다. 실행 후 Demuxed의 공개 접근성 자막 11개 구간과 비교했습니다. 같은 파일인지 SHA-256으로 검증했습니다.\n\n'+note+'\n\n'
 md+='| 원본 시간 | 참고 소리 | 같은 구간의 AI 출력 | 비교 결과 |\n|---|---|---|---|\n'
 for r in rows:md+=f'| {clock(r["source_start"])}~{clock(r["source_end"])} | {r["text"]} | '+(' / '.join(x['text_ko'] for x in r['overlapping_ai']) or '없음')+f' | {r["status_ko"]} |\n'
 md+='\n## 팀에 설명할 내용\n\n“같은 영화 1분을 AI에 넣어 효과음과 발생 시간을 추출하고, 공개 접근성 자막과 비교했습니다. '+headline+' 배경음악과 겹친 효과음, 이 모델에 분류 항목이 없는 하품 등이 한계입니다. 기존 자막에 적힌 소리를 AI가 인식한 것처럼 제시하지 않았습니다. 정답률 80%를 달성했다고 말할 근거는 아직 없습니다.”\n\n'
 md+='## 재현과 원자료\n\n- [실제 AI 원본 출력](../data/ai-raw-result.json) — 모든 분석 창의 상위 5개 분류도 보존합니다. 비교 판정에는 실제로 출력한 최상위 후보만 사용합니다.\n- [비교표](../data/ai-comparison.csv), [고정 비교 규칙](../evaluation/comparison-rules.json), [분석 코드](../evaluation/analyze.py), [비교 코드](../evaluation/compare.py)\n- [참고 자막 출처](https://github.com/demuxed/big-buck-captions/blob/main/big-buck-bunny.srt)\n\n참고 자막은 불완전한 비교 자료이며 독립 청취 정답표가 아닙니다. 따라서 ‘다른 분류’를 오탐으로 확정하지 않고, 정밀도·재현율을 계산하지 않았습니다.\n'
 (ROOT/'docs/ai-evaluation.md').write_text(md,encoding='utf-8')
 print(json.dumps({k:result[k] for k in ['counts','ai_event_count','timing_within_1s_count','elapsed_seconds']},ensure_ascii=False,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('raw_result');main(p.parse_args().raw_result)
