"""Local sound-event candidate checker. Uses existing OnSori AST weights read-only."""
import argparse, csv, hashlib, json, math, os, sys, time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1'
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
import numpy as np
import av

ROOT = Path(__file__).resolve().parent
SR = 16000
MODEL_ID = 'MIT/ast-finetuned-audioset-10-10-0.4593'
REVISION = 'f826b80d28226b62986cc218e5cec390b1096902'
MODEL_SUBPATH = Path('models/huggingface/hub/models--MIT--ast-finetuned-audioset-10-10-0.4593/snapshots')/REVISION
MODEL_ROOTS = [Path(sys.prefix).parent, Path(os.environ.get('LOCALAPPDATA',''))/'OnSori']
MODEL_PATH = next((p/MODEL_SUBPATH for p in MODEL_ROOTS if (p/MODEL_SUBPATH/'model.safetensors').is_file()), MODEL_ROOTS[0]/MODEL_SUBPATH)
LABELS = {
 'Dog':'개 소리','Bark':'개 짖는 소리','Bow-wow':'개 짖는 소리','Whimper (dog)':'개가 낑낑거리는 소리',
 'Cat':'고양이 소리','Meow':'고양이 울음소리','Purr':'고양이 가르랑 소리',
 'Rain':'빗소리','Raindrop':'빗방울 소리','Rain on surface':'바닥에 떨어지는 빗소리','Thunder':'천둥 소리',
 'Knock':'두드리는 소리','Tap':'톡톡 치는 소리','Door':'문 소리','Slam':'쾅 닫히는 소리','Creak':'삐걱거리는 소리',
 'Clapping':'박수 소리','Applause':'박수갈채','Finger snapping':'손가락 튕기는 소리',
 'Sneeze':'재채기 소리','Cough':'기침 소리','Throat clearing':'목 가다듬는 소리','Sniff':'코 훌쩍이는 소리',
 'Alarm':'알람 소리','Alarm clock':'알람시계 소리','Buzzer':'버저 소리','Beep, bleep':'삐 소리','Ringtone':'벨소리','Telephone bell ringing':'전화벨 소리','Bell':'종소리',
 'Laughter':'웃음소리','Chuckle, chortle':'작게 웃는 소리','Giggle':'킥킥 웃는 소리','Crying, sobbing':'우는 소리','Baby cry, infant cry':'아기 울음소리',
 'Footsteps':'발걸음 소리','Walk, footsteps':'발걸음 소리','Running':'달리는 소리','Keys jangling':'열쇠 달그락 소리',
 'Typing':'타자 소리','Computer keyboard':'키보드 소리','Clicking':'딸깍 소리','Clock':'시계 소리','Tick':'똑딱 소리','Tick-tock':'시계 똑딱 소리',
 'Glass':'유리 소리','Shatter':'깨지는 소리','Water':'물소리','Water tap, faucet':'수돗물 소리','Stream':'시냇물 소리','Waves, surf':'파도 소리','Wind':'바람 소리',
 'Car':'자동차 소리','Vehicle horn, car horn, honking':'자동차 경적','Siren':'사이렌 소리','Engine':'엔진 소리','Bird vocalization, bird call, bird song':'새소리',
 'Whistling':'휘파람 소리','Whistle':'호루라기 소리','Music':'음악','Speech':'말소리','Conversation':'대화 소리','Narration, monologue':'말소리',
 'Explosion':'폭발음 계열','Eruption':'분출음 계열','Bang':'쾅 하는 충격음','Boom':'쿵 울리는 소리','Thunderstorm':'뇌우 소리',
 'Scissors':'가위 소리 후보','Crunch':'바삭·바스락 소리 후보','Biting':'베어 무는 소리로 분류','Chewing, mastication':'씹는 소리로 분류','Tearing':'찢는 소리 후보',
 'Silence':'무음','Noise':'잡음','White noise':'백색 잡음','Static':'지직거리는 소리',
}
BACKGROUND = {'Speech','Conversation','Narration, monologue','Silence'}

def load_audio(path, limit=1200):
    chunks=[]
    with av.open(str(path)) as container:
        streams=[s for s in container.streams if s.type=='audio']
        if not streams: raise ValueError('소리가 들어 있는 파일을 선택해 주세요.')
        # Preserve channels while resampling, then average explicitly. FFmpeg's
        # default stereo-to-mono matrix can amplify identical channels by sqrt(2).
        resampler=av.AudioResampler(format='fltp',rate=SR)
        count=0
        for frame in container.decode(streams[0]):
            for out in resampler.resample(frame):
                x=out.to_ndarray().mean(axis=0).astype(np.float32)
                chunks.append(x); count+=len(x)
            if count > (limit+1)*SR:
                raise ValueError(f'{limit/60:g}분 이하 영상 또는 음원을 선택해 주세요. 긴 파일을 몰래 잘라 분석하지 않습니다.')
        for out in resampler.resample(None): chunks.append(out.to_ndarray().mean(axis=0).astype(np.float32))
    if not chunks: raise ValueError('읽을 수 있는 소리가 없습니다.')
    audio=np.concatenate(chunks)
    if len(audio)>int((limit+.05)*SR): raise ValueError(f'{limit/60:g}분 이하 파일만 분석할 수 있습니다.')
    if len(audio)<int(.2*SR): raise ValueError('0.2초 이상 파일을 선택해 주세요.')
    if not np.isfinite(audio).all(): raise ValueError('잘못된 오디오 값이 있습니다.')
    return audio

def bounds(chunk, start, end):
    # Mixed-waveform energy is only a timing hint, never source separation.
    hop=800
    rms=np.array([np.sqrt(np.mean(chunk[i:i+hop]**2)+1e-12) for i in range(0,len(chunk),hop)])
    active=np.flatnonzero(rms >= max(10**(-55/20),rms.max()*10**(-24/20)))
    if not len(active): return start,end
    return max(start,start+active[0]*.05),min(end,start+(active[-1]+1)*.05)

def merge_events(events):
    merged=[]
    for ev in sorted(events,key=lambda e:(e['label'],e['start'])):
        if merged and ev['label']==merged[-1]['label'] and ev['start']<=merged[-1]['end']+.10:
            merged[-1]['end']=max(ev['end'],merged[-1]['end'])
            merged[-1]['score']=max(ev['score'],merged[-1]['score'])
        else: merged.append(ev.copy())
    return sorted(merged,key=lambda e:(e['start'],e['end'],e['label']))

def analyze(path, progress=lambda value,message:None, cancelled=lambda:False):
    import torch
    from transformers import ASTFeatureExtractor, ASTForAudioClassification
    t=time.perf_counter()
    audio=load_audio(path)
    duration=len(audio)/SR
    if not (MODEL_PATH/'model.safetensors').is_file():
        raise FileNotFoundError('이 PC에 준비된 온소리 AST 모델을 찾지 못했습니다. 모델을 임의로 내려받지 않았습니다.')
    progress(.02,'PC에 설치된 소리 분석 모델 준비 중')
    torch.set_num_threads(min(4,os.cpu_count() or 4))
    extractor=ASTFeatureExtractor.from_pretrained(str(MODEL_PATH),local_files_only=True)
    model=ASTForAudioClassification.from_pretrained(str(MODEL_PATH),local_files_only=True,use_safetensors=True).eval()
    windows=[]; events=[]
    starts=np.arange(0,duration,1.0)
    for i,start in enumerate(starts):
        if cancelled():raise InterruptedError('분석을 중지했습니다.')
        end=min(duration,start+2)
        chunk=audio[int(start*SR):int(end*SR)]
        db=float(20*np.log10(max(np.sqrt(np.mean(chunk**2)),1e-6)))
        record={'start':round(float(start),3),'end':round(float(end),3),'dbfs':round(db,2),'top5':[]}
        if db>=-60 and len(chunk)>=int(.2*SR):
            inputs=extractor(chunk,sampling_rate=SR,return_tensors='pt')
            with torch.inference_mode(): scores=torch.sigmoid(model(**inputs).logits[0]).cpu().numpy()
            order=np.argsort(scores)[::-1]
            record['top5']=[{'label':model.config.id2label[int(k)],'score':round(float(scores[k]),5)} for k in order[:5]]
            # Keep a single leading candidate per window, including unrecognized labels.
            # This deliberately avoids hiding false predictions by prefiltering to known demo classes.
            label=model.config.id2label[int(order[0])]; score=float(scores[order[0]])
            if score>=.24 and label not in BACKGROUND:
                a,b=bounds(chunk,float(start),float(end))
                events.append({'start':round(a,3),'end':round(b,3),'label':label,'text':LABELS.get(label,'소리 후보: '+label),'score':round(score,5),'review_status':'미검수'})
        windows.append(record)
        progress(.08+.87*(i+1)/len(starts),f'{i+1}/{len(starts)} 구간 확인 중')
    result={'title':Path(path).name,'duration':round(duration,3),'model':MODEL_ID,'revision':REVISION,'elapsed_seconds':round(time.perf_counter()-t,2),
      'parameters':{'sample_rate':SR,'window_seconds':2,'hop_seconds':1,'threshold':.24,'silence_gate_dbfs':-60,'candidate_rule':'Top-1 class per window; no prefilter to expected demo labels; sigmoid scores, not probabilities'},
      'limitations':['클립 분류 모델의 2초 창을 이용한 후보입니다. 정밀한 시작·종료 시각은 사람이 확인해야 합니다.','각 창의 대표 후보 하나만 선택하므로 동시에 나는 소리는 놓칠 수 있습니다.','점수는 모델 출력이며 정답 확률이 아닙니다.','소리 원인·장면·감정을 추측하지 않습니다. 음량으로 감정을 판단하지 않습니다.'],
      'events':merge_events(events),'windows':windows,'input_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}
    return result

def srt_time(t):
    n=round(t*1000); h,n=divmod(n,3600000); m,n=divmod(n,60000); s,ms=divmod(n,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def display_time(t):
    n=round(t*100); m,n=divmod(n,6000);s,cs=divmod(n,100)
    return f'{m:02}:{s:02}.{cs:02}'

def save_result(result, folder):
    folder=Path(folder); folder.mkdir(parents=True,exist_ok=True)
    (folder/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    with (folder/'검수표.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f); w.writerow(['시작_분초','종료_분초','시작초_추정','종료초_추정','AI_소리후보','원래분류','모델점수_정답확률아님','검수상태','사람이_확인한_소리','수정시작초','수정종료초','비고'])
        for e in result['events']: w.writerow([display_time(e['start']),display_time(e['end']),e['start'],e['end'],e['text'],e['label'],e['score'],'미검수','','','',''])
    srt='\n\n'.join(f"{i+1}\n{srt_time(e['start'])} --> {srt_time(e['end'])}\n[미검수 후보: {e['text']}]" for i,e in enumerate(result['events']))
    (folder/'AI후보_미검수.srt').write_text(srt+'\n',encoding='utf-8-sig')
    cues=[{'id':f'sound-{i+1}','start':e['start'],'end':e['end'],'text':'[검수 필요] '+e['text'],'kind':'music' if e['label']=='Music' else 'sound','dbfs':None,'relative_db':None,'scale':1,'confidence':e['score'],'source':'AST/AudioSet; independent checker','review_required':True} for i,e in enumerate(result['events'])]
    doc={'schema_version':'1.0','video_id':result.get('video_id'),'title':result['title']+' 효과음 후보 미검수','duration':result['duration'],'cues':cues,'warnings':result['limitations'],'metadata':{'event_model':result['model'],'revision':result['revision'],'review_state':'unreviewed','source_url':result.get('source_url'),'scope':'sound candidates only; no speech transcription'}}
    (folder/'온소리_가져오기_미검수.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('file'); parser.add_argument('--out',default=str(ROOT/'results'))
    args=parser.parse_args()
    result=analyze(args.file,lambda p,m:print(f'{p:.0%} {m}',flush=True))
    save_result(result,args.out)
    print(json.dumps({'seconds':result['elapsed_seconds'],'events':result['events']},ensure_ascii=False,indent=2))
