document.addEventListener('DOMContentLoaded', () => {
    // === 탭 전환 로직 ===
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // 활성 탭 스타일 변경
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // 콘텐츠 전환
            const targetId = btn.dataset.tab;
            tabContents.forEach(c => {
                c.classList.remove('active');
                if (c.id === targetId) c.classList.add('active');
            });
        });
    });

    // === 공통 녹음 변수 ===
    let mediaRecorder = null;
    let audioChunks = [];
    let audioContext = null;
    let analyser = null;
    let dataArray = null;
    let animationId = null;
    let startTime = null;
    let timerInterval = null;
    let recordedBlob = null;

    // DOM 요소 (마이크)
    const btnStartMic = document.getElementById('btn-start-mic');
    const btnStopMic = document.getElementById('btn-stop-mic');
    const micTimer = document.getElementById('mic-timer');
    const micCanvas = document.getElementById('mic-visualizer');
    const micStatus = document.getElementById('mic-status-text');
    
    // DOM 요소 (시스템)
    const btnStartSys = document.getElementById('btn-start-sys');
    const btnStopSys = document.getElementById('btn-stop-sys');
    const sysTimer = document.getElementById('sys-timer');
    const sysCanvas = document.getElementById('sys-visualizer');
    const sysStatus = document.getElementById('sys-status-text');

    // 업로드 섹션
    const uploadSection = document.getElementById('upload-section');
    const titleInput = document.getElementById('meeting-title');
    const btnUpload = document.getElementById('btn-upload');
    const btnCancel = document.getElementById('btn-cancel');
    const audioPreview = document.getElementById('audio-preview');


    // === 녹음 시작 함수 (공통 로직) ===
    async function startRecording(stream, type) {
        try {
            audioChunks = [];
            
            let mimeType;
            if (type === 'sys') {
                // PC 시스템 녹화: 비디오 + 오디오
                // Chrome 등에서 호환성 좋은 코덱 우선순위
                const videoTypes = [
                    'video/webm;codecs=vp8,opus',
                    'video/webm;codecs=vp9,opus',
                    'video/webm'
                ];
                mimeType = videoTypes.find(t => MediaRecorder.isTypeSupported(t)) || 'video/webm';
            } else {
                // 마이크 녹음: 오디오 전용
                mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
                    ? 'audio/webm;codecs=opus' 
                    : 'audio/ogg;codecs=opus';
            }
            
            console.log(`녹화 모드: ${type}, MIME: ${mimeType}`);
            
            mediaRecorder = new MediaRecorder(stream, { mimeType });

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = () => {
                // 녹음 종료 시 처리
                stopVisualizer();
                clearInterval(timerInterval);
                
                // Blob 생성
                const blobType = mediaRecorder.mimeType; 
                recordedBlob = new Blob(audioChunks, { type: blobType });
                
                // 미리보기 설정
                const url = URL.createObjectURL(recordedBlob);
                
                // 타입에 따라 미리보기 태그 변경 (비디오/오디오)
                if (type === 'sys') {
                    // 비디오 미리보기 요소가 없다면 생성 또는 기존 오디오 태그 교체 필요
                    // 현재 UI 구조상 audio-preview를 video로 교체하거나 속성을 바꿈
                    // 간단히: 기존 audio 태그 대신 video 태그를 동적으로 생성하여 교체
                    const videoPreview = document.createElement('video');
                    videoPreview.id = 'audio-preview'; // ID 재사용
                    videoPreview.controls = true;
                    videoPreview.style.width = '100%';
                    videoPreview.style.marginTop = '1rem';
                    videoPreview.src = url;
                    
                    const oldPreview = document.getElementById('audio-preview');
                    if (oldPreview) oldPreview.replaceWith(videoPreview);
                } else {
                    // 오디오 미리보기 (원복)
                    const audioPreviewTag = document.createElement('audio');
                    audioPreviewTag.id = 'audio-preview';
                    audioPreviewTag.controls = true;
                    audioPreviewTag.style.width = '100%';
                    audioPreviewTag.style.marginTop = '1rem';
                    audioPreviewTag.src = url;

                    const oldPreview = document.getElementById('audio-preview');
                    if (oldPreview) oldPreview.replaceWith(audioPreviewTag);
                }
                
                // 업로드 UI 표시
                showUploadUI();
                
                // 스트림 트랙 모두 중지 (마이크/공유 해제)
                stream.getTracks().forEach(track => track.stop());
            };

            // 시각화 시작 (오디오 트랙이 있어야 함)
            if (stream.getAudioTracks().length > 0) {
                setupVisualizer(stream, type === 'mic' ? micCanvas : sysCanvas);
            } else {
                console.warn('오디오 트랙이 없어 시각화를 시작할 수 없습니다.');
            }
            
            // 타이머 시작
            startTimer(type === 'mic' ? micTimer : sysTimer);

            // 녹음 시작
            mediaRecorder.start(1000); // 1초마다 데이터 청크 생성

            // UI 업데이트
            updateUIState(type, true);

        } catch (err) {
            console.error('녹음 시작 실패:', err);
            alert('녹음을 시작할 수 없습니다: ' + err.message);
        }
    }

    // === 마이크 녹음 시작 ===
    btnStartMic.addEventListener('click', async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            startRecording(stream, 'mic');
        } catch (err) {
            if (err.name === 'NotAllowedError') {
                alert('마이크 권한이 거부되었습니다. 브라우저 설정에서 마이크를 허용해주세요.');
            } else {
                alert('마이크 접근 오류: ' + err.message);
            }
        }
    });

    // === 시스템 오디오(및 비디오) 녹음 시작 ===
    btnStartSys.addEventListener('click', async () => {
        try {
            // 시스템 오디오는 getDisplayMedia 사용
            const stream = await navigator.mediaDevices.getDisplayMedia({ 
                video: {
                    cursor: "never" // 마우스 커서 숨기기 시도 (브라우저 호환성 주의)
                }, 
                audio: {
                    echoCancellation: false,
                    noiseSuppression: false,
                    autoGainControl: false
                }
            });

            // 오디오 트랙 확인
            const audioTrack = stream.getAudioTracks()[0];
            if (!audioTrack) {
                alert('시스템 오디오가 공유되지 않았습니다. "시스템 오디오 공유" 체크박스를 확인해주세요.');
                stream.getTracks().forEach(track => track.stop());
                return;
            }

            // 화면 공유 중지 시 녹음도 중지되도록 이벤트 연결
            audioTrack.onended = () => {
                if (mediaRecorder && mediaRecorder.state === 'recording') {
                    mediaRecorder.stop();
                    updateUIState('sys', false);
                }
                stream.getVideoTracks().forEach(t => t.stop());
            };

            // 비디오 트랙 종료(공유 중지 버튼) 이벤트도 연결
            const videoTrack = stream.getVideoTracks()[0];
            if (videoTrack) {
                videoTrack.onended = () => {
                    if (mediaRecorder && mediaRecorder.state === 'recording') {
                        mediaRecorder.stop();
                        updateUIState('sys', false);
                    }
                };
            }

            // [변경] 비디오+오디오 스트림을 그대로 전달 (영상 녹화 포함)
            startRecording(stream, 'sys');

        } catch (err) {
            if (err.name === 'NotAllowedError') {
                // 사용자가 취소한 경우 무시
            } else {
                console.error(err);
                alert('시스템 오디오 접근 오류: ' + err.message);
            }
        }
    });

    // === 녹음 종료 ===
    btnStopMic.addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            updateUIState('mic', false);
        }
    });

    btnStopSys.addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            updateUIState('sys', false);
        }
    });

    // === UI 상태 관리 ===
    function updateUIState(type, isRecording) {
        const btnStart = type === 'mic' ? btnStartMic : btnStartSys;
        const btnStop = type === 'mic' ? btnStopMic : btnStopSys;
        const statusText = type === 'mic' ? micStatus : sysStatus;
        const wrapper = type === 'mic' ? document.querySelector('#mic-tab .recorder-card') : document.querySelector('#system-tab .recorder-card');

        if (isRecording) {
            btnStart.disabled = true;
            btnStop.disabled = false;
            statusText.textContent = '녹음 중...';
            statusText.style.color = '#e74c3c';
            wrapper.classList.add('recording');
            
            // 다른 탭 비활성화 (단순화)
            tabButtons.forEach(b => b.disabled = true);
        } else {
            btnStart.disabled = false;
            btnStop.disabled = true;
            statusText.textContent = '녹음 완료';
            statusText.style.color = '#333';
            wrapper.classList.remove('recording');
            tabButtons.forEach(b => b.disabled = false);
        }
    }

    // === 타이머 ===
    function startTimer(displayElem) {
        startTime = Date.now();
        timerInterval = setInterval(() => {
            const elapsed = Date.now() - startTime;
            const date = new Date(elapsed);
            const mm = String(date.getUTCMinutes()).padStart(2, '0');
            const ss = String(date.getUTCSeconds()).padStart(2, '0');
            const ms = String(Math.floor(date.getUTCMilliseconds() / 10)).padStart(2, '0');
            displayElem.textContent = `${mm}:${ss}:${ms}`;
        }, 50); // 50ms 갱신
    }

    // === Visualizer (파형 시각화) ===
    function setupVisualizer(stream, canvas) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContext.createMediaStreamSource(stream);
        analyser = audioContext.createAnalyser();
        
        analyser.fftSize = 2048;
        const bufferLength = analyser.frequencyBinCount;
        dataArray = new Uint8Array(bufferLength);
        
        source.connect(analyser);
        // analizer.connect(audioContext.destination); // 스피커로 소리가 다시 나면 하울링 발생하므로 연결 X

        const canvasCtx = canvas.getContext('2d');
        const width = canvas.width = canvas.offsetWidth;
        const height = canvas.height = canvas.offsetHeight;

        function draw() {
            if (!analyser) return;
            
            animationId = requestAnimationFrame(draw);
            analyser.getByteTimeDomainData(dataArray);

            canvasCtx.fillStyle = '#f8f9fa';
            canvasCtx.fillRect(0, 0, width, height);

            canvasCtx.lineWidth = 2;
            canvasCtx.strokeStyle = '#3498db';
            canvasCtx.beginPath();

            const sliceWidth = width * 1.0 / bufferLength;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const v = dataArray[i] / 128.0;
                const y = v * height / 2;

                if (i === 0) canvasCtx.moveTo(x, y);
                else canvasCtx.lineTo(x, y);

                x += sliceWidth;
            }

            canvasCtx.lineTo(canvas.width, canvas.height / 2);
            canvasCtx.stroke();
        }

        draw();
    }

    function stopVisualizer() {
        if (animationId) cancelAnimationFrame(animationId);
        if (audioContext) audioContext.close();
        audioContext = null;
        analyser = null;
    }

    // === 업로드 로직 ===
    function showUploadUI() {
        uploadSection.style.display = 'block';
        titleInput.focus();
        // 스크롤 이동
        uploadSection.scrollIntoView({ behavior: 'smooth' });
    }

    btnCancel.addEventListener('click', () => {
        if (confirm('녹음 내용을 삭제하시겠습니까?')) {
            uploadSection.style.display = 'none';
            audioChunks = [];
            recordedBlob = null;
            // 타이머 초기화
            micTimer.textContent = '00:00:00';
            sysTimer.textContent = '00:00:00';
        }
    });

    btnUpload.addEventListener('click', async () => {
        const title = titleInput.value.trim();
        if (!title) {
            alert('회의 제목을 입력해주세요.');
            return;
        }

        if (!recordedBlob) {
            alert('녹음 데이터가 없습니다.');
            return;
        }

        // 현재 활성화된 탭 확인 (파일명 접두어 결정을 위해)
        const activeTab = document.querySelector('.tab-button.active');
        const isSystemRecord = activeTab && activeTab.dataset.tab === 'system-tab';
        
        // 접두어 설정: 마이크는 'mic', 시스템(화상회의)은 'video'
        const prefix = isSystemRecord ? 'video' : 'mic';

        // 날짜/시간 포맷팅 (YYYYMMDD_HHMMSS)
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        const timestampStr = `${year}${month}${day}_${hours}${minutes}${seconds}`;

        // 제목 정제 (파일명에 쓸 수 없는 문자 제거 및 공백을 언더바(_)로 치환)
        // 허용: 한글, 영문, 숫자, 언더바(_), 하이픈(-)
        const sanitizedTitle = title.replace(/[^a-zA-Z0-9가-힣\-_]/g, '_');

        // 최종 파일명 생성: [타입]_[날짜시간]_[제목].webm
        const filename = `${prefix}_${timestampStr}_${sanitizedTitle}.webm`;

        // FormData 생성
        const formData = new FormData();
        formData.append('audio_file', recordedBlob, filename);
        formData.append('title', title);

        btnUpload.disabled = true;
        btnUpload.textContent = '분석 중... (잠시만 기다려주세요)';

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let redirectUrl = null;
            let isCompleted = false;

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                // SSE 메시지는 'data: ... \n\n' 형태로 옴. 여러 메시지가 한 번에 올 수도 있음.
                const lines = chunk.split('\n\n');
                
                for (const line of lines) {
                    const trimmedLine = line.trim();
                    if (trimmedLine.startsWith('data: ')) {
                        try {
                            const jsonStr = trimmedLine.substring(6);
                            const data = JSON.parse(jsonStr);
                            console.log('Server Event:', data);
                            
                            // 버튼에 진행상황 표시
                            if (data.message) {
                                btnUpload.textContent = data.message;
                            }

                            if (data.step === 'complete' && data.redirect) {
                                redirectUrl = data.redirect;
                                isCompleted = true;
                            }
                            
                            if (data.step === 'error') {
                                alert('서버 오류: ' + data.message);
                                btnUpload.disabled = false;
                                btnUpload.textContent = '다시 시도';
                                return;
                            }

                        } catch (e) {
                            console.warn('JSON 파싱 에러:', e, trimmedLine);
                        }
                    }
                }
            }

            if (isCompleted && redirectUrl) {
                window.location.href = redirectUrl;
            } else {
                // 완료되었으나 URL이 없는 경우 (거의 없겠지만)
                if (isCompleted) {
                     alert('완료되었으나 이동할 주소를 찾지 못했습니다. 메인으로 이동합니다.');
                     window.location.href = '/';
                } else {
                     // 스트림이 끊겼거나 알 수 없는 종료
                     alert('서버 연결이 종료되었습니다.');
                     btnUpload.disabled = false;
                }
            }

        } catch (err) {
            console.error('업로드 에러:', err);
            alert('업로드 중 오류 발생: ' + err.message);
            btnUpload.disabled = false;
            btnUpload.textContent = '분석 시작하기';
        }
    });
});
