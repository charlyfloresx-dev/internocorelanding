import { Component, inject, signal, effect, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { GoogleAuthService } from '../../core/google-auth.service';
import { AudioService } from '../../core/audio.service';
import { GeminiService } from '../../core/gemini.service';
import { InterviewService } from '../../core/interview.service';

@Component({
  selector: 'app-trainer-v3',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="w-full h-[100dvh] flex flex-col p-3 sm:p-6 md:p-8 font-inter animate-in fade-in duration-700 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-primary/5 via-transparent to-transparent overflow-hidden">
      
      <!-- AUDITOR HEADER -->
      <div class="flex items-center justify-between mb-8 shrink-0">
        <div class="flex items-center gap-3 sm:gap-4">
          <div class="w-10 h-10 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl bg-gradient-to-br from-primary to-indigo-600 flex items-center justify-center shadow-xl shadow-primary/20 p-2 sm:p-2.5">
             <!-- InternoCore SVG Logo -->
             <svg viewBox="0 0 630 630" class="w-full h-full">
                <path fill="#FFFFFF" d="M338.272552,413.107239 C330.839233,417.587891 323.635864,421.750458 316.649078,426.249237 C314.147339,427.860046 312.337738,427.765350 309.887360,426.264191 C295.698029,417.571625 281.434052,409.000305 267.160767,400.445618 C251.387711,390.992035 235.610611,381.544006 219.750412,372.238220 C217.142288,370.707947 216.119690,369.030518 216.127686,365.948029 C216.232727,325.462097 216.233948,284.975708 216.122742,244.489822 C216.113312,241.053635 217.221832,239.234848 220.231827,237.466171 C239.426285,226.187683 258.471649,214.655045 277.546661,203.173767 C288.055878,196.848251 298.572174,190.532074 308.986481,184.052917 C311.865021,182.262070 314.044312,182.169617 317.112610,184.033737 C347.010559,202.198257 377.041809,220.143265 406.979431,238.242828 C408.214264,238.989395 409.692230,240.630295 409.716217,241.880264 C409.929535,252.985809 409.840302,264.097137 409.840302,275.417236 C399.728363,275.417236 390.114716,275.417236 379.629395,275.417236 C379.629395,270.605988 379.466278,265.855347 379.690308,261.123047 C379.825562,258.265961 378.890594,256.633087 376.361328,255.174744 C359.512085,245.459778 342.747772,235.596924 325.998749,225.709518 C323.027374,223.955460 320.035461,222.115005 317.450348,219.859161 C314.357361,217.160156 311.853790,217.796646 308.676056,219.740143 C288.991638,231.779083 269.163849,243.584183 249.523483,255.693604 C247.929001,256.676697 246.492538,259.351105 246.479782,261.249664 C246.282745,290.570831 246.283813,319.893951 246.455124,349.215363 C246.465103,350.921570 247.898575,353.308319 249.380890,354.213226 C269.629700,366.574463 289.974365,378.780426 310.410675,390.829193 C311.852356,391.679169 314.641815,391.749207 316.055511,390.914032 C336.233826,378.992950 356.255341,366.806763 376.398499,354.825500 C378.900482,353.337280 379.792572,351.701019 379.664124,348.843384 C379.426453,343.556030 379.596100,338.250366 379.596100,332.514282 C389.774567,332.514282 399.497437,332.514282 409.861481,332.514282 C409.861481,341.669586 409.277893,350.991852 410.044250,360.201813 C410.669006,367.710052 408.017487,371.654205 401.523926,375.356476 C380.304047,387.455170 359.532196,400.339630 338.272552,413.107239 z"></path>
                <path fill="#FFFFFF" d="M283.442566,467.396484 C262.120392,454.618988 241.163971,441.949097 220.106964,429.448669 C217.361130,427.818573 216.058136,426.174622 216.139130,422.819214 C216.379929,412.842804 216.225449,402.856842 216.225449,391.756836 C222.217041,395.304138 227.542450,398.403046 232.815720,401.588226 C257.871216,416.722260 282.948395,431.821198 307.919464,447.093445 C311.573212,449.328094 314.302826,449.486786 318.146393,447.152618 C353.730103,425.542633 389.440826,404.141174 425.195038,382.813904 C427.876617,381.214325 428.730133,379.505707 428.691589,376.506409 C428.524597,363.518463 428.598999,350.527435 428.586151,337.537506 C428.584564,335.927002 428.585968,334.316498 428.585968,332.396912 C438.836426,332.396912 448.441071,332.396912 458.523712,332.396912 C458.610016,333.981537 458.769440,335.570068 458.771973,337.158905 C458.801636,355.821960 458.725983,374.485779 458.897614,393.147400 C458.927399,396.388306 457.952759,398.185547 455.136902,399.869202 C417.647003,422.284607 380.238403,444.835968 342.810883,467.355621 C334.399323,472.416779 325.916809,477.366089 317.620453,482.609650 C314.193390,484.775604 311.802094,485.204559 308.022400,482.503662 C300.315674,476.996521 291.900421,472.480896 283.442566,467.396484 z"></path>
                <path fill="#FFFFFF" d="M235.082947,206.927277 C228.952850,210.641693 223.126678,214.158249 216.727325,218.020782 C216.524139,216.346359 216.258240,215.145996 216.251907,213.944244 C216.206238,205.280014 216.421875,196.607849 216.104980,187.954666 C215.970200,184.274109 217.271194,182.332092 220.342957,180.502716 C247.689163,164.216888 275.244720,148.247147 302.042664,131.096878 C310.486816,125.692780 316.027954,126.108505 324.255096,131.165054 C367.352722,157.653641 410.864594,183.469391 454.313843,209.382568 C457.737549,211.424484 458.994995,213.643417 458.939392,217.647873 C458.696472,235.140076 458.824310,252.637421 458.817810,270.132904 C458.817200,271.761902 458.817749,273.390900 458.817749,275.310699 C448.646667,275.310699 438.902893,275.310699 428.537384,275.310699 C428.537384,266.584900 428.525909,257.974396 428.541718,249.363983 C428.551178,244.200806 428.460663,239.031372 428.688995,233.876892 C428.829071,230.714569 427.883118,228.740555 425.011810,227.029099 C388.901855,205.505783 352.871704,183.848557 316.828644,162.213028 C314.669861,160.917175 312.924957,159.900711 310.120148,161.612503 C285.282288,176.771469 260.315552,191.719269 235.082947,206.927277 z"></path>
                <path fill="#FFFFFF" d="M167.237305,339.999878 C167.231201,317.851624 167.280746,296.203033 167.153702,274.555511 C167.136078,271.554321 167.920334,269.757721 170.640457,268.201569 C179.381302,263.200989 187.936111,257.875275 197.124573,252.336243 C197.124573,306.893494 197.124573,360.744293 197.124573,415.345459 C187.396072,409.520905 178.017197,404.040222 168.842422,398.236908 C167.735657,397.536835 167.295074,395.094055 167.285614,393.454681 C167.183884,375.803589 167.230759,358.151611 167.237305,339.999878 z"></path>
                <path fill="#FFFFFF" d="M197.510864,222.768204 C198.422928,228.129318 196.353119,231.068268 191.985764,233.426636 C185.028687,237.183426 178.436737,241.614136 171.662277,245.713440 C170.443161,246.451126 169.088699,246.965179 167.188995,247.872879 C167.188995,236.271759 167.036346,225.319336 167.357971,214.380859 C167.404770,212.788727 169.422058,210.785721 171.032471,209.786926 C179.466415,204.555984 188.063080,199.587387 197.508453,193.991287 C197.508453,203.847900 197.508453,213.075729 197.510864,222.768204 z"></path>
             </svg>
          </div>
          <div class="flex flex-col">
             <span class="text-[7px] sm:text-[10px] font-black uppercase tracking-[0.2em] sm:tracking-[0.4em] text-primary">InternoCore Recruiting</span>
             <h1 class="text-base sm:text-xl font-black text-white tracking-tight italic">Technical Auditor</h1>
          </div>
        </div>

        @if (auth.isAuthenticated()) {
           <div class="flex items-center gap-2 sm:gap-3">
             <div class="flex items-center gap-2 sm:gap-3 p-1 sm:p-1.5 pr-2 sm:pr-4 rounded-xl sm:rounded-2xl bg-white/5 border border-white/5 backdrop-blur-md">
                <img [src]="auth.user()?.picture" class="w-6 h-6 sm:w-8 sm:h-8 rounded-lg sm:rounded-xl border border-white/10 shadow-lg" alt="Avatar">
                <div class="hidden sm:flex flex-col">
                   <span class="text-[8px] font-black text-white/40 uppercase tracking-widest leading-none mb-0.5">Candidate</span>
                   <span class="text-[10px] font-black text-white tracking-tight">{{ auth.user()?.name }}</span>
                </div>
             </div>
             
             <!-- LOGOUT / RESET BUTTON -->
             <button (click)="logoutAll()" class="w-8 h-8 sm:w-10 sm:h-10 rounded-xl sm:rounded-2xl bg-rose-500/10 hover:bg-rose-500 text-rose-500 hover:text-white flex items-center justify-center transition-all border border-rose-500/20" title="Sign Out">
                <span class="material-icons !text-base sm:!text-lg">logout</span>
             </button>
           </div>
        } @else {
           <div id="google-login-v3" class="scale-75 sm:scale-90 origin-right transition-transform hover:scale-100"></div>
        }
      </div>

      <!-- CHAT STREAM -->
      <div class="flex-1 overflow-hidden flex flex-col gap-6 relative">
          
          <div id="chat-scroller" class="flex-1 overflow-y-auto custom-scrollbar pr-2 sm:pr-4 flex flex-col gap-4 sm:gap-8 pb-64 sm:pb-72 scroll-smooth">
             @for (msg of gemini.chatHistory(); track $index) {
                @if ($index > 0) {
                   <div class="flex flex-col gap-2 animate-in slide-in-from-bottom-2 duration-300 w-full"
                        [class.items-end]="msg.role === 'user'"
                        [class.items-start]="msg.role === 'model'">
                      
                      <div class="max-w-[92%] sm:max-w-[85%] md:max-w-[75%] p-4 sm:p-5 md:p-6 rounded-[24px] sm:rounded-[32px] shadow-3xl relative border border-white/10 group group-bubble"
                           [ngClass]="msg.role === 'model' ? 'bg-primary/20 backdrop-blur-3xl rounded-tl-none' : 'bg-white/5 rounded-tr-none'">
                         
                         @if (msg.role === 'model') {
                            <!-- INTERVIEWER QUESTION (PRIMARY DIALOGUE) -->
                            <div class="mb-4">
                               <p class="text-white font-medium text-base md:text-lg leading-relaxed tracking-wide italic">
                                 {{ parseMainText(msg.parts[0].text) }}
                               </p>
                            </div>

                            <!-- TOGGLE FOR ANALYTICS -->
                            <div class="flex flex-col gap-3">
                                <button (click)="toggleMessage($index)" 
                                        class="w-fit flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/5 hover:bg-white/10 transition-all group">
                                  <span class="material-icons text-[14px] text-primary group-hover:rotate-12 transition-transform">insights</span>
                                  <span class="text-[9px] font-black uppercase text-white/50 tracking-widest">{{ expandedMessages().has($index) ? 'Ocultar Análisis' : 'Ver Análisis y Sugerencia' }}</span>
                                  <span class="material-icons text-[14px] text-white/20">{{ expandedMessages().has($index) ? 'expand_less' : 'expand_more' }}</span>
                                </button>

                                @if (expandedMessages().has($index)) {
                                   <div class="animate-in slide-in-from-top-2 duration-300 flex flex-col gap-4 mt-2">
                                      <!-- COACHING BLOCK -->
                                      @if (getCoaching(msg.parts[0].text); as coaching) {
                                         <div class="p-4 bg-rose-500/5 border-l-2 border-rose-500 rounded-xl">
                                            <div class="flex items-center gap-2 mb-2">
                                               <span class="material-icons text-rose-500 !text-[12px]">analytics</span>
                                               <span class="text-[8px] font-black uppercase text-rose-500 tracking-widest">Feedback del Coach</span>
                                            </div>
                                            <p class="text-[11px] font-medium text-white/70 italic leading-relaxed">{{ coaching }}</p>
                                         </div>
                                      }

                                      <!-- NATIVE RETRY -->
                                      @if (getNativeRetry(msg.parts[0].text); as retry) {
                                         <div class="p-4 bg-indigo-500/5 border-l-2 border-indigo-500 rounded-xl">
                                            <div class="flex items-center gap-2 mb-2">
                                               <span class="material-icons text-indigo-400 !text-[12px]">record_voice_over</span>
                                               <span class="text-[8px] font-black uppercase text-indigo-400 tracking-widest">Fraseo Nativo (B2/C1)</span>
                                            </div>
                                            <p class="text-[11px] font-medium text-indigo-100 italic leading-relaxed">"{{ retry }}"</p>
                                         </div>
                                      }

                                      <!-- SUGGESTED SCRIPT -->
                                      @if (getSuggestedScript(msg.parts[0].text); as script) {
                                         <div class="p-4 bg-emerald-500/10 rounded-2xl border border-emerald-500/20 shadow-inner">
                                            <div class="flex items-center gap-2 mb-2">
                                               <span class="material-icons text-emerald-400 !text-[12px]">psychology_alt</span>
                                               <span class="text-[8px] font-black uppercase text-emerald-400 tracking-widest">Respuesta Sugerida</span>
                                            </div>
                                            <p class="text-[12px] font-semibold text-emerald-100/90 italic">"{{ script }}"</p>
                                         </div>
                                      }
                                   </div>
                                }
                            </div>
                         } @else {
                            <div class="flex flex-col gap-3 relative">
                               <p class="font-medium text-sm leading-relaxed whitespace-pre-wrap italic">
                                  @if (msg.parts[0].text !== "Hello! Let's start the interview.") {
                                     "
                                     @for (w of getColoredWords(msg.parts[0].text); track $index) {
                                        <span [class]="w.color">{{ w.word }} </span>
                                     }
                                     "
                                  } @else {
                                     <span class="text-white">"{{ msg.parts[0].text }}"</span>
                                  }
                               </p>
                            </div>
                         }

                         <!-- Unified Floating Audio Pills -->
                         @if (msg.role === 'model') {
                            <div class="absolute -bottom-4 sm:-bottom-5 right-4 sm:right-6 flex items-center gap-1.5 bg-[#0F131C] border border-white/10 px-3 sm:px-4 py-1.5 rounded-full shadow-2xl z-20">
                              <button (click)="audio.readText(parseMainText(msg.parts[0].text))" title="Reproducir audio"
                                      class="text-indigo-400 hover:text-indigo-300 transition-all hover:scale-110 flex items-center gap-1.5">
                                 <span class="material-icons !text-[12px] sm:!text-[14px]">volume_up</span>
                                 <span class="text-[8px] font-black uppercase tracking-widest hidden sm:inline-block">Listen</span>
                              </button>
                              <div class="w-px h-3 bg-white/10 mx-1"></div>
                              <button (click)="audio.stopSpeaking()" title="Detener audio"
                                      class="text-white/40 hover:text-rose-400 transition-all hover:scale-110 flex items-center gap-1.5">
                                 <span class="material-icons !text-[12px] sm:!text-[14px]">volume_off</span>
                              </button>
                            </div>
                         } @else if (msg.parts[0].text !== "Hello! Let's start the interview.") {
                            <div class="absolute -top-4 sm:-top-5 right-4 sm:right-6 flex items-center gap-1.5 bg-[#0F131C] border border-white/10 px-3 sm:px-4 py-1.5 rounded-full shadow-2xl z-20">
                               <button (click)="audio.playRecording()" title="Mi Voz" class="text-white/50 hover:text-white transition-all hover:scale-110 flex items-center gap-1.5">
                                  <span class="material-icons !text-[12px] sm:!text-[14px]">headphones</span>
                                  <span class="text-[8px] font-black uppercase tracking-widest hidden sm:inline-block">Mi Voz</span>
                               </button>
                               <div class="w-px h-3 bg-white/10 mx-1"></div>
                               <button (click)="audio.readText(msg.parts[0].text)" title="Ideal" class="text-indigo-400 hover:text-indigo-300 transition-all hover:scale-110 flex items-center gap-1.5">
                                  <span class="material-icons !text-[12px] sm:!text-[14px]">volume_up</span>
                                  <span class="text-[8px] font-black uppercase tracking-widest hidden sm:inline-block">Ideal</span>
                               </button>
                               <div class="w-px h-3 bg-white/10 mx-1"></div>
                               <button (click)="audio.stopSpeaking()" title="Detener audio" class="text-white/40 hover:text-rose-400 transition-all hover:scale-110 flex items-center gap-1.5">
                                  <span class="material-icons !text-[12px] sm:!text-[14px]">volume_off</span>
                               </button>
                            </div>
                         }
                      </div>

                       <div class="flex flex-col items-end gap-1 px-4 mt-2">
                          @if (msg.role === 'user' && msg.parts[0].text !== "Hello! Let's start the interview.") {
                             <!-- Minimalist Floating Footer -->
                             <div class="flex items-center gap-6 mb-1 opacity-70 hover:opacity-100 transition-opacity">
                                <!-- Minimal Metrics -->
                                <div class="flex items-center gap-4">
                                   <div class="flex flex-col items-center">
                                      <span class="text-[5px] font-black uppercase text-white/30 tracking-[0.3em] mb-[2px]">Confidence</span>
                                      <span class="text-[10px] font-black text-white/90 tracking-tighter leading-none">{{ getMockScore(msg.parts[0].text) }}%</span>
                                   </div>
                                   <div class="w-[1px] h-3 bg-white/10"></div>
                                   <div class="flex flex-col items-center">
                                      <span class="text-[5px] font-black uppercase text-white/30 tracking-[0.3em] mb-[2px]">Accuracy</span>
                                      <span class="text-[10px] font-black text-indigo-400/90 tracking-tighter leading-none">{{ getMockScore(msg.parts[0].text) - 13 }}%</span>
                                   </div>
                                </div>
                                
                                <div class="w-1 h-1 rounded-full bg-white/10"></div>
                                
                                <!-- Ghost Dashboard Text -->
                                <button class="text-[6px] font-black uppercase text-white/5 hover:text-white/20 tracking-[0.4em] transition-colors leading-none" title="Analizar en Dashboard">
                                   Dashboard
                                </button>
                             </div>
                          }

                          <span class="text-[8px] font-black uppercase text-white/20 tracking-[0.5em]">
                             {{ msg.role === 'user' ? (auth.user()?.name || 'Candidate') : 'InternoCore Recruiter AI' }}
                          </span>
                       </div>
                    </div>
                }
             }

           <!-- CHAT HEADER -->
           <div class="flex items-center justify-between px-2 sm:px-4 mb-4">
              <span class="text-[8px] sm:text-[10px] font-black uppercase text-white/20 sm:text-white/30 tracking-[0.2em] sm:tracking-[0.3em]">Protocolo V3: Activo</span>
              <div class="flex gap-1.5 sm:gap-2">
                 <button (click)="changeProfile()" class="flex items-center gap-1.5 px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg sm:rounded-xl bg-white/5 hover:bg-white/10 text-white/60 hover:text-white transition-all border border-white/10">
                    <span class="material-icons !text-xs">person_add</span>
                    <span class="text-[8px] sm:text-[9px] font-black uppercase tracking-widest hidden xs:inline">Perfil</span>
                 </button>
                 <button (click)="resetAndRestart()" class="flex items-center gap-1.5 px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg sm:rounded-xl bg-rose-500/5 hover:bg-rose-500/20 text-rose-400/80 transition-all border border-rose-500/10">
                    <span class="material-icons !text-xs">restart_alt</span>
                    <span class="text-[8px] sm:text-[9px] font-black uppercase tracking-widest hidden xs:inline">Reset</span>
                 </button>
              </div>
           </div>

             @if (gemini.isThinking()) {
                <div class="flex items-center gap-5 p-7 rounded-[40px] bg-primary/5 border border-primary/10 w-fit animate-pulse ml-4">
                   <div class="flex gap-2">
                      <div class="w-2.5 h-2.5 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]"></div>
                      <div class="w-2.5 h-2.5 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]"></div>
                      <div class="w-2.5 h-2.5 rounded-full bg-primary animate-bounce"></div>
                   </div>
                   <span class="text-xs font-black uppercase text-primary tracking-[0.2em] italic">Architectural Evaluation in progress...</span>
                </div>
             }
          </div>

          <!-- COMMAND CENTER -->
          <div class="absolute bottom-6 sm:bottom-0 left-0 right-0 p-2 sm:p-8 pb-6 sm:pb-10 bg-gradient-to-t from-surface-card via-surface-card/95 to-transparent flex flex-col items-center gap-2 sm:gap-6 z-30">
             
             @if (!auth.isAuthenticated()) {
                <div class="px-4 py-3 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 animate-in fade-in zoom-in duration-500 mx-4">
                   <span class="material-icons text-rose-500 text-sm animate-pulse">lock</span>
                   <p class="text-[9px] font-black text-rose-500 uppercase tracking-widest text-center">Global Authentication Required</p>
                </div>
             } @else if (!gemini.userApiKey()) {
                <div class="w-full max-w-xs sm:max-w-lg px-4 sm:px-6 py-4 sm:py-5 bg-indigo-500/10 border border-indigo-500/20 backdrop-blur-md rounded-2xl flex flex-col items-center gap-3 sm:gap-4 animate-in fade-in zoom-in duration-500">
                   <div class="flex items-center gap-2">
                      <span class="material-icons text-indigo-400 text-xs sm:text-sm">vpn_key</span>
                      <p class="text-[9px] sm:text-[10px] font-black text-indigo-400 uppercase tracking-widest text-center">BYOK Security Protocol</p>
                   </div>
                   <div class="flex w-full gap-1.5 sm:gap-2">
                      <input #apiKeyInput type="password" placeholder="Key..." autocomplete="off" class="flex-1 bg-black/50 font-mono border border-white/10 rounded-lg sm:rounded-xl px-3 sm:px-4 py-2 text-xs sm:text-sm text-white tracking-widest focus:outline-none focus:border-indigo-500 transition-colors">
                      <button (click)="saveKeyAndStart(apiKeyInput.value)" class="px-3 sm:px-6 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-[10px] sm:text-xs font-black uppercase tracking-widest rounded-lg sm:rounded-xl transition-all shadow-lg shadow-indigo-500/20">Connect</button>
                   </div>
                   <a href="https://aistudio.google.com/app/apikey" target="_blank" class="text-[8px] sm:text-[9px] text-white/40 hover:text-white/80 underline decoration-white/20 transition-colors flex items-center gap-1"><span class="material-icons !text-[10px]">open_in_new</span> Key Studio</a>
                </div>
             } @else {
                <div class="flex flex-col items-center gap-2 sm:gap-4">
                   <!-- STOP AI SPEECH BUTTON -->
                   @if (audio.isSpeaking()) {
                      <button (click)="audio.stopSpeaking()" 
                              class="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-full flex items-center gap-2 animate-bounce shadow-lg shadow-rose-600/50 border border-white/10 mb-1">
                         <span class="material-icons !text-sm">volume_off</span>
                         <span class="text-[9px] font-black uppercase tracking-widest">Stop AI Speaking</span>
                      </button>
                   }
                   
                   @if (interview.isRecording()) {
                      <div class="flex items-center gap-2 h-10 px-6 rounded-full bg-rose-500/10 border border-rose-500/20 mb-2">
                         <div class="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></div>
                         <span class="text-[10px] font-black text-rose-500 uppercase tracking-widest">Listening Candidate...</span>
                      </div>
                   }

                   <div class="flex items-center gap-4 sm:gap-8">
                      <!-- LIVE MODE TOGGLE -->
                      <button (click)="toggleLiveMode()" 
                              class="w-12 h-12 sm:w-14 sm:h-14 rounded-xl sm:rounded-2xl flex items-center justify-center transition-all duration-300 border backdrop-blur-md relative group"
                              [ngClass]="interview.isLiveMode() ? 'bg-primary/20 border-primary shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)]' : 'bg-white/5 border-white/10' + (!interview.isLiveMode() ? ' opacity-40 hover:opacity-100' : '')">
                         <span class="material-icons text-lg sm:text-xl" [class.text-primary]="interview.isLiveMode()" [class.text-white]="!interview.isLiveMode()">auto_awesome</span>
                         @if (interview.isLiveMode()) {
                            <div class="absolute -top-1 -right-1 w-2.5 h-2.5 sm:w-3 h-3 bg-primary rounded-full animate-ping"></div>
                         }
                      </button>

                      <button (click)="toggleRecording()" 
                              class="w-16 h-16 sm:w-24 sm:h-24 rounded-full flex items-center justify-center transition-all duration-500 hover:scale-105 active:scale-90 shadow-[0_0_50px_rgba(var(--primary-rgb),0.2)] relative overflow-hidden group"
                              [ngClass]="interview.isRecording() ? 'bg-rose-600 text-white' : 'bg-primary text-white'">
                         
                         <span class="material-icons !text-3xl sm:!text-5xl z-10">{{ interview.isRecording() ? 'stop' : 'mic' }}</span>
                         <div class="absolute inset-0 bg-white/10 scale-0 group-hover:scale-100 transition-transform duration-500 rounded-full"></div>
                      </button>

                      <div class="flex flex-col max-w-[120px] sm:max-w-md w-full">
                         <span class="text-[9px] sm:text-[12px] font-black uppercase tracking-widest sm:tracking-[0.2em] mb-0.5 sm:mb-1"
                               [ngClass]="interview.isRecording() ? 'text-rose-400 animate-pulse' : 'text-white'">
                            {{ interview.isRecording() ? '🔴 LISTENING' : (interview.isLiveMode() ? '✨ LIVE' : 'AUDIT') }}
                         </span>
                         <span class="text-[10px] sm:text-xs font-medium text-white/60 sm:text-white/70 italic leading-tight line-clamp-2">
                            {{ interview.isRecording() ? (audio.liveTranscript() || 'Monitoring...') : (interview.isLiveMode() ? 'Hands-free...' : 'Monitoring real-time.') }}
                         </span>
                      </div>
                   </div>
                </div>
             }
          </div>

      </div>
    </div>
  `,
  styles: [`
    .custom-scrollbar::-webkit-scrollbar { width: 4px; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.05); border-radius: 10px; }
  `]
})
export class TrainerV3Component {
  protected auth = inject(GoogleAuthService);
  protected audio = inject(AudioService);
  protected gemini = inject(GeminiService);
  protected interview = inject(InterviewService);
  private cdr = inject(ChangeDetectorRef);

  readonly expandedMessages = signal<Set<number>>(new Set());

  constructor() {
    effect(() => {
      if (this.auth.isAuthenticated() && this.gemini.userApiKey() && this.gemini.chatHistory().length === 0) {
        this.startConversation();
      }
      
      if (!this.auth.isAuthenticated()) {
        setTimeout(() => this.auth.renderButton('google-login-v3'), 500);
      }

      if (this.gemini.chatHistory().length > 0) {
        setTimeout(() => this.scrollToBottom(), 150);
        this.cdr.markForCheck();
      }
    }, { allowSignalWrites: true });

    this.setupLiveAutoStop();
  }

  ngOnDestroy() {
    this.audio.stopSpeaking();
  }

  getMockScore(text: string): number {
    let hash = 0;
    for (let i = 0; i < text.length; i++) hash += text.charCodeAt(i);
    return 70 + (hash % 28); // Score between 70 and 97
  }

  getColoredWords(text: string): {word: string, color: string}[] {
    return text.split(' ').filter(w => w.trim().length > 0).map(word => {
      let hash = 0;
      const cleanWord = word.replace(/[^a-zA-Z]/g, '').toLowerCase();
      for (let i = 0; i < cleanWord.length; i++) hash += cleanWord.charCodeAt(i);
      
      let color = 'text-emerald-400 font-semibold'; // Optimal
      if (cleanWord.length > 3) {
        if (hash % 11 === 0) color = 'text-rose-400 font-bold decoration-rose-500/50 underline underline-offset-4'; // Mispronounced/Missed
        else if (hash % 5 === 0) color = 'text-yellow-400 font-semibold'; // Needs attention
      }
      
      return { word, color };
    });
  }

  resetAndRestart() {
    if (confirm('¿Seguro que quieres reiniciar la entrevista? Se borrará todo el progreso actual.')) {
      this.gemini.clearHistory();
      this.startConversation();
    }
  }

  changeProfile() {
    if (confirm('¿Quieres cambiar de perfil? Regresarás al paso de configuración inicial.')) {
      this.gemini.clearHistory();
      this.interview.isSetupMode.set(true);
      this.interview.setupStep.set(1);
    }
  }

  toggleMessage(index: number) {
    const next = new Set(this.expandedMessages());
    if (next.has(index)) next.delete(index);
    else next.add(index);
    this.expandedMessages.set(next);
  }

  saveKeyAndStart(key: string) {
    if (this.gemini.setApiKey(key)) {
       this.startConversation();
    } else {
       alert('Invalid API Key format. Must start with AIza...');
    }
  }

  logoutAll() {
    this.auth.logout();
    this.gemini.logoutKey();
  }

  private liveTimer: any = null;

  toggleLiveMode() {
    this.interview.isLiveMode.update(v => !v);
    if (this.interview.isLiveMode()) {
       if (!this.interview.isRecording()) {
         this.toggleRecording();
       }
    }
  }

  // Effect to handle Live Mode logic
  private setupLiveAutoStop() {
    effect(() => {
      const isLive = this.interview.isLiveMode();
      const transcript = this.audio.liveTranscript();
      const isRecording = this.interview.isRecording();

      if (isLive && isRecording && transcript.trim().length > 0) {
        // Reset the "silence" timer every time the transcript evolves
        if (this.liveTimer) clearTimeout(this.liveTimer);
        this.liveTimer = setTimeout(() => {
          if (this.interview.isLiveMode() && this.interview.isRecording()) {
            this.toggleRecording(); // Stop and Send automatically!
          }
        }, 1800); // 1.8 seconds of silence trigger the send
      }
    }, { allowSignalWrites: true });
  }

  async startConversation() {
    const introText = await this.gemini.startNewConversation();
    if (introText.includes('[SYSTEM FAILURE]')) {
      alert('Error inicial: Por favor verifica tu API Key.');
      this.interview.setupStep.set(2);
      this.interview.isSetupMode.set(true);
      return;
    }
    this.processAIResponse(introText);
  }

  private processAIResponse(text: string) {
    if (text.includes('[QUOTA EXCEEDED]')) {
       this.interview.isLiveMode.set(false); // Stop live loop to avoid spamming
       return;
    }
    const cleaned = this.parseMainText(text);
    this.audio.readText(cleaned, () => {
      // IF LIVE MODE IS ON: start listening immediately after AI finishes
      if (this.interview.isLiveMode()) {
        this.toggleRecording();
      }
    });
    this.cdr.markForCheck();
  }

  async toggleRecording() {
    if (this.interview.isRecording()) {
      this.interview.setRecording(false);
      this.interview.setProcessing(true);
      
      const result = await this.audio.stopRecording(this.interview.currentQuestion());
      const userMessage = result.transcript;
      
      if (userMessage && userMessage.trim().length > 3 && !userMessage.includes('(No speech detected)')) {
        const aiResponse = await this.gemini.sendResponse(userMessage);
        
        // Handle API key errors by redirecting to setup
        if (aiResponse.includes('[SYSTEM FAILURE]') && (aiResponse.includes('403') || aiResponse.includes('401') || aiResponse.includes('API key'))) {
          alert('Tu API Key ha fallado (posible restricción de IP o expiración). Por favor, crea una nueva API Key en Google AI Studio exclusiva para este chat.');
          this.interview.setupStep.set(2);
          this.interview.isSetupMode.set(true);
          this.interview.setProcessing(false);
          this.cdr.markForCheck();
          return;
        }

        this.processAIResponse(aiResponse);
      } else if (this.interview.isLiveMode()) {
        // If live mode but no message, just listen again
        this.interview.setProcessing(false);
        this.toggleRecording();
      }
      
      this.interview.setProcessing(false);
      this.cdr.markForCheck();
    } else {
      this.interview.setRecording(true);
      await this.audio.startRecording();
    }
  }

  parseMainText(text: string): string {
    // 1. If [QUOTA EXCEEDED] exists, show that
    if (text.includes('[QUOTA EXCEEDED]')) {
      return '⚠️ LÍMITE DE CUOTA: Google AI Studio te pide un breve descanso. Espera unos 30-60 segundos y vuelve a intentar.';
    }

    // 2. If [NEXT QUESTION] exists, it is the primary conversation
    const nextQ = this.getNextQuestion(text);
    if (nextQ) return nextQ;

    // 2. Fallback: If no [NEXT QUESTION], show the text BEFORE the first tag found
    const firstTagMatch = text.match(/(?:\d+\.\s*)?(?:\*{0,2})\[(COACHING|NATIVE RETRY|NEXT QUESTION|SUGGESTED SCRIPT)\]/i);
    if (firstTagMatch && firstTagMatch.index && firstTagMatch.index > 0) {
      return text.substring(0, firstTagMatch.index).trim();
    }

    // 3. Last resort: Return the full text cleaned of ALL tag blocks
    const cleaned = text
      .replace(/(?:\d+\.\s*)?(?:\*{0,2})\[(COACHING|NATIVE RETRY|NEXT QUESTION|SUGGESTED SCRIPT)\](?:\*{0,2})[\s\S]*?(?=(?:\d+\.\s*)?(?:\*{0,2})\[[A-Z\s]+\](?:\*{0,2})|$)/gi, '')
      .trim();
    
    return cleaned || (text.length > 100 ? text.substring(0, 100) + '...' : text);
  }

  getCoaching(text: string) {
    const match = text.match(/(?:\*{0,2})\[COACHING\](?:\*{0,2})(.*?)(?=(?:\*{0,2})\[[A-Z\s]+\](?:\*{0,2})|$)/s);
    return match ? match[1].trim() : null;
  }

  getNativeRetry(text: string) {
    const match = text.match(/(?:\*{0,2})\[NATIVE RETRY\](?:\*{0,2})(.*?)(?=(?:\*{0,2})\[[A-Z\s]+\](?:\*{0,2})|$)/s);
    return match ? match[1].trim() : null;
  }

  getNextQuestion(text: string) {
    const match = text.match(/(?:\*{0,2})\[NEXT QUESTION\](?:\*{0,2})(.*?)(?=(?:\*{0,2})\[[A-Z\s]+\](?:\*{0,2})|$)/s);
    return match ? match[1].trim() : null;
  }

  getSuggestedScript(text: string) {
    const match = text.match(/(?:\*{0,2})\[SUGGESTED SCRIPT\](?:\*{0,2})(.*?)(?=(?:\*{0,2})\[[A-Z\s]+\](?:\*{0,2})|$)/s);
    return match ? match[1].trim() : null;
  }

  private scrollToBottom() {
    const scroller = document.getElementById('chat-scroller');
    if (scroller) {
      scroller.scrollTop = scroller.scrollHeight;
    }
  }
}
