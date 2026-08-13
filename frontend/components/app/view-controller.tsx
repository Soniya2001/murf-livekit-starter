'use client';

import { useState, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';
import { ShieldAlert, RefreshCw, Loader2, PhoneCall, Lock, Zap, Globe, MicOff, BarChart3 } from 'lucide-react';
import Link from 'next/link';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';
import { Button } from '@/components/ui/button';
import { LanguageCode, LANGUAGES, TRANSLATIONS } from '@/lib/translations';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(AgentSessionView_01);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
    },
    hidden: {
      opacity: 0,
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.5,
    ease: 'linear',
  },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, start, end } = useSessionContext();
  const { resolvedTheme } = useTheme();

  // Language settings state
  const [lang, setLang] = useState<LanguageCode>('en');
  const t = TRANSLATIONS[lang];

  // States: 'ready' | 'connecting' | 'connected' | 'ended' | 'permission-denied'
  const [connectionStage, setConnectionStage] = useState<'ready' | 'connecting' | 'connected' | 'ended' | 'permission-denied'>('ready');
  const [hasConnectedOnce, setHasConnectedOnce] = useState(false);

  // Sync state with LiveKit's isConnected status
  useEffect(() => {
    if (isConnected) {
      setConnectionStage('connected');
      setHasConnectedOnce(true);
    } else if (hasConnectedOnce && !isConnected) {
      setConnectionStage('ended');
    }
  }, [isConnected, hasConnectedOnce]);

  const handleStartCall = async (initialQuestion?: string) => {
    try {
      if (initialQuestion) {
        window.sessionStorage.setItem('finbuddy_initial_question', initialQuestion);
      } else {
        window.sessionStorage.removeItem('finbuddy_initial_question');
      }

      // Step 4: Handle microphone permission check
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());

      // If successful, start the call
      setConnectionStage('connecting');
      await start();
    } catch (err: any) {
      console.error('Microphone permission check failed:', err);
      setConnectionStage('permission-denied');
    }
  };

  const handleRestart = () => {
    setHasConnectedOnce(false);
    setConnectionStage('ready');
  };

  return (
    <div className="flex flex-col min-h-screen w-full bg-background text-foreground">
      {/* Sticky Header with navigation and language controls */}
      <header className="w-full h-16 shrink-0 sticky top-0 bg-[#060b18]/90 backdrop-blur-md text-white flex items-center justify-between px-6 border-b border-white/5 z-50">
        {/* Left Side: logo + branding */}
        <div className="flex items-center gap-3">
          <img
            src="/finbuddy_logo.png"
            alt="FinBuddy Logo"
            className="size-8 object-contain rounded-md"
          />
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold tracking-tight">FinBuddy</h1>
              <span className="px-2 py-0.5 bg-indigo-500/10 border border-indigo-500/30 text-[9px] font-semibold text-indigo-400 rounded-full">
                AI Voice Assistant
              </span>
            </div>
            <p className="text-[10px] text-slate-400">AI Financial Voice Assistant</p>
          </div>
        </div>

        {/* Center: Navigation Links */}
        <nav className="hidden md:flex items-center gap-6 text-xs font-semibold text-slate-300">
          <a href="#how-it-helps" className="hover:text-white hover:underline decoration-indigo-400 underline-offset-4 transition-colors">How FinBuddy Helps</a>
          <a href="#schemes" className="hover:text-white hover:underline decoration-indigo-400 underline-offset-4 transition-colors">Government Schemes</a>
          <a href="#fraud-safety" className="hover:text-white hover:underline decoration-indigo-400 underline-offset-4 transition-colors">Fraud Safety</a>
        </nav>

        {/* Right Side: styled language picker */}
        <div className="flex items-center gap-2">
          <Link
            href="/call-analytics"
            className="flex items-center gap-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white border border-transparent px-3 py-1.5 rounded-lg text-xs font-semibold shadow-md hover:shadow-indigo-500/20 transition-all cursor-pointer mr-1"
          >
            <BarChart3 className="size-3.5" />
            <span className="hidden sm:inline">Call Analytics</span>
            <span className="sm:hidden">Analytics</span>
          </Link>
          <div className="relative flex items-center gap-1.5 bg-[#0e1628] border border-white/10 px-3 py-1.5 rounded-lg text-xs font-semibold text-white cursor-pointer hover:border-slate-500 transition-colors">
            <Globe className="size-3.5 text-slate-300" />
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value as LanguageCode)}
              className="bg-[#0e1628] text-white cursor-pointer outline-none border-none pr-4 text-xs font-semibold appearance-none"
            >
              <option value="en" className="bg-[#0e1628] text-white">English</option>
              <option value="hi" className="bg-[#0e1628] text-white">हिन्दी</option>
              <option value="ta" className="bg-[#0e1628] text-white">தமிழ்</option>
              <option value="te" className="bg-[#0e1628] text-white">తెలుగు</option>
            </select>
            <div className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-white size-0" />
          </div>
        </div>
      </header>

      {/* Main content viewport */}
      <div className="flex-1 w-full flex flex-col justify-start items-center py-6 bg-[#060b18]">
        <AnimatePresence mode="wait">
          {/* Ready State or Permission Denied (shows welcome view behind dialog) */}
          {(connectionStage === 'ready' || connectionStage === 'permission-denied') && (
            <MotionWelcomeView
              key="welcome"
              {...VIEW_MOTION_PROPS}
              startButtonText={t.startBtn}
              onStartCall={handleStartCall}
              lang={lang}
            />
          )}

          {/* Connecting State */}
          {connectionStage === 'connecting' && (
            <motion.div
              key="connecting"
              {...VIEW_MOTION_PROPS}
              className="flex flex-col items-center justify-center text-center p-6 my-auto"
            >
              <div className="relative flex items-center justify-center size-24 mb-6">
                <div className="absolute inset-0 rounded-full border-4 border-indigo-500/20 animate-ping duration-1000" />
                <div className="absolute inset-0 rounded-full border-4 border-t-indigo-500 border-r-indigo-500 border-b-transparent border-l-transparent animate-spin" />
                <Loader2 className="size-10 text-indigo-400 animate-pulse" />
              </div>
              <h2 className="text-2xl font-bold tracking-tight mb-2 text-white">Connecting to FinBuddy...</h2>
              <p className="text-slate-400 max-w-sm text-sm">
                {t.waitMessage}
              </p>
            </motion.div>
          )}

          {/* Connected State (Session View) */}
          {connectionStage === 'connected' && (
            <MotionSessionView
              key="session-view"
              {...VIEW_MOTION_PROPS}
              lang={lang}
              supportsChatInput={appConfig.supportsChatInput}
              supportsVideoInput={appConfig.supportsVideoInput}
              supportsScreenShare={appConfig.supportsScreenShare}
              isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
              audioVisualizerType={appConfig.audioVisualizerType}
              audioVisualizerColor={
                resolvedTheme === 'dark'
                  ? appConfig.audioVisualizerColorDark
                  : appConfig.audioVisualizerColor
              }
              audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
              audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
              audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
              audioVisualizerGridColumnCount={appConfig.audioVisualizerGridColumnCount}
              audioVisualizerRadialBarCount={appConfig.audioVisualizerRadialBarCount}
              audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
              audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
              className="fixed inset-x-0 bottom-0 top-16"
            />
          )}

          {/* Call Ended State */}
          {connectionStage === 'ended' && (
            <motion.div
              key="ended"
              {...VIEW_MOTION_PROPS}
              className="flex flex-col items-center justify-center text-center p-6 my-auto"
            >
              <div className="bg-indigo-500/10 p-4 rounded-full mb-6 border border-indigo-500/20 text-indigo-400">
                <PhoneCall className="size-12" />
              </div>
              <h2 className="text-2xl font-bold tracking-tight mb-2 text-white">Conversation ended</h2>
              <p className="text-slate-400 max-w-sm mb-8 text-sm">
                {t.callEndedDesc}
              </p>
              <div className="flex flex-col sm:flex-row gap-3 w-full max-w-xs justify-center">
                <Button onClick={() => handleStartCall()} size="lg" className="rounded-full bg-indigo-600 hover:bg-indigo-500 text-xs font-bold tracking-wider uppercase text-white cursor-pointer">
                  Talk Again
                </Button>
                <Button onClick={handleRestart} variant="outline" size="lg" className="rounded-full border-white/10 hover:bg-white/5 text-xs font-bold tracking-wider uppercase text-slate-300 hover:text-white cursor-pointer">
                  Return Home
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Polished Microphone Permission Error Modal */}
        {connectionStage === 'permission-denied' && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md bg-[#0c1324] border border-white/10 p-6 rounded-3xl shadow-2xl space-y-6 text-slate-100 text-center"
            >
              <div className="mx-auto w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center text-red-400 border border-red-500/20">
                <MicOff className="size-6" />
              </div>

              <div className="space-y-2">
                <h3 className="text-lg font-bold text-white">Microphone access is needed</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  FinBuddy needs microphone permission to hear your questions.
                </p>
              </div>

              <div className="text-left bg-black/30 border border-white/5 p-4 rounded-xl space-y-3 text-xs">
                <p className="font-semibold text-slate-300">Instructions:</p>
                <ol className="list-decimal pl-4 space-y-2 text-slate-400 font-medium">
                  <li>Click the microphone/lock icon in your browser.</li>
                  <li>Allow microphone access.</li>
                  <li>Try again.</li>
                </ol>
              </div>

              <div className="flex items-center gap-3">
                <Button
                  onClick={() => handleStartCall()}
                  className="flex-1 rounded-full bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold py-5 cursor-pointer text-white"
                >
                  Try Again
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setConnectionStage('ready')}
                  className="flex-1 rounded-full border-white/10 hover:bg-white/5 text-xs font-semibold py-5 cursor-pointer text-slate-300 hover:text-white"
                >
                  Close
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </div>
    </div>
  );
}
