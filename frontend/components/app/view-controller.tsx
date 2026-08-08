'use client';

import { useState, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';
import { ShieldAlert, RefreshCw, Loader2, PhoneCall, Lock, Zap, Globe } from 'lucide-react';
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

  const handleStartCall = async () => {
    try {
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
      {/* Dynamic Styled Header exactly like the screenshot */}
      <header className="w-full h-16 shrink-0 bg-[#0c2445] text-white flex items-center justify-between px-6 border-b border-[#13325c] z-50">
        {/* Left Side: logo + branding */}
        <div className="flex items-center gap-3">
          <img
            src="/finbuddy_logo.png"
            alt="FinBuddy Logo"
            className="size-8 object-contain rounded-md"
          />
          <div>
            <h1 className="text-sm font-bold tracking-tight">FinBuddy</h1>
            <p className="text-[10px] text-slate-300">AI Financial Voice Assistant</p>
          </div>
        </div>

        {/* Center: badging */}
        <div className="hidden sm:flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1 bg-[#102e54] rounded-full border border-slate-700/40 text-[10px] font-semibold text-slate-200">
            <Lock className="size-3 text-emerald-400" />
            <span>{t.secureConn}</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1 bg-[#102e54] rounded-full border border-slate-700/40 text-[10px] font-semibold text-slate-200">
            <Zap className="size-3 text-sky-400" />
            <span>{t.lowLatency}</span>
          </div>
        </div>

        {/* Right Side: styled language picker */}
        <div className="flex items-center gap-2">
          <div className="relative flex items-center gap-1.5 bg-[#102e54] border border-slate-700/60 px-3 py-1.5 rounded-lg text-xs font-semibold text-white cursor-pointer hover:border-slate-500 transition-colors">
            <Globe className="size-3.5 text-slate-300" />
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value as LanguageCode)}
              className="bg-transparent text-white cursor-pointer outline-none border-none pr-4 text-xs font-semibold appearance-none"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code} className="bg-[#0c2445] text-white">
                  {l.label}
                </option>
              ))}
            </select>
            <div className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-white size-0" />
          </div>
        </div>
      </header>

      {/* Main content viewport */}
      <div className="flex-1 w-full flex flex-col justify-start items-center py-6">
        <AnimatePresence mode="wait">
          {/* Ready State */}
          {connectionStage === 'ready' && (
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
              className="flex flex-col items-center justify-center text-center p-6"
            >
              <div className="relative flex items-center justify-center size-24 mb-6">
                <div className="absolute inset-0 rounded-full border-4 border-primary/20 animate-ping duration-1000" />
                <div className="absolute inset-0 rounded-full border-4 border-t-primary border-r-primary border-b-transparent border-l-transparent animate-spin" />
                <Loader2 className="size-10 text-primary animate-pulse" />
              </div>
              <h2 className="text-2xl font-bold tracking-tight mb-2">{t.connecting}</h2>
              <p className="text-muted-foreground max-w-sm">
                {t.waitMessage}
              </p>
            </motion.div>
          )}

          {/* Permission Denied State */}
          {connectionStage === 'permission-denied' && (
            <motion.div
              key="permission-denied"
              {...VIEW_MOTION_PROPS}
              className="flex flex-col items-center justify-center text-center p-8 max-w-md mx-auto"
            >
              <div className="bg-destructive/10 p-4 rounded-full mb-6">
                <ShieldAlert className="size-12 text-destructive" />
              </div>
              <h2 className="text-2xl font-bold tracking-tight text-destructive mb-3">{t.micBlocked}</h2>
              <div className="text-left bg-muted/50 p-4 rounded-lg border border-border/60 mb-6 text-sm space-y-3">
                <p className="font-semibold text-foreground">{t.micBlockedDesc}</p>
                <ol className="list-decimal pl-4 space-y-2 text-muted-foreground">
                  <li>{t.micStep1}</li>
                  <li>{t.micStep2}</li>
                  <li>{t.micStep3}</li>
                </ol>
              </div>
              <Button onClick={handleStartCall} size="lg" className="w-full gap-2 rounded-full">
                <RefreshCw className="size-4" />
                {t.tryAgain}
              </Button>
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
              className="flex flex-col items-center justify-center text-center p-6"
            >
              <div className="bg-primary/10 p-4 rounded-full mb-6">
                <PhoneCall className="size-12 text-primary" />
              </div>
              <h2 className="text-2xl font-bold tracking-tight mb-2">{t.callEnded}</h2>
              <p className="text-muted-foreground max-w-sm mb-8">
                {t.callEndedDesc}
              </p>
              <Button onClick={handleRestart} size="lg" className="w-64 gap-2 rounded-full font-mono text-xs font-bold tracking-wider uppercase">
                {t.startAgain}
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
