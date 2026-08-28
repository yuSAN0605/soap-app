<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>カルテ記録入力・生成システム | 八王子クリニック</title>
  <style>
    :root {
      --primary-color: #0284c7;
      --bg-color: #f8fafc;
      --card-bg: #ffffff;
      --text-color: #1e293b;
      --border-color: #cbd5e1;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background-color: var(--bg-color);
      color: var(--text-color);
      line-height: 1.6;
      padding: 20px;
    }

    .container {
      max-width: 800px;
      margin: 0 auto;
    }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 16px;
      margin-bottom: 24px;
      border-bottom: 2px solid var(--border-color);
    }

    .header h1 {
      font-size: 1.4rem;
      color: #0f172a;
    }

    .header .nav-link {
      color: var(--primary-color);
      text-decoration: none;
      font-weight: 600;
    }

    .card {
      background: var(--card-bg);
      border-radius: 12px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
      padding: 24px;
      margin-bottom: 24px;
    }

    .form-group {
      margin-bottom: 18px;
    }

    .form-label {
      display: block;
      font-weight: 600;
      margin-bottom: 6px;
      font-size: 0.9rem;
    }

    .form-control {
      width: 100%;
      padding: 10px 14px;
      border: 1px solid var(--border-color);
      border-radius: 6px;
      font-size: 1rem;
    }

    .form-control:focus {
      outline: none;
      border-color: var(--primary-color);
    }

    textarea.form-control {
      min-height: 140px;
      resize: vertical;
    }

    .btn-group {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-bottom: 12px;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 12px 10px;
      border: none;
      border-radius: 6px;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      transition: opacity 0.2s;
    }

    .btn:hover { opacity: 0.9; }
    .btn:disabled { opacity: 0.6; cursor: not-allowed; }
    .btn-voice { background-color: #00c853; color: white; }
    .btn-voice.recording { background-color: #d32f2f; animation: pulse 1.5s infinite; }
    .btn-file { background-color: #00b0ff; color: white; }
    .btn-tpl { background-color: #f59e0b; color: white; }
    .btn-generate { width: 100%; background-color: #b388ff; color: white; padding: 14px; font-size: 1.1rem; }
    .btn-pdf { width: 100%; background-color: #334155; color: white; margin-top: 16px; padding: 14px; font-size: 1.05rem; }

    @keyframes pulse {
      0% { opacity: 1; }
      50% { opacity: 0.6; }
      100% { opacity: 1; }
    }

    .camera-box-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-bottom: 18px;
    }

    .camera-card {
      border: 2px dashed #cbd5e1;
      border-radius: 8px;
      padding: 14px;
      text-align: center;
      background: #f8fafc;
    }

    .camera-card-title {
      font-weight: bold;
      font-size: 0.9rem;
      margin-bottom: 10px;
      color: #334155;
    }

    .btn-cam-action {
      background-color: #ef4444;
      color: white;
      width: 100%;
      padding: 8px 12px;
      font-size: 0.85rem;
    }

    .thumb-preview-box {
      margin-top: 10px;
      position: relative;
      display: none;
    }

    .thumb-preview-box img {
      width: 100%;
      max-height: 120px;
      object-fit: cover;
      border-radius: 6px;
      border: 1px solid var(--border-color);
    }

    .remove-thumb-btn {
      position: absolute;
      top: 4px;
      right: 4px;
      background: rgba(239, 68, 68, 0.9);
      color: white;
      border: none;
      border-radius: 50%;
      width: 22px;
      height: 22px;
      font-size: 12px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .preview-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 8px;
    }

    .preview-container {
      position: relative;
      display: inline-block;
    }

    .pdf-preview-box {
      width: 90px;
      height: 90px;
      background-color: #f1f5f9;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 6px;
      text-align: center;
      font-size: 0.75rem;
      color: #475569;
      word-break: break-all;
    }

    .pdf-preview-box span { font-size: 1.4rem; margin-bottom: 2px; }

    .result-field-group {
      margin-bottom: 14px;
    }

    .result-field-label {
      font-weight: bold;
      font-size: 0.95rem;
      color: #0f172a;
      margin-bottom: 4px;
    }

    .result-textarea {
      width: 100%;
      padding: 10px 12px;
      border: 1px solid var(--border-color);
      border-radius: 4px;
      font-size: 0.95rem;
      font-family: inherit;
      resize: vertical;
      background: #fff;
      line-height: 1.5;
    }

    .template-info {
      background-color: #e0f2fe;
      border-left: 4px solid var(--primary-color);
      padding: 12px;
      margin-top: 8px;
      border-radius: 4px;
      font-size: 0.9rem;
      color: #0c4a6e;
    }

    .alert {
      padding: 12px;
      border-radius: 6px;
      margin-bottom: 16px;
      display: none;
    }

    .alert.success {
      background-color: #d4edda;
      border: 1px solid #c3e6cb;
      color: #155724;
    }

    .alert.error {
      background-color: #f8d7da;
      border: 1px solid #f5c6cb;
      color: #721c24;
    }

    .alert.info {
      background-color: #d1ecf1;
      border: 1px solid #bee5eb;
      color: #0c5460;
    }

    .alert.active {
      display: block;
    }

    .loading-spinner {
      display: inline-block;
      width: 16px;
      height: 16px;
      border: 2px solid #f3f3f3;
      border-top: 2px solid #b388ff;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin-right: 8px;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  </style>
</head>
<body>

<div class="container">
  
  <header class="header">
    <h1>カルテ記録入力 | 八王子クリニック</h1>
    <a href="#" class="nav-link">記録一覧</a>
  </header>

  <main class="card">
    <div id="alertBox" class="alert"></div>

    <form id="soapForm">
      
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
        <div class="form-group">
          <label class="form-label" for="staffId">スタッフID</label>
          <input type="text" id="staffId" class="form-control" placeholder="例: T001">
        </div>
        <div class="form-group">
          <label class="form-label" for="patientId">患者ID</label>
          <input type="text" id="patientId" class="form-control" placeholder="例: P123">
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">評価テンプレート挿入</label>
        <div class="btn-group">
          <button type="button" class="btn btn-tpl" onclick="insertTemplate('腰臀部')">
            🦴 腰臀部評価モード
          </button>
          <button type="button" class="btn btn-tpl" onclick="insertTemplate('頸椎')">
            🦴 頸椎評価モード
          </button>
        </div>
        <div class="template-info" id="templateInfo" style="display: none;">
          ✓ テンプレートが検出されました。自動的に構造化データとして解析されます。
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">入力方法を選択</label>
        <div class="btn-group">
          <button type="button" id="voiceBtn" class="btn btn-voice" onclick="toggleVoiceInput()">
            🎤 音声入力
          </button>
          
          <label class="btn btn-file" style="margin: 0; cursor: pointer;">
            📁 画像・PDF選択
            <input type="file" accept="image/*,application/pdf" multiple style="display: none;" onchange="handleFiles(event)">
          </label>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">撮影エリア（それぞれの枠からカメラ撮影）</label>
        <div class="camera-box-grid">
          
          <div class="camera-card">
            <div class="camera-card-title">📋 院内カルテ</div>
            <button type="button" class="btn btn-cam-action" onclick="openCameraFor('karte')">
              📷 撮影する
            </button>
            <div class="thumb-preview-box" id="karteThumbArea">
              <img id="karteImg" src="" alt="院内カルテ">
              <button type="button" class="remove-thumb-btn" onclick="clearSpecificImage('karte')">✕</button>
            </div>
          </div>

          <div class="camera-card">
            <div class="camera-card-title">📝 臨床メモ</div>
            <button type="button" class="btn btn-cam-action" onclick="openCameraFor('memo')">
              📷 撮影する
            </button>
            <div class="thumb-preview-box" id="memoThumbArea">
              <img id="memoImg" src="" alt="臨床メモ">
              <button type="button" class="remove-thumb-btn" onclick="clearSpecificImage('memo')">✕</button>
            </div>
          </div>

        </div>
      </div>

      <div class="form-group" id="cameraArea" style="display: none; text-align: center; background: #1e293b; padding: 16px; border-radius: 8px; margin-bottom: 18px;">
        <div style="color: white; font-size: 0.9rem; margin-bottom: 8px;" id="cameraModeTitle">カメラ表示</div>
        <video id="webcam" autoplay playsinline style="width: 100%; max-width: 500px; border-radius: 6px;"></video>
        <div style="margin-top: 12px;">
          <button type="button" class="btn" style="background-color: #22c55e; color: white; padding: 10px 24px;" onclick="takePhotoForTarget()">
            📸 撮影
          </button>
          <button type="button" class="btn" style="background-color: #64748b; color: white; margin-left: 8px;" onclick="stopCamera()">
            キャンセル
          </button>
        </div>
        <canvas id="canvas" style="display: none;"></canvas>
      </div>

      <div class="form-group" id="previewArea" style="display: none;">
        <label class="form-label" id="previewTitle">添付ファイル（0件）</label>
        <div class="preview-grid" id="previewGrid"></div>
      </div>

      <div class="form-group">
        <label class="form-label" for="inputText">入力テキスト（テンプレート入力・音声・手入力可能）</label>
        <textarea id="inputText" class="form-control" placeholder="テンプレートボタンを押すか、音声入力・キーボード直接入力でメモを記載してください。"></textarea>
      </div>

      <button type="button" id="generateBtn" class="btn btn-generate" onclick="generateSOAP()">
        カルテテキスト生成
      </button>

    </form>
  </main>

  <section class="card" id="soapResult" style="display: none;">
    <h2 style="font-size: 1.1rem; margin-bottom: 16px;">生成結果（カルテ用プレーンテキスト）</h2>

    <div class="result-field-group">
      <div class="result-field-label">＊経過</div>
      <textarea id="resProgress" class="result-textarea" rows="4" placeholder="【現病歴】内容（現病歴・検査結果）&#10;【画像所見】X線：... MRI：...（該当なければ無記載）"></textarea>
    </div>

    <div class="result-field-group">
      <div class="result-field-label">＊注意点</div>
      <textarea id="resNotice" class="result-textarea" rows="2" placeholder="既往歴 / 体重 / 仕事（記載なければ無記載）"></textarea>
    </div>

    <div class="result-field-group">
      <div class="result-field-label">S）</div>
      <textarea id="resS" class="result-textarea" rows="3" placeholder="主訴・患者の発言（要望・目標・主訴のみ記載）"></textarea>
    </div>

    <div class="result-field-group">
      <div class="result-field-label">O）</div>
      <textarea id="resO" class="result-textarea" rows="4" placeholder="客観的所見（ROM, MMT, 触診, 動作観察, NRS等）"></textarea>
    </div>

    <div class="result-field-group">
      <div class="result-field-label">A）</div>
      <textarea id="resA" class="result-textarea" rows="3" placeholder="評価・考察"></textarea>
    </div>

    <div class="result-field-group">
      <div class="result-field-label">P）</div>
      <textarea id="resP" class="result-textarea" rows="3" placeholder="#1 関節可動域訓練 #2 筋力強化訓練 #3 バランス訓練 #4 自主トレーニング指導"></textarea>
    </div>

    <button type="button" class="btn btn-pdf" id="pdfBtn" onclick="downloadTextPDF()">
      💾 テキストファイル保存（コピペ用）
    </button>
  </section>

</div>

<script>
  const API_BASE_URL = window.location.origin;

  let localStream = null;
  let activeCameraTarget = null;
  let karteBase64 = null;
  let memoBase64 = null;
  let attachedFiles = [];
  let recognition = null;
  let isRecording = false;

  const templates = {
    '腰臀部': `【腰部・臀部疾患理学療法評価】
S (Subjective)
・動作：[座位 / 歩行 / 立位 / 立ち上がり / その他:]
・時期：[朝・動き始め / 夕方・徐々に]
・部位：[腰部 / 上臀部 / 下臀部 / 大腿 / 下肢]
・範囲：[局所 / 広範囲]

O (Objective)
▼1. 腰椎可動域・誘発テスト
・屈曲： ° (痛・制限：)
・伸展： ° (痛・制限：)
・Kemp test：右 [＋/－] (部位:) / 左 [＋/－] (部位:)

▼2. 下肢神経・軟部組織絞扼誘発テスト
・SLR：Rt [＋/－] / Lt [＋/－]
・SLR内転：Rt [＋/－] / Lt [＋/－]
・梨状筋 (屈・内転・内旋)：Rt [＋/－] / Lt [＋/－]
・大腿方形/内閉鎖筋 (屈・内転・外旋)：Rt [＋/－] / Lt [＋/－]
・FNST (大腿神経伸長)：Rt [＋/－] / Lt [＋/－]

▼3. 仙腸関節評価
・Patrick test：右 [＋/－] (部位:) / 左 [＋/－] (部位:)
・P4 test：右 [＋/－] / 左 [＋/－]
・Td (PSIS付近)：右 [＋/－] / 左 [＋/－]
・座位後方荷重：[＋/－]

▼4. 触診 (圧痛・Td)
・横突起 (胸腰筋膜中葉)：[右/左]
・椎間関節 (多裂筋)：[右/左]
・梨状筋 (坐骨神経ルート)：[右/左]
・PSIS付近 (仙腸関節)：[右/左]

▼5. 神経学的所見 (感覚・MMT)
・知覚：L4(下腿内側) [Rt/Lt] / L5(母趾) [Rt/Lt] / S1(小趾) [Rt/Lt]
・MMT：EHL [] / FHL [] / TA [] / 中殿筋 [] / 大殿筋 [] / ハム [] / 腸腰筋 [] / 大腿四頭筋 []

A (Assessment)
[ ] 神経根圧排(牽引)型
[ ] 神経根絞扼(挟み込み)型
[ ] ダブル・クラッシュ
[ ] 椎間関節性
[ ] 椎間板性
[ ] 筋・筋膜性
[ ] 仙腸関節障害`,

    '頸椎': `【頸部疾患理学療法評価】
S (Subjective)
・疼痛部位：[片側 / 両側 / 後頸部 / 肩甲骨周囲 / 上肢]

O (Objective)
▼1. 頸部可動域 (ROM)
・屈曲： ° (痛・制限：) / 伸展： ° (痛・制限：)
・右側屈： ° (痛・制限：) / 左側屈： ° (痛・制限：)
・右回旋： ° (痛・制限：) / 左回旋： ° (痛・制限：)

▼2. 特殊テスト (椎間孔・神経根評価)
・Jackson test：右 [＋/－] (部位:)
・Spurling test：右 [＋/－] (部位:)

▼3. 触診 (圧痛・Td)
・椎間関節・椎間孔：[右/左] (部位:)
・横突起 (中斜角筋・斜角筋隙)：[右/左]
・肩甲骨上角 (肩甲挙筋・肩甲背神経)：[右/左]
・烏口突起下 (腕神経叢・小胸筋間隙)：[右/左]

▼4. 神経学的所見
・知覚：C5 [] / C6 [] / C7 [] / C8 []
・Tinel sign：尺骨神経 [右/左] / 正中神経 [右/左] / 橈骨神経 [右/左]

▼5. 運動機能 (MMT)
・C5(肩外転) [Rt/Lt] / C6(肘屈曲) [Rt/Lt] / C7(肘伸展) [Rt/Lt] / C8(指屈曲) [Rt/Lt]

A (Assessment)
[ ] 椎間関節性 (片側性)
[ ] 神経根症 (片側性)
[ ] 筋・筋膜性 (両側性)
[ ] 椎間板
[ ] 胸郭出口症候群 (TOS)
[ ] 末梢神経絞扼障害`
  };

  function showAlert(message, type = 'info') {
    const alertBox = document.getElementById('alertBox');
    alertBox.textContent = message;
    alertBox.className = `alert ${type} active`;
    if (type !== 'error') {
      setTimeout(() => {
        alertBox.classList.remove('active');
      }, 4000);
    }
  }

  function parseTemplateInput(inputText) {
    const result = {
      hasTemplate: false,
      subjective: '',
      objective: '',
      assessment: '',
      rawText: inputText
    };

    if (inputText.includes('S (Subjective)') || inputText.includes('O (Objective)') || inputText.includes('A (Assessment)')) {
      result.hasTemplate = true;

      const subjectiveMatch = inputText.match(/S \(Subjective\)([\s\S]*?)(?=O \(Objective\)|$)/);
      const objectiveMatch = inputText.match(/O \(Objective\)([\s\S]*?)(?=A \(Assessment\)|$)/);
      const assessmentMatch = inputText.match(/A \(Assessment\)([\s\S]*?)$/);

      if (subjectiveMatch) result.subjective = subjectiveMatch[1].trim();
      if (objectiveMatch) result.objective = objectiveMatch[1].trim();
      if (assessmentMatch) result.assessment = assessmentMatch[1].trim();
    }

    return result;
  }

  function insertTemplate(type) {
    const inputText = document.getElementById('inputText');
    const templateText = templates[type];
    
    if (inputText.value.trim() !== '') {
      inputText.value = inputText.value + '\n\n' + templateText;
    } else {
      inputText.value = templateText;
    }
    
    showTemplateInfo();
  }

  function showTemplateInfo() {
    const inputText = document.getElementById('inputText').value;
    const parsed = parseTemplateInput(inputText);
    const infoBox = document.getElementById('templateInfo');
    
    if (parsed.hasTemplate) {
      infoBox.style.display = 'block';
    } else {
      infoBox.style.display = 'none';
    }
  }

  document.addEventListener('DOMContentLoaded', function() {
    const inputText = document.getElementById('inputText');
    if (inputText) {
      inputText.addEventListener('input', showTemplateInfo);
    }
  });

  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.lang = 'ja-JP';
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onresult = function(event) {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          transcript += event.results[i][0].transcript + '\n';
        }
      }
      document.getElementById('inputText').value += transcript;
      showTemplateInfo();
    };

    recognition.onerror = function(event) {
      console.error("音声認識エラー:", event.error);
      stopVoiceInput();
      showAlert('音声認識エラーが発生しました', 'error');
    };

    recognition.onend = function() {
      if (isRecording) recognition.start();
    };
  }

  function toggleVoiceInput() {
    if (!recognition) {
      showAlert("お使いのブラウザは音声入力に対応していません。", 'error');
      return;
    }
    isRecording ? stopVoiceInput() : startVoiceInput();
  }

  function startVoiceInput() {
    isRecording = true;
    recognition.start();
    const btn = document.getElementById('voiceBtn');
    btn.classList.add('recording');
    btn.innerHTML = '⏹️ 録音停止';
    showAlert('音声入力開始', 'info');
  }

  function stopVoiceInput() {
    isRecording = false;
    if (recognition) recognition.stop();
    const btn = document.getElementById('voiceBtn');
    btn.classList.remove('recording');
    btn.innerHTML = '🎤 音声入力';
  }

  async function openCameraFor(target) {
    activeCameraTarget = target;
    const cameraArea = document.getElementById('cameraArea');
    const video = document.getElementById('webcam');
    const title = document.getElementById('cameraModeTitle');

    title.innerText = target === 'karte' ? "撮影モード: 📋 院内カルテ" : "撮影モード: 📝 臨床メモ";

    try {
      localStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { exact: "environment" } },
        audio: false
      });
    } catch (err) {
      try {
        localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      } catch (e) {
        showAlert("カメラの起動に失敗しました。", 'error');
        return;
      }
    }

    video.srcObject = localStream;
    cameraArea.style.display = 'block';
  }

  function stopCamera() {
    if (localStream) {
      localStream.getTracks().forEach(track => track.stop());
    }
    document.getElementById('cameraArea').style.display = 'none';
  }

  function takePhotoForTarget() {
    const video = document.getElementById('webcam');
    const canvas = document.getElementById('canvas');
    const context = canvas.getContext('2d');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imageDataUrl = canvas.toDataURL('image/jpeg');
    const base64Data = imageDataUrl.split(',')[1];

    if (activeCameraTarget === 'karte') {
      karteBase64 = base64Data;
      document.getElementById('karteImg').src = imageDataUrl;
      document.getElementById('karteThumbArea').style.display = 'block';
    } else if (activeCameraTarget === 'memo') {
      memoBase64 = base64Data;
      document.getElementById('memoImg').src = imageDataUrl;
      document.getElementById('memoThumbArea').style.display = 'block';
    }

    stopCamera();
    showAlert('撮影完了', 'success');
  }

  function clearSpecificImage(target) {
    if (target === 'karte') {
      karteBase64 = null;
      document.getElementById('karteImg').src = '';
      document.getElementById('karteThumbArea').style.display = 'none';
    } else if (target === 'memo') {
      memoBase64 = null;
      document.getElementById('memoImg').src = '';
      document.getElementById('memoThumbArea').style.display = 'none';
    }
  }

  function handleFiles(event) {
    const files = event.target.files;
    if (files && files.length > 0) {
      Array.from(files).forEach(file => {
        const reader = new FileReader();
        reader.onload = function(e) {
          const base64Data = e.target.result.split(',')[1];
          let mimeType = file.type || 'application/pdf';
          
          if (!mimeType && file.name.endsWith('.pdf')) {
            mimeType = 'application/pdf';
          }

          attachedFiles.push({
            mimeType: mimeType,
            data: base64Data,
            name: file.name
          });
          renderPreviews();
        };
        reader.readAsDataURL(file);
      });
    }
  }

  function renderPreviews() {
    const previewArea = document.getElementById('previewArea');
    const previewGrid = document.getElementById('previewGrid');
    const previewTitle = document.getElementById('previewTitle');

    previewGrid.innerHTML = '';

    if (attachedFiles.length === 0) {
      previewArea.style.display = 'none';
      return;
    }

    previewTitle.innerText = `その他添付ファイル（${attachedFiles.length}件）`;
    previewArea.style.display = 'block';

    attachedFiles.forEach((fileObj, index) => {
      const container = document.createElement('div');
      container.className = 'preview-container';

      if (fileObj.mimeType.startsWith('image/')) {
        const img = document.createElement('img');
        img.style.width = '90px';
        img.style.height = '90px';
        img.src = `data:${fileObj.mimeType};base64,${fileObj.data}`;
        container.appendChild(img);
      } else {
        const pdfBox = document.createElement('div');
        pdfBox.className = 'pdf-preview-box';
        const shortName = fileObj.name.length > 10 ? fileObj.name.substring(0, 8) + '...' : fileObj.name;
        pdfBox.innerHTML = `<span>📄</span><div>${shortName}</div>`;
        container.appendChild(pdfBox);
      }

      const removeBtn = document.createElement('button');
      removeBtn.className = 'remove-thumb-btn';
      removeBtn.innerText = '✕';
      removeBtn.type = 'button';
      removeBtn.onclick = function() {
        attachedFiles.splice(index, 1);
        renderPreviews();
      };

      container.appendChild(removeBtn);
      previewGrid.appendChild(container);
    });
  }

  async function generateSOAP() {
    const inputText = document.getElementById('inputText').value;
    const generateBtn = document.getElementById('generateBtn');

    if (!inputText && !karteBase64 && !memoBase64 && attachedFiles.length === 0) {
      showAlert("テキスト、院内カルテ画像、臨床メモ画像、または添付ファイルのいずれかを指定してください。", 'error');
      return;
    }

    generateBtn.disabled = true;
    generateBtn.innerHTML = '<span class="loading-spinner"></span>生成中...';

    document.getElementById('soapResult').style.display = 'block';
    document.getElementById('resProgress').value = "解析中...";
    document.getElementById('resNotice').value = "解析中...";
    document.getElementById('resS').value = "解析中...";
    document.getElementById('resO').value = "解析中...";
    document.getElementById('resA').value = "解析中...";
    document.getElementById('resP').value = "解析中...";

    try {
      const response = await fetch(`${API_BASE_URL}/api/generate-soap`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          inputText: inputText,
          karteImage: karteBase64 || null,
          memoImage: memoBase64 || null,
          attachedFiles: attachedFiles
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP Error: ${response.status}`);
      }

      const result = await response.json();
      
      document.getElementById('resProgress').value = result.progress || "";
      document.getElementById('resNotice').value = result.notice || "";
      document.getElementById('resS').value = result.s || "";
      document.getElementById('resO').value = result.o || "";
      document.getElementById('resA').value = result.a || "";
      document.getElementById('resP').value = result.p || "";

      showAlert('カルテ生成に成功しました', 'success');

    } catch (error) {
      console.error('Error:', error);
      showAlert(`エラーが発生しました: ${error.message}`, 'error');
      clearFields();
    } finally {
      generateBtn.disabled = false;
      generateBtn.innerHTML = 'カルテテキスト生成';
    }
  }

  function clearFields() {
    document.getElementById('resProgress').value = "";
    document.getElementById('resNotice').value = "";
    document.getElementById('resS').value = "";
    document.getElementById('resO').value = "";
    document.getElementById('resA').value = "";
    document.getElementById('resP').value = "";
  }

  function downloadTextPDF() {
    const resProgress = document.getElementById('resProgress').value || '';
    const resNotice = document.getElementById('resNotice').value || '';
    const resS = document.getElementById('resS').value || '';
    const resO = document.getElementById('resO').value || '';
    const resA = document.getElementById('resA').value || '';
    const resP = document.getElementById('resP').value || '';

    const now = new Date();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const date = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');

    const fileName = `calte_${month}${date}${hours}${minutes}.txt`;

    const textContent = `＊経過
${resProgress}

＊注意点
${resNotice}

S）
${resS}

O）
${resO}

A）
${resA}

P）
${resP}`;

    const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);

    showAlert('ファイルをダウンロードしました', 'success');
  }
</script>

</body>
</html>