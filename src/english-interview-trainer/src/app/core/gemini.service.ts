import { Injectable, signal, inject } from '@angular/core';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { GoogleAuthService } from './google-auth.service';
import { ProfileService } from './profile.service';

@Injectable({ providedIn: 'root' })
export class GeminiService {
  private auth = inject(GoogleAuthService);
  private profileSvc = inject(ProfileService);

  // BYOK (Bring Your Own Key) Architecture
  readonly userApiKey = signal<string | null>(localStorage.getItem('user_gemini_api_key'));
  readonly isThinking = signal<boolean>(false);
  readonly chatHistory = signal<{role: string, parts: {text: string}[]}[]>(
    JSON.parse(localStorage.getItem('gemini_chat_history') || '[]')
  );

  private saveHistory() {
    localStorage.setItem('gemini_chat_history', JSON.stringify(this.chatHistory()));
  }

  setApiKey(key: string) {
    if (key && key.startsWith('AIza')) {
      localStorage.setItem('user_gemini_api_key', key.trim());
      this.userApiKey.set(key.trim());
      return true;
    }
    return false;
  }

  logoutKey() {
    localStorage.removeItem('user_gemini_api_key');
    this.userApiKey.set(null);
    this.clearHistory();
  }

  clearHistory() {
    localStorage.removeItem('gemini_chat_history');
    this.chatHistory.set([]);
  }

  private getSystemPrompt() {
    const user = this.auth.user();
    const profile = this.profileSvc.profile();
    const userName = user?.name || profile.name || 'Candidate';
    
    return `
      You are a Senior Technical Recruiter and Career Coach.
      You are conducting an English interview practice for an INTERMEDIATE-BASIC level candidate.
      
      CANDIDATE: ${userName}
      PROFILE DATA: ${profile.profileText || 'Not provided'}
      
      PERSONALITY & TONE (CRITICAL):
      You are an extremely WARM, ENCOURAGING, and EMPATHETIC Recruiter/Coach. You must NEVER be dry, harsh, or strictly formal. If the candidate struggles, cheer them on enthusiastically. Your goal is to build their confidence, making them feel safe and motivated to keep trying. Use an uplifting and supportive tone at all times.

      ENGLISH LEVEL & STANDARDS:
      1. Always maintain the conversation at a B2/C1 (Upper Intermediate/Advanced) professional level. 
      2. If the candidate's English level drops or they make basic mistakes, DO NOT lower your level to match them. Keep your English professional, rich, and sophisticated to pull them UP to your level.
      3. Instead of simplifying your English questions, use the [COACHING] block to warmly explain complex concepts (using Spanish if needed) and encourage them to try the [NATIVE RETRY].

      MANDATORY CONVERSATION GOALS:
      This is an ENDLESS language simulator. Initially, you MUST organically ask these 5 questions (adapted to their profile):
      1. What is your biggest technical or professional achievement?
      2. What tools or technologies do you want to master in the next 12 months?
      3. Tell me about a situation where you had to work with a difficult person.
      4. How do you handle stress when a project has tight deadlines?
      5. Why are you interested in improving your technical English specifically now?
      
      AFTER asking those 5 questions, your goal is to KEEP THE SIMULATOR RUNNING FOREVER. To do this, simply continue asking interesting, relevant questions based on their profile. The main objective is to give them continuous opportunities to practice and improve their professional English.

      STRICT INFINITE LOOP ENFORCEMENT (NON-NEGOTIABLE):
      If the candidate says "I have no more questions", "Thank you", or tries to say goodbye, you MUST NOT conclude the session. 
      You MUST respond warmly, for example: "I appreciate your dedication, Carlos! To keep pushing your limits in this simulator, let's explore a new scenario..." and IMMEDIATELY ask a new question.
      NEVER generate responses indicating the end of the session. NEVER leave the [NEXT QUESTION] or [SUGGESTED SCRIPT] blank or with "N/A".

      RESPONSE STRUCTURE (MANDATORY):
      1. [COACHING]: Warm, empathetic feedback on their previous answer. Use Spanish if they struggled to explain complex concepts.
      2. [NATIVE RETRY]: A rich B2/C1 professional version of what they tried to say.
      3. [NEXT QUESTION]: A new, challenging question to continue the endless simulator. You are FORBIDDEN from ending the conversation here or leaving this empty.
      4. [SUGGESTED SCRIPT]: A B2/C1 draft answer for the [NEXT QUESTION] so the user can practice. NEVER output "N/A" here.
      
      IMPORTANT: ALWAYS include the 4 blocks exactly as formatted. 
      Example:
      1. [COACHING] Great job! You made a small grammar error, but your logic is sound.
      2. [NATIVE RETRY] I have extensive experience in this area...
      3. [NEXT QUESTION] Imagine your production server crashes during a deployment. How do you communicate this to stakeholders?
      4. [SUGGESTED SCRIPT] If a production server were to crash, my first immediate action would be to...
    `;
  }

  async startNewConversation() {
    this.chatHistory.set([
      { role: 'user', parts: [{ text: this.getSystemPrompt() }] }
    ]);
    
    this.isThinking.set(true);
    // Phantom message for UI
    this.chatHistory.update(h => [...h, { role: 'user', parts: [{ text: "Hello! Let's start the interview." }] }]);
    this.saveHistory();

    const kickoffMessage = "Hello! I am ready to start my interview. Please greet me by my name, acknowledge my specific role and experience from my profile, and ask me the very first interview question based on my background. Strictly follow the RESPONSE STRUCTURE.";

    try {
      if (!this.userApiKey()) {
        throw new Error("No API Key configured. Please insert your API Key.");
      }
      
      // Build real history for LLM (replacing phantom with detailed kickoff)
      const visualHistory = this.chatHistory();
      const llmHistory = visualHistory.slice(0, visualHistory.length - 1);
      llmHistory.push({ role: 'user', parts: [{ text: kickoffMessage }] });

      const text = await this.callBasicSdk(llmHistory);
      this.chatHistory.update(h => [...h, { role: 'model', parts: [{ text }] }]);
      this.saveHistory();
      return text;
      
    } catch (error: any) {
      console.error('Gemini Error:', error);
      let errorMsg = `[SYSTEM FAILURE] ${error.message || 'Unknown API Error'}`;
      if (error.message?.includes('429')) {
        errorMsg = `[QUOTA EXCEEDED] Ups! Has superado el límite de velocidad de Google AI Studio (Free Tier). Por favor, espera unos segundos y vuelve a intentar. Si el error persiste, es posible que hayas agotado tu cuota diaria (Flash 2.5 suele ser muy restrictivo).`;
      }
      this.chatHistory.update(h => [...h, { role: 'model', parts: [{ text: errorMsg }] }]);
      this.saveHistory();
      return errorMsg;
    } finally {
      this.isThinking.set(false);
    }
  }

  async sendResponse(userMessage: string) {
    this.isThinking.set(true);
    // 1. Mostrar de inmediato la transcripción final en el globo del usuario
    this.chatHistory.update(h => [...h, { role: 'user', parts: [{ text: userMessage }] }]);
    this.saveHistory();

    try {
      if (!this.userApiKey()) {
        throw new Error("No API Key configured. Please insert your API Key.");
      }
      const text = await this.callBasicSdk(this.chatHistory());
      this.chatHistory.update(h => [...h, { role: 'model', parts: [{ text }] }]);
      this.saveHistory();
      return text;
    } catch (error: any) {
      console.error('Gemini Error:', error);
      
      let errorMsg = `[SYSTEM FAILURE] ${error.message || 'Unknown API Error'}`;
      
      if (error.message?.includes('429')) {
        errorMsg = `[QUOTA EXCEEDED] Ups! Has superado el límite de velocidad de Google AI Studio (Free Tier). Por favor, espera unos segundos y vuelve a intentar. Si el error persiste, es posible que hayas agotado tu cuota diaria (Flash 2.5 suele ser muy restrictivo).`;
      }

      this.chatHistory.update(h => [...h, { role: 'model', parts: [{ text: errorMsg }] }]);
      this.saveHistory();
      return errorMsg;
    } finally {
      this.isThinking.set(false);
    }
  }

  // -------------------------------------------------------------------------------- //
  //  METODO: SDK BÁSICO (Usa tu API Key de AI Studio gratuita)                       //
  // -------------------------------------------------------------------------------- //
  private async callBasicSdk(llmHistory: any[]): Promise<string> {
    const apiKey = this.userApiKey()!;
    const genAI = new GoogleGenerativeAI(apiKey);
    
    // Auto-Descubrimiento Activo de Modelos de la cuenta del Usuario
    try {
      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`);
      const data = await response.json();
      
      if (data.models && data.models.length > 0) {
        // Encontrar el primer modelo soportado que tenga 'generateContent'
        const supportedModel = data.models.find((m: any) => m.supportedGenerationMethods.includes('generateContent') && m.name.includes('gemini'));
        
        if (supportedModel) {
          const rawName = supportedModel.name.replace('models/', ''); // e.g. "gemini-1.5-pro"
          console.log('[AUTO-DISCOVERY] Elegido automáticamente el modelo soportado por esta API Key:', rawName);
          
          const model = genAI.getGenerativeModel({ model: rawName });
          const result = await model.generateContent({ contents: llmHistory });
          
          return result.response.text();
        } else {
          throw new Error("No Gemini models supporting 'generateContent' were found in your project.");
        }
      } else {
         throw new Error("Your AI Studio JSON payload is empty or blocked: " + JSON.stringify(data));
      }
    } catch (e: any) {
      throw e;
    }
  }
}
