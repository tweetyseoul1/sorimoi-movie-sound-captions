# 소리모이 · 영화 속 소리 시간표

기존 영화 **Big Buck Bunny의 원본 00:30~01:30** 구간에서 어떤 소리가 언제 나는지 한국어 설명으로 보여주는 1분 자료입니다.

**[웹페이지 열기](https://tweetyseoul1.github.io/sorimoi-movie-sound-captions/)**

## 보는 방법

1. 웹페이지에서 영상을 재생합니다. 해당 시간에 한국어 소리 설명이 표시됩니다.
2. 표의 **이 부분 보기**를 누르면 그 장면으로 이동합니다.
3. **원본 영화 시간**과 **1분 구간의 시간**을 비교합니다. 구간 시간에 30초를 더하면 원본 시간이 됩니다.
4. 시간표 CSV 또는 자막 SRT를 내려받을 수 있습니다.

화면의 설명은 코 고는 소리, 킁킁거림, 귀가 펴지는 소리, 하품, 목의 뚝 소리, 한숨, 사과가 떨어지는 소리 등 11개 표시 구간입니다. 전체화면에서는 영상 플레이어의 한국어 자막을 선택하거나 [자막이 영상에 포함된 MP4](assets/movie-captioned.mp4)를 이용하세요.

## 이 자료가 의미하는 것

**공개 접근성 자막을 한국어로 번역하고 시간을 정리한 자료입니다.** AI가 영화의 모든 소리를 자동 탐지한 결과가 아니며, 별도의 직접 청취 검수나 당사자 사용성 검증을 마친 결과도 아닙니다. 배경에 있는 모든 작은 소리를 빠짐없이 기록하지는 않습니다.

원본 소리 설명과 표시 시각은 [Demuxed의 Big Buck Captions](https://github.com/demuxed/big-buck-captions/blob/main/big-buck-bunny.srt)를 근거로 합니다. 첫 코 고는 소리는 선택한 구간 이전인 원본 00:29.416부터 이어져서, 1분 영상에서는 00:00부터 표시됩니다.

## 파일

| 파일 | 용도 |
|---|---|
| `index.html`, `styles.css`, `app.js` | 영화 재생과 소리 시간표 웹페이지 |
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
