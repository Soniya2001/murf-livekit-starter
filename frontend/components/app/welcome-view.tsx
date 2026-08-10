'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { 
  ShieldCheck, 
  GraduationCap, 
  AlertTriangle, 
  ExternalLink, 
  Mic, 
  ArrowRight, 
  Shield, 
  MessageSquare, 
  Volume2, 
  Info,
  Sparkles
} from 'lucide-react';
import { LanguageCode, TRANSLATIONS } from '@/lib/translations';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: (initialQuestion?: string) => void;
  lang: LanguageCode;
}

export const WelcomeView = React.forwardRef<HTMLDivElement, WelcomeViewProps>(
  ({ startButtonText, onStartCall, lang }, ref) => {
    const t = TRANSLATIONS[lang];

    const examplePrompts = [
      "Am I eligible for PMJDY?",
      "Explain APY simply",
      "How do I identify a UPI scam?",
      "How should I start saving?"
    ];

    return (
      <div ref={ref} className="w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-10 mx-auto flex flex-col space-y-24 text-slate-100 bg-[#060b18]">
        
        {/* HERO SECTION */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center pt-6 lg:pt-12">
          {/* Left Column: Headings & CTAs */}
          <div className="lg:col-span-7 space-y-8 text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-indigo-500/10 border border-indigo-500/20 text-xs font-medium text-indigo-300 rounded-full">
              <Sparkles className="size-3.5" />
              <span>AI-powered Financial Guidance</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight">
              Financial Guidance.<br />
              <span className="bg-gradient-to-r from-blue-400 via-indigo-400 to-violet-400 bg-clip-text text-transparent">
                Just Ask.
              </span>
            </h1>

            <p className="text-slate-300 text-base sm:text-lg max-w-2xl leading-relaxed">
              Talk to FinBuddy about government schemes, banking, savings, digital payments, and staying safe from financial fraud.
            </p>

            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 pt-2">
              <Button
                size="lg"
                onClick={() => onStartCall()}
                className="rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-sm tracking-wide shadow-lg shadow-indigo-500/25 transition-all hover:scale-[1.03] py-6 px-8 flex items-center justify-center gap-2.5 cursor-pointer"
              >
                <Mic className="size-5 animate-pulse" />
                <span>Talk to FinBuddy</span>
              </Button>

              <a
                href="#how-it-helps"
                className="inline-flex items-center justify-center px-6 py-3.5 text-sm font-semibold text-slate-300 hover:text-white border border-white/10 hover:border-white/20 rounded-full bg-white/5 backdrop-blur-md transition-all"
              >
                Explore what FinBuddy can help with
              </a>
            </div>

            <div className="space-y-3 pt-2">
              <p className="text-xs text-slate-400 font-medium">
                Speak naturally in English, Hindi, Tamil or Telugu
              </p>
              <div className="flex flex-wrap gap-2">
                {['English', 'हिन्दी', 'தமிழ்', 'తెలుగు'].map((l) => (
                  <span key={l} className="px-3 py-1 bg-white/5 border border-white/5 rounded-full text-xs text-slate-300 font-medium">
                    {l}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: AI Voice Visualization Panel */}
          <div className="lg:col-span-5 flex flex-col items-center justify-center">
            <div className="relative w-full max-w-sm aspect-square bg-[#0c1324]/40 border border-white/5 rounded-3xl p-6 flex flex-col items-center justify-between shadow-2xl backdrop-blur-md">
              <div className="text-center">
                <span className="text-[10px] uppercase font-bold tracking-widest text-indigo-400 font-mono">Ready to Help</span>
              </div>

              {/* Circular Avatar + Pulse Waveform Container */}
              <div className="relative flex items-center justify-center w-48 h-48 my-4">
                {/* Glowing Rings */}
                <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-blue-500/20 via-indigo-500/20 to-violet-500/20 animate-[spin_12s_linear_infinite]" />
                <div className="absolute inset-2 rounded-full border border-indigo-500/10 bg-indigo-950/20 backdrop-blur-sm" />
                
                {/* Waveform bars (CSS animated) */}
                <div className="absolute inset-0 flex items-center justify-center gap-1.5 pointer-events-none opacity-60">
                  <span className="w-1 bg-blue-400 rounded-full animate-[bounce_1.2s_infinite_100ms] h-12" />
                  <span className="w-1 bg-indigo-400 rounded-full animate-[bounce_1.2s_infinite_300ms] h-16" />
                  <span className="w-1 bg-violet-400 rounded-full animate-[bounce_1.2s_infinite_200ms] h-20" />
                  <span className="w-1 bg-indigo-400 rounded-full animate-[bounce_1.2s_infinite_400ms] h-16" />
                  <span className="w-1 bg-blue-400 rounded-full animate-[bounce_1.2s_infinite_150ms] h-12" />
                </div>

                {/* Main Avatar Circle */}
                <button 
                  onClick={() => onStartCall()}
                  className="relative w-28 h-28 rounded-full overflow-hidden border-2 border-indigo-500/30 shadow-inner group hover:scale-105 transition-transform duration-300 cursor-pointer"
                >
                  <img
                    src="/finbuddy_avatar.png"
                    alt="FinBuddy Avatar"
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                    <Mic className="size-6 text-white" />
                  </div>
                </button>
              </div>

              {/* Status and instruction */}
              <div className="text-center space-y-1">
                <p className="text-xs font-bold text-slate-200 flex items-center justify-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                  FinBuddy is ready
                </p>
                <p className="text-[11px] text-slate-400">
                  Tap the microphone and ask a financial question.
                </p>
              </div>
            </div>

            {/* Example Prompt Chips */}
            <div className="w-full max-w-sm mt-6 flex flex-col gap-2">
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider text-center font-mono">Try asking:</span>
              <div className="grid grid-cols-2 gap-2">
                {examplePrompts.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => onStartCall(prompt)}
                    className="p-2.5 text-left text-xs bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/10 rounded-xl text-slate-300 hover:text-white transition-all font-medium truncate cursor-pointer"
                  >
                    "{prompt}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* THREE CORE CAPABILITIES */}
        <section id="how-it-helps" className="space-y-12 pt-6">
          <div className="text-center space-y-3">
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">How can FinBuddy help you?</h2>
            <p className="text-slate-400 text-sm max-w-xl mx-auto">Simple financial guidance without complicated jargon.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Capability 1 */}
            <div className="group relative flex flex-col justify-between p-6 rounded-2xl border border-white/5 bg-[#0c1324]/30 hover:bg-[#0c1324]/50 transition-all hover:shadow-lg hover:shadow-indigo-500/5">
              <div className="space-y-4">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
                  <GraduationCap className="size-5" />
                </div>
                <h3 className="text-base font-bold text-slate-200">Financial Literacy</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Understand savings, budgeting, banking, loans and digital payments in simple language.
                </p>
                <div className="bg-white/5 rounded-lg p-2.5 border border-white/5 text-[11px] text-slate-300">
                  <span className="font-semibold text-indigo-300 block mb-0.5">Example:</span>
                  "How does compound interest work?"
                </div>
              </div>
              <button 
                onClick={() => onStartCall("How does compound interest work?")}
                className="mt-6 flex items-center gap-1.5 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors cursor-pointer self-start"
              >
                <span>Ask FinBuddy</span>
                <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-1" />
              </button>
            </div>

            {/* Capability 2 */}
            <div className="group relative flex flex-col justify-between p-6 rounded-2xl border border-white/5 bg-[#0c1324]/30 hover:bg-[#0c1324]/50 transition-all hover:shadow-lg hover:shadow-indigo-500/5">
              <div className="space-y-4">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
                  <ShieldCheck className="size-5" />
                </div>
                <h3 className="text-base font-bold text-slate-200">Government Schemes</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Understand eligibility, benefits and official information about Indian financial schemes.
                </p>
                <div className="bg-white/5 rounded-lg p-2.5 border border-white/5 text-[11px] text-slate-300">
                  <span className="font-semibold text-indigo-300 block mb-0.5">Example Schemes:</span>
                  PMJDY • APY • PMJJBY • PMSBY
                </div>
              </div>
              <a 
                href="#schemes"
                className="mt-6 flex items-center gap-1.5 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors self-start"
              >
                <span>Explore Schemes</span>
                <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-1" />
              </a>
            </div>

            {/* Capability 3 */}
            <div className="group relative flex flex-col justify-between p-6 rounded-2xl border border-white/5 bg-[#0c1324]/30 hover:bg-[#0c1324]/50 transition-all hover:shadow-lg hover:shadow-indigo-500/5">
              <div className="space-y-4">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
                  <Shield className="size-5" />
                </div>
                <h3 className="text-base font-bold text-slate-200">Fraud & Scam Awareness</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Learn how to recognize suspicious calls, UPI scams, phishing links and other financial fraud.
                </p>
                <div className="bg-white/5 rounded-lg p-2.5 border border-white/5 text-[11px] text-slate-300">
                  <span className="font-semibold text-indigo-300 block mb-0.5">Example:</span>
                  "Someone is asking for my OTP. What should I do?"
                </div>
              </div>
              <button 
                onClick={() => onStartCall("Someone is asking for my OTP. What should I do?")}
                className="mt-6 flex items-center gap-1.5 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors cursor-pointer self-start"
              >
                <span>Check with FinBuddy</span>
                <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-1" />
              </button>
            </div>
          </div>
        </section>

        {/* POPULAR GOVERNMENT SCHEMES */}
        <section id="schemes" className="space-y-12 pt-6">
          <div className="text-center space-y-3">
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">Government Schemes Made Simple</h2>
            <p className="text-slate-400 text-sm max-w-xl mx-auto">Ask FinBuddy to explain schemes in everyday language.</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Scheme 1 */}
            <div className="p-6 rounded-2xl border border-white/5 bg-[#0c1324]/30 flex flex-col justify-between space-y-4 hover:border-indigo-500/20 transition-all">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider font-mono">Financial Inclusion</span>
                  <span className="text-[10px] px-2 py-0.5 bg-white/5 border border-white/5 text-slate-400 rounded-full font-semibold font-mono">PMJDY</span>
                </div>
                <h3 className="text-base font-bold text-slate-200">Pradhan Mantri Jan Dhan Yojana</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  National Mission for Financial Inclusion to ensure access to financial services, savings accounts, remittance, and pension.
                </p>
              </div>
              <div className="flex items-center gap-3 pt-2">
                <Button 
                  onClick={() => onStartCall("Explain Pradhan Mantri Jan Dhan Yojana eligibility and benefits")} 
                  size="sm" 
                  className="rounded-full bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white px-4 py-2 cursor-pointer"
                >
                  Ask FinBuddy
                </Button>
                <a
                  href="https://www.pmjdy.gov.in/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-white transition-colors"
                >
                  <span>Official Portal</span>
                  <ExternalLink className="size-3" />
                </a>
              </div>
            </div>

            {/* Scheme 2 */}
            <div className="p-6 rounded-2xl border border-white/5 bg-[#0c1324]/30 flex flex-col justify-between space-y-4 hover:border-indigo-500/20 transition-all">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider font-mono">Social Security & Pension</span>
                  <span className="text-[10px] px-2 py-0.5 bg-white/5 border border-white/5 text-slate-400 rounded-full font-semibold font-mono">APY</span>
                </div>
                <h3 className="text-base font-bold text-slate-200">Atal Pension Yojana</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Guaranteed monthly pension scheme targeting workers in the unorganized sector, ensuring safe post-retirement income.
                </p>
              </div>
              <div className="flex items-center gap-3 pt-2">
                <Button 
                  onClick={() => onStartCall("Explain Atal Pension Yojana eligibility and benefits")} 
                  size="sm" 
                  className="rounded-full bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white px-4 py-2 cursor-pointer"
                >
                  Ask FinBuddy
                </Button>
                <a
                  href="https://www.npscra.nsdl.co.in/scheme-atal-pension-yojana.php"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-white transition-colors"
                >
                  <span>Official Portal</span>
                  <ExternalLink className="size-3" />
                </a>
              </div>
            </div>

            {/* Scheme 3 */}
            <div className="p-6 rounded-2xl border border-white/5 bg-[#0c1324]/30 flex flex-col justify-between space-y-4 hover:border-indigo-500/20 transition-all">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider font-mono">Life Insurance</span>
                  <span className="text-[10px] px-2 py-0.5 bg-white/5 border border-white/5 text-slate-400 rounded-full font-semibold font-mono">PMJJBY</span>
                </div>
                <h3 className="text-base font-bold text-slate-200">Pradhan Mantri Jeevan Jyoti Bima Yojana</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  One-year life insurance scheme renewable from year to year, offering high-value life insurance cover for death due to any cause.
                </p>
              </div>
              <div className="flex items-center gap-3 pt-2">
                <Button 
                  onClick={() => onStartCall("Explain PMJJBY scheme details")} 
                  size="sm" 
                  className="rounded-full bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white px-4 py-2 cursor-pointer"
                >
                  Ask FinBuddy
                </Button>
                <a
                  href="https://www.jansuraksha.gov.in/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-white transition-colors"
                >
                  <span>Official Portal</span>
                  <ExternalLink className="size-3" />
                </a>
              </div>
            </div>

            {/* Scheme 4 */}
            <div className="p-6 rounded-2xl border border-white/5 bg-[#0c1324]/30 flex flex-col justify-between space-y-4 hover:border-indigo-500/20 transition-all">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider font-mono">Accident Insurance</span>
                  <span className="text-[10px] px-2 py-0.5 bg-white/5 border border-white/5 text-slate-400 rounded-full font-semibold font-mono">PMSBY</span>
                </div>
                <h3 className="text-base font-bold text-slate-200">Pradhan Mantri Suraksha Bima Yojana</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Accident insurance scheme offering coverage for accidental death and full or partial disability in a very affordable manner.
                </p>
              </div>
              <div className="flex items-center gap-3 pt-2">
                <Button 
                  onClick={() => onStartCall("Explain PMSBY scheme details")} 
                  size="sm" 
                  className="rounded-full bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white px-4 py-2 cursor-pointer"
                >
                  Ask FinBuddy
                </Button>
                <a
                  href="https://www.jansuraksha.gov.in/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-white transition-colors"
                >
                  <span>Official Portal</span>
                  <ExternalLink className="size-3" />
                </a>
              </div>
            </div>
          </div>

          {/* Scheme Trust Disclaimer */}
          <div className="p-4 rounded-xl border border-white/5 bg-white/5 flex gap-3 text-left items-start">
            <Info className="size-4.5 text-indigo-400 shrink-0 mt-0.5" />
            <p className="text-[11px] text-slate-400 leading-relaxed">
              <span className="font-semibold text-slate-300">Eligibility Disclaimer:</span> FinBuddy can explain eligibility requirements, but final eligibility is determined by the relevant authority. Never assume guaranteed eligibility.
            </p>
          </div>
        </section>

        {/* FRAUD PROTECTION SECTION */}
        <section id="fraud-safety" className="p-8 sm:p-12 rounded-3xl border border-red-500/10 bg-red-950/5 relative overflow-hidden text-left space-y-8">
          <div className="absolute top-0 right-0 -translate-y-12 translate-x-12 w-64 h-64 bg-red-500/5 rounded-full blur-3xl pointer-events-none" />
          
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-red-500/10 border border-red-500/20 text-xs font-medium text-red-300 rounded-full">
                <Shield className="size-3.5 text-red-400" />
                <span>Your Security Comes First</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">FinBuddy will NEVER ask for:</h2>
            </div>
            
            <Button
              onClick={() => onStartCall("How do I stay safe from financial fraud?")}
              className="rounded-full bg-red-900/30 hover:bg-red-950/40 text-red-300 hover:text-red-200 border border-red-900/50 text-xs font-bold cursor-pointer"
            >
              Ask About a Suspicious Message
            </Button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {['OTP', 'PIN', 'Password', 'Full bank credentials'].map((item) => (
              <div key={item} className="p-4 rounded-xl border border-white/5 bg-black/20 flex flex-col items-center justify-center text-center">
                <span className="text-xl font-black text-red-500/80 mb-1">❌</span>
                <span className="text-sm font-semibold text-slate-200">{item}</span>
              </div>
            ))}
          </div>

          <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/5 text-xs text-red-300 font-semibold leading-relaxed">
            ⚠️ Warning: Never share an OTP or PIN — even with someone claiming to be from your bank.
          </div>
        </section>

        {/* MULTILINGUAL SECTION */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center text-left">
          <div className="lg:col-span-6 space-y-6">
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">Financial guidance in your language.</h2>
            <p className="text-slate-300 text-sm leading-relaxed">
              Speak naturally. FinBuddy can understand and respond across multiple Indian languages.
            </p>
            
            <div className="space-y-4 bg-[#0c1324]/30 border border-white/5 rounded-2xl p-6">
              <span className="text-[10px] uppercase font-bold tracking-widest text-indigo-400 font-mono">Code-mixed conversations supported</span>
              <div className="flex gap-3 items-start">
                <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  <MessageSquare className="size-4.5" />
                </div>
                <div>
                  <p className="text-xs italic text-slate-300 font-mono">"PMJDY scheme-ku eligibility enna?"</p>
                  <p className="text-[11px] text-slate-400 mt-1">→ FinBuddy should understand the user's natural language style.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-6 flex flex-col justify-center space-y-4">
            <div className="grid grid-cols-2 gap-4">
              {[
                { lang: 'English', bubble: 'Can I apply for APY online?' },
                { lang: 'हिन्दी', bubble: 'क्या मैं ऑनलाइन जन धन खाता खोल सकता हूँ?' },
                { lang: 'தமிழ்', bubble: 'எனக்கு APY திட்டம் பற்றி சொல்லுங்கள்.' },
                { lang: 'తెలుగు', bubble: 'UPI మోసాల గురించి చెప్పండి.' }
              ].map((item) => (
                <div key={item.lang} className="p-4 rounded-2xl border border-white/5 bg-[#0c1324]/30 space-y-2 flex flex-col justify-between">
                  <span className="text-[10px] font-bold text-slate-400">{item.lang}</span>
                  <p className="text-xs text-slate-300 italic">"{item.bubble}"</p>
                  <div className="flex items-center gap-1 text-[9px] text-indigo-400 font-semibold self-end">
                    <Volume2 className="size-3" />
                    <span>Speak</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* TRUST DISCLAIMER */}
        <section className="p-6 rounded-2xl border border-white/5 bg-[#0c1324]/20 text-center max-w-3xl mx-auto space-y-3">
          <div className="flex items-center justify-center text-slate-400 gap-1.5">
            <ShieldCheck className="size-5 text-indigo-400" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">Trust and Safety</span>
          </div>
          <p className="text-slate-400 text-xs leading-relaxed">
            FinBuddy provides educational financial guidance and does not represent a bank or government authority.
          </p>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            Scheme eligibility, benefits and rules may change. Verify important information through official government or banking sources. Never share OTPs, PINs, passwords or sensitive banking credentials.
          </p>
        </section>

        {/* FINAL CTA SECTION */}
        <section className="p-12 sm:p-16 rounded-3xl bg-gradient-to-r from-blue-900/30 via-indigo-900/30 to-violet-900/30 border border-indigo-500/10 text-center space-y-8">
          <div className="space-y-3">
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
              Financial questions shouldn't feel complicated.
            </h2>
            <p className="text-slate-300 text-sm max-w-xl mx-auto">
              Ask FinBuddy and understand them one conversation at a time.
            </p>
          </div>

          <Button
            size="lg"
            onClick={() => onStartCall()}
            className="rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-sm tracking-wide shadow-lg shadow-indigo-500/25 py-6 px-10 flex items-center justify-center gap-2 mx-auto cursor-pointer"
          >
            <Mic className="size-5 animate-pulse" />
            <span>Talk to FinBuddy</span>
          </Button>

          <div className="flex items-center justify-center gap-3 text-xs text-slate-400 font-semibold font-mono">
            <span>English</span>
            <span>•</span>
            <span>हिन्दी</span>
            <span>•</span>
            <span>தமிழ்</span>
            <span>•</span>
            <span>తెలుగు</span>
          </div>
        </section>

        {/* FOOTER */}
        <footer className="pt-12 border-t border-white/5 text-slate-400 text-left space-y-8">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <img src="/finbuddy_logo.png" alt="FinBuddy Logo" className="size-5 object-contain" />
                FinBuddy
              </h4>
              <p className="text-xs text-slate-500">AI Financial Voice Assistant</p>
            </div>
            
            <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs font-semibold">
              <a href="#" className="hover:text-white transition-colors">About</a>
              <a href="#" className="hover:text-white transition-colors">Safety</a>
              <a href="#" className="hover:text-white transition-colors">Government Resources</a>
              <a href="#" className="hover:text-white transition-colors">Privacy</a>
            </div>
          </div>

          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 text-[10px] text-slate-500">
            <p>Built for accessible financial literacy.</p>
            <p>© {new Date().getFullYear()} FinBuddy. All rights reserved.</p>
          </div>
        </footer>

      </div>
    );
  }
);

WelcomeView.displayName = 'WelcomeView';
