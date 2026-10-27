# 소리모이 · 영화 속 소리 시간표

기존 영화 **Big Buck Bunny의 원본 00:30~01:30** 구간에서 어떤 소리가 언제 나는지 한국어 설명으로 보여주는 1분 자료입니다.

**[웹페이지 열기](https://tweetyseoul1.github.io/sorimoi-movie-sound-captions/)**

## 실제 AI 인식 시험 결과

**[AI 결과와 참고 자막 비교 보기](https://tweetyseoul1.github.io/sorimoi-movie-sound-captions/evaluation.html)**

같은 영화 파일을 AST 모델에 실제로 입력했습니다. 참고 자막을 모델에 주지 않고 분석한 뒤 비교했습니다.

- AI의 최종 출력: **음악 5개 구간**, 효과음 후보 0개.
- 참고 자막 11개 구간 중 같은 소리 종류가 겹친 구간: **0개**.
- 10개 구간은 해당 효과음 후보가 없었습니다. 하품 1개 구간은 모델에 독립 분류 항목이 없습니다.
- **현재 모델과 설정으로는 이 장면의 배경음악과 겹친 효과음 확인에 충분하지 않았습니다.** 모든 AI가 효과음을 인식할 수 없다는 뜻은 아닙니다.

이는 공개 자막과의 구간별 비교이며 정답률·정밀도·재현율이 아닙니다. 자막 자료 자체도 독립 청취 검수를 마친 완전한 정답표가 아닙니다. [팀 공유용 결과 설명](docs/ai-evaluation.md), [CSV 비교표](data/ai-comparison.csv), [AI 전체 원본 출력](data/ai-raw-result.json)을 함께 보존했습니다.

## 보는 방법

1. 웹페이지에서 영상을 재생합니다. 해당 시간에 한국어 소리 설명이 표시됩니다.
2. 표의 **이 부분 보기**를 누르면 그 장면으로 이동합니다.
3. **원본 영화 시간**과 **1분 구간의 시간**을 비교합니다. 구간 시간에 30초를 더하면 원본 시간이 됩니다.
4. 시간표 CSV 또는 자막 SRT를 내려받을 수 있습니다.

화면의 설명은 코 고는 소리, 킁킁거림, 귀가 펴지는 소리, 하품, 목의 뚝 소리, 한숨, 사과가 떨어지는 소리 등 11개 표시 구간입니다. 전체화면에서는 영상 플레이어의 한국어 자막을 선택하거나 [자막이 영상에 포함된 MP4](assets/movie-captioned.mp4)를 이용하세요.

## 이 자료가 의미하는 것

기본 시간표와 영상에 들어간 한국어 자막은 **공개 접근성 자막을 번역한 비교용 자료**입니다. 별도 비교 페이지는 **이번에 실제 실행한 AI 출력**을 보여줍니다. 두 결과를 섞어 AI가 효과음을 인식한 것처럼 표시하지 않았습니다. 직접 청취 검수나 당사자 사용성 검증을 마친 최종 자막은 아닙니다.

원본 소리 설명과 표시 시각은 [Demuxed의 Big Buck Captions](https://github.com/demuxed/big-buck-captions/blob/main/big-buck-bunny.srt)를 근거로 합니다. 첫 코 고는 소리는 선택한 구간 이전인 원본 00:29.416부터 이어져서, 1분 영상에서는 00:00부터 표시됩니다.

## 파일

| 파일 | 용도 |
|---|---|
| `index.html`, `styles.css`, `app.js` | 영화 재생과 소리 시간표 웹페이지 |
| `evaluation.html` | AI 출력과 참고 자막을 동시에 보고 비교하는 화면 |
| `data/ai-raw-result.json` | 실제 모델 출력과 모든 분석 창의 상위 5개 분류 |
| `data/ai-comparison.json`, `data/ai-comparison.csv` | 고정 규칙에 따른 구간별 비교 결과 |
| `evaluation/` | 분석 코드, 비교 규칙, 재현 방법과 실행 환경 |
| `assets/movie-clip.mp4` | 원본 영화의 1분 발췌 영상 |
| `assets/movie-captioned.mp4` | 한국어 소리 설명이 영상에 포함된 파일 |
| `data/sound-timeline.csv` | 원본·구간 시간과 소리 설명 |
| `data/captions-ko.srt`, `data/captions-ko.vtt` | 1분 영상에 맞춘 한국어 자막 |
| `data/caption-sources.json` | 출처와 원본·구간 시간 데이터 |
| `docs/sound-timeline.md` | 글로 읽는 전체 시간표 |

## PC에서 열기

GitHub의 **Code → Download ZIP**으로 받아 압축을 풀고 `index.html`을 여세요. 영화와 화면 아래의 소리 설명은 인터넷 없이도 볼 수 있습니다. 브라우저가 로컬 VTT 자막을 제한하면 자막 포함 MP4를 사용하세요.

개발용으로는 폴더에서 `python -m http.server 8000`을 실행하고 `http://localhost:8000`을 열면 됩니다. 별도 패키지 설치나 API 키가 필요하지 않습니다.

## 출처 및 이용 조건

- 영화: © 2008 Blender Foundation / www.bigbuckbunny.org, **CC BY 3.0**. [공식 안내](https://peach.blender.org/about/), [원본 영상](https://media.w3.org/2010/05/bunny/movie.mp4).
- 접근성 자막: **Demuxed / Big Buck Captions, CC BY 3.0**. [프로젝트 및 라이선스](https://github.com/demuxed/big-buck-captions#license).
- 변경: 원본 00:30~01:30 발췌·재인코딩, 소리 자막 한국어 번역, 시간 기준 변환, 자막 삽입본 제작. 영화 속 소리를 새로 추가하지 않았습니다.
- [라이선스와 출처 상세](LICENSE.md).
