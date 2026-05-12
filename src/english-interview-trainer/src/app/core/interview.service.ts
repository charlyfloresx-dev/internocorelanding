import { Injectable, signal } from '@angular/core';

export interface InterviewQuestion {
  id: number;
  questionEn: string;
  questionEs: string;
  expectedKeywords: string[];
  contextHint: string;
  fullSuggestedResponseEn: string; // New: Full text to practice
}

export interface AnalysisResult {
  score: number;
  transcript: string;
  clarity: number;
  wordInsights: Array<{ word: string, confidence: number }>; // New: Detailed per-word stats
  grammarCorrection: string | null;
  improvedResponse: string;
  keywordsFound: string[];
  keywordsMissed: string[];
  feedback: string;
}

@Injectable({ providedIn: 'root' })
export class InterviewService {
  private questions: InterviewQuestion[] = [
    {
      id: 0,
      questionEn: "Hi Carlos! Can you briefly introduce yourself and mention your biggest achievement as a Senior MES Consultant?",
      questionEs: "¡Hola Carlos! ¿Puedes presentarte brevemente y mencionar tu mayor logro como Consultor Senior de MES?",
      expectedKeywords: ["WIP", "Traceability", "MES", "Safran", "Tulip", "Digital Transformation"],
      contextHint: "Focus on the $4.8M WIP reduction and your experience with full-traceability systems.",
      fullSuggestedResponseEn: "Hi, I'm Carlos Javier Flores Montoya, a Senior MES and Digital Transformation Consultant. My biggest achievement was reducing lost WIP from $4.8 million to just $40,000 in only two months at Safran Aerospace. I achieved this by designing and deploying a full-traceability MES ecosystem from scratch that provided real-time plant floor control and data visibility."
    },
    {
      id: 1,
      questionEn: "You led a Tulip rollout with custom Python ETL for Class III medical devices. What was your technical strategy for this integration?",
      questionEs: "Lideraste un despliegue de Tulip con ETL de Python personalizado. ¿Cuál fue tu estrategia técnica para esta integración?",
      expectedKeywords: ["Python", "ETL", "REST APIs", "Integration", "Class III", "FDA", "Real-time"],
      contextHint: "Mention how you handled legacy systems and ensured zero downtime during the integration.",
      fullSuggestedResponseEn: "For the Tulip rollout at Outset Medical, my strategy focused on building robust Python-based ETL processes. I integrated the Tulip platform with our QAD ERP system using custom REST APIs, ensuring seamless data flow for Class III medical device manufacturing while maintaining strict FDA compliance and zero operational downtime."
    },
    {
      id: 2,
      questionEn: "In your experience, how do you achieve a 95%+ secondary operator adoption rate during a digital adoption program?",
      questionEs: "¿En tu experiencia, cómo logras una tasa de adopción del 95%+ en operadores durante un programa de adopción digital?",
      expectedKeywords: ["Cultural change", "Training", "Shop-floor", "Analytics", "UX", "Uptime", "Standard Time"],
      contextHint: "Talk about your hands-on floor leadership and how you make operators 'love the system'.",
      fullSuggestedResponseEn: "I achieve high adoption rates through hands-on leadership directly on the shop floor. My approach involves personalized operator training and cultural change management. By focusing on UX and showing operators how digital tools reduce their workload and improve uptime accuracy, I've consistently reached over 95% user adoption across multiple plants."
    },
    {
      id: 3,
      questionEn: "You've built MES from scratch using .NET, PHP, and SQL. How would you design a scalable architecture for an Industry 4.0 roadmap today?",
      questionEs: "Has construido MES desde cero. ¿Cómo diseñarías una arquitectura escalable para una hoja de ruta de Industria 4.0 hoy en día?",
      expectedKeywords: ["Microservices", "IoT", "Cloud", "Edge Computing", "IIoT", "Database Management", "Scalability"],
      contextHint: "Discuss the evolution from legacy MS SQL/PHP to modern REST APIs and IoT integration.",
      fullSuggestedResponseEn: "Today, I would design a scalable Industry 4.0 architecture using a microservices approach with IIoT edge computing. By leveraging modern REST APIs and cloud-ready database management, we can ensure high scalability and seamless communication between shop-floor sensors and enterprise-level analytics for real-time decision making."
    },
    {
      id: 4,
      questionEn: "Reducing WIP from $4.8M to $40K in 2 months is massive. What were the key metrics you implemented to monitor this in real-time?",
      questionEs: "Reducir el WIP de $4.8M a $40K es masivo. ¿Qué métricas clave implementaste para monitorear esto en tiempo real?",
      expectedKeywords: ["Inventory recovery", "Dashboard", "Power BI", "Traceability", "Efficiency", "ROI"],
      contextHint: "Don't just mention the result; explain the traceability logic that captured the losses.",
      fullSuggestedResponseEn: "The key was implementing a real-time inventory recovery dashboard using Power BI. I tracked granular traceability metrics at every station to identify bottlenecks and sorting errors. This visibility allowed for immediate recalibration of production flow, leading to a massive ROI and nearly eliminating multi-million dollar losses."
    }
  ];

  readonly currentQuestion = signal<InterviewQuestion>(this.questions[0]);
  readonly currentIndex = signal<number>(0);
  readonly totalQuestions = signal<number>(this.questions.length);
  readonly isSetupMode = signal<boolean>(true);
  readonly setupStep = signal<number>(1);
  readonly isLiveMode = signal<boolean>(false);
  readonly isRecording = signal<boolean>(false);
  readonly isProcessing = signal<boolean>(false);
  readonly hasAnalysis = signal<boolean>(false);
  readonly lastAnalysis = signal<AnalysisResult | null>(null);
  readonly lastAudioUrl = signal<string | null>(null);

  toggleSetupMode(val: boolean) {
    this.isSetupMode.set(val);
  }

  resetInterview() {
    this.currentIndex.set(0);
    this.lastAnalysis.set(null);
    this.lastAudioUrl.set(null);
    this.isSetupMode.set(false);
    this.hasAnalysis.set(false); // Also reset analysis state
  }

  nextQuestion() {
    if (this.currentIndex() < this.questions.length - 1) {
      this.currentIndex.update(i => i + 1);
      this.currentQuestion.set(this.questions[this.currentIndex()]);
      this.hasAnalysis.set(false);
    }
  }

  prevQuestion() {
    if (this.currentIndex() > 0) {
      this.currentIndex.update(i => i - 1);
      this.currentQuestion.set(this.questions[this.currentIndex()]);
      this.hasAnalysis.set(false);
    }
  }

  setRecording(state: boolean) {
    this.isRecording.set(state);
  }

  setProcessing(state: boolean) {
    this.isProcessing.set(state);
  }

  setAnalysisResult(result: AnalysisResult | null) {
    this.lastAnalysis.set(result);
    this.hasAnalysis.set(!!result);
    this.isProcessing.set(false);
  }

  setAudioUrl(url: string | null) {
    this.lastAudioUrl.set(url);
  }
}
