import { Injectable, signal, inject } from '@angular/core';
import { InterviewQuestion, AnalysisResult, InterviewService } from './interview.service';

@Injectable({ providedIn: 'root' })
export class AudioService {
  private recognition: any = null;
  private isRecognitionActive = false;
  readonly liveTranscript = signal<string>('');
  readonly clarity = signal<number>(1.0); // 0.0 to 1.0 confidence
  readonly volume = signal<number>(0);
  readonly error = signal<string | null>(null);
  readonly isSpeaking = signal<boolean>(false);

  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private currentAudioElement: HTMLAudioElement | null = null;

  private interview = inject(InterviewService);

  constructor() {
    this.initRecognition();
  }

  private initRecognition() {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      this.error.set('Web Speech API not supported in this browser.');
      return;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-US';

    this.recognition.onstart = () => {
      this.isRecognitionActive = true;
      this.error.set(null);
    };

    this.recognition.onresult = (event: any) => {
      let interimTranscript = '';
      let confidenceTotal = 0;
      let resultCount = 0;

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          // Final result
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
        confidenceTotal += event.results[i][0].confidence;
        resultCount++;
      }
      
      this.clarity.set(resultCount > 0 ? (confidenceTotal / resultCount) : 1);

      let finalTranscript = '';
      for (let i = 0; i < event.results.length; ++i) {
        finalTranscript += event.results[i][0].transcript;
      }
      this.liveTranscript.set(finalTranscript || interimTranscript);
    };

    this.recognition.onerror = (event: any) => {
      console.error('Speech Recognition Error:', event.error);
      if (event.error === 'no-speech') {
        // Keep active
      } else {
        this.error.set(`Speech Error: ${event.error}`);
        this.isRecognitionActive = false;
      }
    };

    this.recognition.onend = () => {
      this.isRecognitionActive = false;
    };
  }

  async startRecording(): Promise<void> {
    this.error.set(null);
    this.liveTranscript.set('');
    this.clarity.set(1.0);
    this.volume.set(0);
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        } 
      });
      
      this.audioContext = new AudioContext({ sampleRate: 48000 }); 
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }
      
      this.error.set(null);

      const source = this.audioContext.createMediaStreamSource(stream);
      const gainNode = this.audioContext.createGain();
      gainNode.gain.value = 2.0;

      const destination = this.audioContext.createMediaStreamDestination();
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      
      source.connect(gainNode);
      gainNode.connect(destination);
      gainNode.connect(this.analyser);
      
      const bufferLength = this.analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const updateVolume = () => {
        if (!this.analyser) return;
        this.analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) sum += dataArray[i];
        const vol = Math.round(sum / bufferLength);
        this.volume.set(vol);
        if (this.mediaRecorder) requestAnimationFrame(updateVolume);
      };
      updateVolume();

      this.mediaRecorder = new MediaRecorder(destination.stream);
      this.audioChunks = [];
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) this.audioChunks.push(event.data);
      };

      if (this.recognition) {
        try { this.recognition.start(); } catch(e) {}
      }

      this.mediaRecorder.start(100);
    } catch (err: any) {
      this.error.set('Mic Init Error: ' + err.message);
      throw err;
    }
  }

  async stopRecording(question: InterviewQuestion): Promise<AnalysisResult> {
    if (this.recognition) {
      try { this.recognition.stop(); } catch(e) {}
    }

    return new Promise((resolve) => {
      if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
        this.mediaRecorder.onstop = () => {
          const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
          const audioUrl = URL.createObjectURL(audioBlob);
          this.interview.lastAudioUrl.set(audioUrl); // <<-- FIX: Ahora el botón de Play lo encontrará
          
          const transcript = this.liveTranscript().trim();
          
          if (!transcript) {
            resolve(this.generateEmptyFeedback(question));
          } else {
            resolve(this.processTranscript(transcript, question));
          }
        };
        this.mediaRecorder.stop();
      } else {
        resolve(this.generateEmptyFeedback(question));
      }
    });
  }

  playRecording() {
    const url = this.interview.lastAudioUrl();
    if (url) {
      if (this.currentAudioElement) {
        this.currentAudioElement.pause();
        this.currentAudioElement = null;
      }

      this.currentAudioElement = new Audio(url);
      this.isSpeaking.set(true);
      
      this.currentAudioElement.onended = () => {
        this.isSpeaking.set(false);
        this.currentAudioElement = null;
      };

      this.currentAudioElement.onerror = () => {
        this.isSpeaking.set(false);
        this.currentAudioElement = null;
      };

      this.currentAudioElement.play();
    }
  }

  getRecordingUrl() {
    return this.interview.lastAudioUrl();
  }

  readText(text: string, onEnd?: () => void) {
    // Stop any current reading
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 1.05; 
    utterance.pitch = 1.0;
    
    this.isSpeaking.set(true);

    utterance.onend = () => {
      this.isSpeaking.set(false);
      if (onEnd) onEnd();
    };

    utterance.onerror = () => {
      this.isSpeaking.set(false);
    };
    
    window.speechSynthesis.speak(utterance);
  }

  stopSpeaking() {
    // Stop TTS
    window.speechSynthesis.cancel();
    
    // Stop Audio Files
    if (this.currentAudioElement) {
      this.currentAudioElement.pause();
      this.currentAudioElement = null;
    }

    this.isSpeaking.set(false);
  }

  private processTranscript(transcript: string, question: InterviewQuestion): AnalysisResult {
    const transcriptLower = transcript.toLowerCase();
    
    // Mejoramos la detección: si escuchamos 'mess' pero buscamos 'MES', lo damos por bueno.
    const normalize = (s: string) => s.toLowerCase()
      .replace('mess', 'mes')
      .replace('florist', 'flores')
      .replace('san fran airspace', 'safran aerospace')
      .replace('sanford', 'safran')
      .replace('crossability', 'traceability')
      .replace('archive', 'achieved')
      .replace('guitar', 'digital')
      .replace('weight', 'wip')
      .replace('miles', 'thousand')
      .replace('bully blow up', 'tulip rollout')
      .replace('outside medical', 'outset medical')
      .replace('history focuses', 'strategy focused')
      .replace('robots', 'robust')
      .replace('basket atl', 'based etl')
      .replace('fully platform', 'tulip platform')
      .replace('280 erp', 'qad erp')
      .replace('district fda', 'strict fda')
      .replace('street fda', 'strict fda')
      .replace('complaints', 'compliance')
      .replace('ball maintaining', 'while maintaining')
      .replace('house of america myers', 'outset medical')
      .replace('make out', 'outset')
      .replace('only brought out', 'tulip rollout')
      .replace('brought out', 'rollout')
      .replace('basic atl', 'based etl')
      .replace('base at atl', 'based etl')
      .replace('toilet platform', 'tulip platform')
      .replace('rest happy', 'rest apis')
      .replace('insurance', 'ensuring')
      .replace('the floor', 'data flow')
      .replace('data floor', 'data flow')
      .replace('classroom', 'class iii')
      .replace('several', 'zero')
      .replace('sarah', 'zero');

    const normalizedTranscript = normalize(transcriptLower);

    const found = question.expectedKeywords.filter(kw => 
      normalizedTranscript.includes(kw.toLowerCase()) || 
      transcriptLower.includes(kw.toLowerCase())
    );
    const missed = question.expectedKeywords.filter(kw => 
      !normalizedTranscript.includes(kw.toLowerCase()) && 
      !transcriptLower.includes(kw.toLowerCase())
    );

    const keywordWeight = found.length / (question.expectedKeywords.length || 1);
    const score = Math.round((keywordWeight * 10));

    const wordInsights = transcript.split(' ').filter(w => w.length > 0).map(word => ({
      word,
      confidence: this.clarity()
    }));

    return {
      score,
      transcript,
      clarity: this.clarity(),
      wordInsights,
      grammarCorrection: null,
      improvedResponse: `Focus on: ${missed.slice(0, 2).join(', ')}.`,
      keywordsFound: found,
      keywordsMissed: missed,
      feedback: score >= 7 ? 'Excellent clarity and technical scope.' : 'Good start, try reading the suggested response below.'
    };
  }

  private generateEmptyFeedback(question: InterviewQuestion): AnalysisResult {
    return {
      score: 0,
      transcript: '(No speech detected)',
      clarity: 0,
      wordInsights: [],
      grammarCorrection: 'Microphone did not pick up audio or transcript failed.',
      improvedResponse: 'Try reading the suggested text aloud.',
      keywordsFound: [],
      keywordsMissed: question.expectedKeywords,
      feedback: 'Silence detected. Check your mic and try again.'
    };
  }
}
