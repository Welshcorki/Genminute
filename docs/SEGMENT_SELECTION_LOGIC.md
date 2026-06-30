# 세그먼트 선택 로직 상세 문서

## 개요

NoteDetail 페이지에서 오디오 재생 중 세그먼트 선택 로직의 동작 방식과 개선 방안을 설명합니다.

## 문제 상황

### 기존 문제점

1. **세그먼트 클릭 시 전체가 선택되는 문제**
   - 사용자가 특정 세그먼트를 클릭해도 `handleTimeUpdate`가 실행되면서 다른 세그먼트로 덮어쓰는 현상

2. **재생바 클릭 시 세그먼트 동기화 문제**
   - 재생바를 클릭해도 해당 시간의 세그먼트가 선택되지 않거나, 잘못된 세그먼트가 선택됨

3. **자동 선택 로직의 과도한 실행**
   - `timeupdate` 이벤트마다 "가장 가까운 세그먼트"를 찾는 로직이 실행되어 사용자 선택을 방해

## 해결 방안

### 방안 1: 사용자 선택 우선 로직

사용자가 명시적으로 선택한 세그먼트를 추적하고, 자동 선택 로직보다 우선시합니다.

#### 구현 방식

```typescript
// 사용자가 명시적으로 선택한 세그먼트 추적
const [userSelectedSegmentId, setUserSelectedSegmentId] = useState<number | null>(null);

// 세그먼트 클릭 시
const handleSegmentClick = (segment: TranscriptSegment) => {
  setUserSelectedSegmentId(segment.id);  // 사용자 선택 표시
  setActiveSegmentId(segment.id);
  // ...
};

// 재생바 클릭 시
const handleProgressChange = (newTime: number) => {
  // 해당 시간의 세그먼트를 찾아서 사용자 선택으로 표시
  const activeSegment = meeting.transcript.find(
    seg => newTime >= seg.start_time && newTime < seg.end_time
  );
  if (activeSegment) {
    setUserSelectedSegmentId(activeSegment.id);
    setActiveSegmentId(activeSegment.id);
  }
  // ...
};

// handleTimeUpdate에서
const handleTimeUpdate = () => {
  // 1. 사용자가 명시적으로 선택한 세그먼트가 있고,
  //    현재 시간이 그 세그먼트 범위에 있으면 유지
  if (userSelectedSegmentId) {
    const userSelectedSegment = meeting.transcript.find(
      seg => seg.id === userSelectedSegmentId
    );
    if (userSelectedSegment && 
        audio.currentTime >= userSelectedSegment.start_time && 
        audio.currentTime < userSelectedSegment.end_time) {
      setActiveSegmentId(userSelectedSegmentId);
      return;  // 다른 로직 실행 안 함
    }
  }
  
  // 2. 사용자 선택 범위를 벗어났으면 자동 선택 로직 실행
  // ...
};
```

#### 동작 흐름

```
사용자가 세그먼트 클릭
    ↓
userSelectedSegmentId 설정
    ↓
오디오 재생 시작
    ↓
timeupdate 이벤트 발생
    ↓
현재 시간이 사용자 선택 세그먼트 범위 내?
    ├─ YES → 사용자 선택 세그먼트 유지 ✅
    └─ NO → 사용자 선택 해제 후 자동 선택 로직 실행
```

### 방안 2: 조건부 "가장 가까운 세그먼트" 로직

현재 시간이 모든 세그먼트 범위에서 충분히 멀리 떨어져 있을 때만 "가장 가까운 세그먼트"를 찾습니다.

#### 거리 계산 함수

```typescript
/**
 * 현재 시간과 세그먼트 사이의 최소 거리를 계산합니다.
 * 
 * @param currentTime 현재 재생 시간 (초)
 * @param segment 세그먼트 객체
 * @returns 거리 (초). 범위 내에 있으면 0, 범위 앞이면 양수, 범위 뒤면 양수
 */
const calculateDistance = (currentTime: number, segment: TranscriptSegment): number => {
  // 세그먼트 범위 내에 있으면 거리 0
  if (currentTime >= segment.start_time && currentTime < segment.end_time) {
    return 0;
  }
  
  // 범위 앞에 있으면 (start_time - currentTime)
  if (currentTime < segment.start_time) {
    return segment.start_time - currentTime;
  }
  
  // 범위 뒤에 있으면 (currentTime - end_time)
  return currentTime - segment.end_time;
};
```

#### 임계값 설정

```typescript
// 임계값: 이 거리 이상 떨어져 있어야 "충분히 멀리 떨어져 있다"고 판단
const DISTANCE_THRESHOLD = 2.0; // 2초

// 모든 세그먼트와의 최소 거리가 임계값보다 큰지 확인
const minDistance = Math.min(
  ...meeting.transcript.map(seg => calculateDistance(audio.currentTime, seg))
);

if (minDistance >= DISTANCE_THRESHOLD) {
  // ✅ 충분히 멀리 떨어져 있을 때만 가장 가까운 세그먼트 찾기
  // ...
} else {
  // ⚠️ 가까이 있으면 아무것도 하지 않음 (사용자가 선택한 세그먼트 유지)
}
```

#### 시각적 예시

```
세그먼트 1: [====0초====5초====]
세그먼트 2: [====5초====10초====]
세그먼트 3: [====10초====15초====]

임계값: 2초

시나리오 1: 현재 시간 = 6초
├─ 세그먼트 2 범위 내 (5초 ~ 10초)
├─ 거리: 0초
└─ ✅ 세그먼트 2 선택

시나리오 2: 현재 시간 = 4.8초
├─ 세그먼트 1 범위 밖 (4.8 < 5.0)
├─ 세그먼트 1과의 거리: 0.2초 (임계값 2초 미만)
├─ 세그먼트 2와의 거리: 0.2초 (임계값 2초 미만)
└─ ❌ "가장 가까운 세그먼트" 로직 실행 안 함
   → 사용자가 선택한 세그먼트 유지

시나리오 3: 현재 시간 = 50초
├─ 모든 세그먼트 범위 밖
├─ 가장 가까운 세그먼트(세그먼트 3)와의 거리: 35초 (임계값 2초 초과)
└─ ✅ "가장 가까운 세그먼트" 로직 실행
   → 세그먼트 3 선택

시나리오 4: 현재 시간 = 12초
├─ 세그먼트 3 범위 내 (10초 ~ 15초)
├─ 거리: 0초
└─ ✅ 세그먼트 3 선택
```

#### 임계값 조정 옵션

```typescript
// 옵션 1: 고정 임계값
const DISTANCE_THRESHOLD = 2.0; // 2초

// 옵션 2: 세그먼트 길이 기반 동적 임계값
const avgSegmentLength = meeting.transcript.reduce(
  (sum, seg) => sum + (seg.end_time - seg.start_time), 0
) / meeting.transcript.length;
const DISTANCE_THRESHOLD = avgSegmentLength * 0.5; // 평균 길이의 50%

// 옵션 3: 최소 세그먼트 길이 기반
const minSegmentLength = Math.min(
  ...meeting.transcript.map(seg => seg.end_time - seg.start_time)
);
const DISTANCE_THRESHOLD = minSegmentLength * 0.3; // 최소 길이의 30%
```

## 통합 로직

### 전체 흐름도

```
오디오 재생 중 timeupdate 이벤트 발생
    ↓
현재 시간 업데이트
    ↓
사용자가 명시적으로 선택한 세그먼트가 있는가?
    ├─ YES → 현재 시간이 그 세그먼트 범위 내?
    │   ├─ YES → 사용자 선택 세그먼트 유지 ✅
    │   └─ NO → 사용자 선택 해제 후 자동 선택 로직으로
    └─ NO → 자동 선택 로직으로
        ↓
    현재 시간이 어떤 세그먼트 범위 내에 있는가?
        ├─ YES → 해당 세그먼트 선택 ✅
        └─ NO → 모든 세그먼트와의 거리 계산
            ↓
        최소 거리 >= 임계값?
            ├─ YES → 가장 가까운 세그먼트 선택 ✅
            └─ NO → 아무것도 하지 않음 (기존 선택 유지) ⏸️
```

### 코드 구조

```typescript
// 상태 관리
const [activeSegmentId, setActiveSegmentId] = useState<number | null>(null);
const [userSelectedSegmentId, setUserSelectedSegmentId] = useState<number | null>(null);

// 거리 계산 함수
const calculateDistance = (currentTime: number, segment: TranscriptSegment): number => {
  // ...
};

// 세그먼트 클릭 핸들러
const handleSegmentClick = (segment: TranscriptSegment) => {
  setUserSelectedSegmentId(segment.id);
  setActiveSegmentId(segment.id);
  // ...
};

// 재생바 클릭 핸들러
const handleProgressChange = (newTime: number) => {
  // 해당 시간의 세그먼트 찾기
  const activeSegment = meeting.transcript.find(
    seg => newTime >= seg.start_time && newTime < seg.end_time
  );
  if (activeSegment) {
    setUserSelectedSegmentId(activeSegment.id);
    setActiveSegmentId(activeSegment.id);
  }
  // ...
};

// 시간 업데이트 핸들러
const handleTimeUpdate = () => {
  setCurrentTime(audio.currentTime);
  
  // 1. 사용자 선택 우선 처리
  if (userSelectedSegmentId) {
    const userSelectedSegment = meeting.transcript.find(
      seg => seg.id === userSelectedSegmentId
    );
    if (userSelectedSegment && 
        audio.currentTime >= userSelectedSegment.start_time && 
        audio.currentTime < userSelectedSegment.end_time) {
      setActiveSegmentId(userSelectedSegmentId);
      return;
    } else {
      // 사용자 선택 범위를 벗어났으면 해제
      setUserSelectedSegmentId(null);
    }
  }
  
  // 2. 자동 선택 로직
  if (meeting?.transcript) {
    const activeSegment = meeting.transcript.find(
      seg => audio.currentTime >= seg.start_time && audio.currentTime < seg.end_time
    );
    
    if (activeSegment) {
      setActiveSegmentId(activeSegment.id);
    } else {
      // 3. 조건부 "가장 가까운 세그먼트" 로직
      const minDistance = Math.min(
        ...meeting.transcript.map(seg => calculateDistance(audio.currentTime, seg))
      );
      
      if (minDistance >= DISTANCE_THRESHOLD) {
        const closestSegment = meeting.transcript.reduce((closest, seg) => {
          if (!closest) return seg;
          const closestDist = calculateDistance(audio.currentTime, closest);
          const segDist = calculateDistance(audio.currentTime, seg);
          return segDist < closestDist ? seg : closest;
        }, null as TranscriptSegment | null);
        
        if (closestSegment) {
          setActiveSegmentId(closestSegment.id);
        }
      }
      // minDistance < DISTANCE_THRESHOLD인 경우 아무것도 하지 않음
    }
  }
};
```

## 장점

1. **사용자 선택 보존**: 사용자가 명시적으로 선택한 세그먼트가 우선적으로 유지됨
2. **명확한 범위 처리**: 세그먼트 범위 내에서는 정확한 세그먼트가 선택됨
3. **과도한 자동 선택 방지**: 세그먼트 근처에서는 자동 선택을 하지 않아 사용자 경험 개선
4. **멀리 떨어진 경우 처리**: 모든 세그먼트에서 충분히 멀리 떨어져 있을 때만 가장 가까운 세그먼트 선택

## 테스트 시나리오

### 시나리오 1: 세그먼트 클릭
1. 사용자가 세그먼트 2 클릭
2. 오디오가 세그먼트 2의 시작 시간으로 이동
3. 재생 시작
4. **기대 결과**: 세그먼트 2가 선택된 상태로 유지

### 시나리오 2: 재생바 클릭
1. 사용자가 재생바의 7초 지점 클릭
2. 오디오가 7초로 이동
3. **기대 결과**: 세그먼트 2 (5초 ~ 10초 범위)가 선택됨

### 시나리오 3: 재생 중 자동 선택
1. 오디오가 재생 중
2. 현재 시간이 세그먼트 범위를 넘어감
3. **기대 결과**: 
   - 다음 세그먼트 범위에 들어가면 해당 세그먼트 선택
   - 세그먼트 사이의 간격이 작으면 (임계값 미만) 기존 선택 유지
   - 세그먼트 사이의 간격이 크면 (임계값 이상) 가장 가까운 세그먼트 선택

### 시나리오 4: 사용자 선택 범위 벗어남
1. 사용자가 세그먼트 2 클릭
2. 오디오가 재생되면서 세그먼트 2 범위를 벗어남
3. **기대 결과**: 
   - 세그먼트 2 범위 내에서는 세그먼트 2 유지
   - 범위를 벗어나면 사용자 선택 해제 후 자동 선택 로직 실행

## 참고사항

- `timeupdate` 이벤트는 약 250ms마다 발생하므로, 로직이 너무 자주 실행되지 않도록 주의
- 임계값은 실제 사용 패턴에 따라 조정 가능
- 사용자 선택은 오디오 재생이 멈추거나 다른 세그먼트를 클릭할 때까지 유지됨

