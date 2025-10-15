const functions = require('firebase-functions');
const admin = require('firebase-admin');
const { Storage } = require('@google-cloud/storage');
const { VideoIntelligenceServiceClient } = require('@google-cloud/video-intelligence');
const { SpeechClient } = require('@google-cloud/speech');
const { ImageAnnotatorClient } = require('@google-cloud/vision');
const { VertexAI } = require('@google-cloud/vertexai');
const ffmpeg = require('fluent-ffmpeg');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Initialize Firebase Admin
admin.initializeApp();

// Initialize Google Cloud clients
const storage = new Storage();
const videoIntelligence = new VideoIntelligenceServiceClient();
const speechClient = new SpeechClient();
const visionClient = new ImageAnnotatorClient();
const vertexAI = new VertexAI({
  project: process.env.GOOGLE_CLOUD_PROJECT,
  location: 'us-central1'
});

// Initialize Gemini model
const model = vertexAI.getGenerativeModel({
  model: 'gemini-1.5-pro',
  generationConfig: {
    maxOutputTokens: 8192,
    temperature: 0.1,
    topP: 0.8,
  },
});

/**
 * Cloud Function triggered by video upload to Cloud Storage
 */
exports.analyzeVideo = functions.storage.object().onFinalize(async (object) => {
  const fileBucket = object.bucket;
  const filePath = object.name;
  const contentType = object.contentType;

  // Only process video files
  if (!contentType.startsWith('video/')) {
    console.log('File is not a video, skipping analysis');
    return null;
  }

  console.log(`Processing video: ${filePath}`);

  try {
    // Download video to local temp directory
    const tempDir = os.tmpdir();
    const localFilePath = path.join(tempDir, `video_${Date.now()}.${getFileExtension(contentType)}`);
    
    await storage.bucket(fileBucket).file(filePath).download({
      destination: localFilePath
    });

    console.log('Video downloaded to:', localFilePath);

    // Extract audio and key frames
    const analysisResults = await analyzeVideoContent(localFilePath);

    // Generate timeline summary using Gemini
    const timelineSummary = await generateTimelineSummary(analysisResults);

    // Send results to backend API
    await sendResultsToBackend(filePath, timelineSummary, analysisResults);

    // Clean up temporary file
    fs.unlinkSync(localFilePath);

    console.log('Video analysis completed successfully');
    return null;

  } catch (error) {
    console.error('Error processing video:', error);
    throw error;
  }
});

/**
 * Analyze video content using multiple AI services
 */
async function analyzeVideoContent(videoPath) {
  const results = {
    audioTranscription: '',
    keyFrames: [],
    objects: [],
    text: [],
    emotions: [],
    activities: []
  };

  try {
    // Extract audio using FFmpeg
    const audioPath = videoPath.replace(/\.[^/.]+$/, '.wav');
    await extractAudio(videoPath, audioPath);

    // Transcribe audio using Speech-to-Text
    if (fs.existsSync(audioPath)) {
      results.audioTranscription = await transcribeAudio(audioPath);
      fs.unlinkSync(audioPath); // Clean up audio file
    }

    // Extract key frames
    const keyFrames = await extractKeyFrames(videoPath);
    results.keyFrames = keyFrames;

    // Analyze each key frame
    for (const framePath of keyFrames) {
      const frameAnalysis = await analyzeFrame(framePath);
      results.objects.push(...frameAnalysis.objects);
      results.text.push(...frameAnalysis.text);
      results.emotions.push(...frameAnalysis.emotions);
    }

    // Analyze video for activities using Video Intelligence API
    const activityAnalysis = await analyzeVideoActivities(videoPath);
    results.activities = activityAnalysis;

    return results;

  } catch (error) {
    console.error('Error analyzing video content:', error);
    throw error;
  }
}

/**
 * Extract audio from video using FFmpeg
 */
function extractAudio(videoPath, audioPath) {
  return new Promise((resolve, reject) => {
    ffmpeg(videoPath)
      .output(audioPath)
      .audioCodec('pcm_s16le')
      .audioChannels(1)
      .audioFrequency(16000)
      .on('end', resolve)
      .on('error', reject)
      .run();
  });
}

/**
 * Transcribe audio using Google Speech-to-Text
 */
async function transcribeAudio(audioPath) {
  const audioBytes = fs.readFileSync(audioPath).toString('base64');

  const request = {
    audio: {
      content: audioBytes,
    },
    config: {
      encoding: 'LINEAR16',
      sampleRateHertz: 16000,
      languageCode: 'zh-TW', // Traditional Chinese
      alternativeLanguageCodes: ['en-US'],
    },
  };

  const [response] = await speechClient.recognize(request);
  const transcription = response.results
    .map(result => result.alternatives[0].transcript)
    .join('\n');

  return transcription;
}

/**
 * Extract key frames from video
 */
function extractKeyFrames(videoPath) {
  return new Promise((resolve, reject) => {
    const tempDir = path.dirname(videoPath);
    const keyFrames = [];
    let frameCount = 0;

    ffmpeg(videoPath)
      .on('end', () => resolve(keyFrames))
      .on('error', reject)
      .screenshots({
        timestamps: ['10%', '25%', '50%', '75%', '90%'],
        filename: 'frame_%i.png',
        folder: tempDir,
        size: '320x240'
      })
      .on('filenames', (filenames) => {
        keyFrames.push(...filenames.map(name => path.join(tempDir, name)));
      });
  });
}

/**
 * Analyze a single frame using Vision API
 */
async function analyzeFrame(framePath) {
  const imageBytes = fs.readFileSync(framePath);
  
  const [objectResult] = await visionClient.objectLocalization({
    image: { content: imageBytes }
  });

  const [textResult] = await visionClient.textDetection({
    image: { content: imageBytes }
  });

  const [faceResult] = await visionClient.faceDetection({
    image: { content: imageBytes }
  });

  return {
    objects: objectResult.localizedObjectAnnotations || [],
    text: textResult.textAnnotations || [],
    emotions: faceResult.faceAnnotations || []
  };
}

/**
 * Analyze video activities using Video Intelligence API
 */
async function analyzeVideoActivities(videoPath) {
  const gcsUri = `gs://${process.env.GOOGLE_CLOUD_PROJECT}-videos/${path.basename(videoPath)}`;
  
  // Upload video to GCS for Video Intelligence API
  await storage.bucket(`${process.env.GOOGLE_CLOUD_PROJECT}-videos`).upload(videoPath);

  const request = {
    inputUri: gcsUri,
    features: ['LABEL_DETECTION', 'ACTIVITY_RECOGNITION', 'OBJECT_TRACKING'],
  };

  const [operation] = await videoIntelligence.annotateVideo(request);
  const [results] = await operation.promise();

  return results.annotationResults || [];
}

/**
 * Generate timeline summary using Gemini
 */
async function generateTimelineSummary(analysisResults) {
  const prompt = `
    請分析以下影片內容並生成一個詳細的時間軸摘要：

    音頻轉錄：${analysisResults.audioTranscription}

    檢測到的物件：${JSON.stringify(analysisResults.objects)}

    檢測到的文字：${JSON.stringify(analysisResults.text)}

    檢測到的活動：${JSON.stringify(analysisResults.activities)}

    請以繁體中文生成一個結構化的時間軸，包含：
    1. 主要事件和時間點
    2. 潛在的詐騙風險指標
    3. 建議的安全措施
    4. 需要特別注意的行為模式

    格式請使用 JSON 結構。
  `;

  const result = await model.generateContent(prompt);
  const response = await result.response;
  return response.text();
}

/**
 * Send analysis results to backend API
 */
async function sendResultsToBackend(filePath, timelineSummary, analysisResults) {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  
  const payload = {
    file_id: path.basename(filePath),
    summary: timelineSummary,
    analysis_results: analysisResults,
    timestamp: new Date().toISOString()
  };

  try {
    const response = await fetch(`${backendUrl}/api/v1/media/analyze-video-summary`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.BACKEND_API_KEY}`
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.statusText}`);
    }

    console.log('Results sent to backend successfully');
  } catch (error) {
    console.error('Error sending results to backend:', error);
    // Don't throw error to avoid function retry
  }
}

/**
 * Get file extension from content type
 */
function getFileExtension(contentType) {
  const extensions = {
    'video/mp4': 'mp4',
    'video/webm': 'webm',
    'video/avi': 'avi',
    'video/mov': 'mov'
  };
  return extensions[contentType] || 'mp4';
}

