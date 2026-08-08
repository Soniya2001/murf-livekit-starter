'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { ShieldCheck, PiggyBank, GraduationCap, AlertTriangle, ExternalLink } from 'lucide-react';
import { LanguageCode, TRANSLATIONS } from '@/lib/translations';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  lang: LanguageCode;
}

export const WelcomeView = React.forwardRef<HTMLDivElement, WelcomeViewProps>(
  ({ startButtonText, onStartCall, lang }, ref) => {
    const t = TRANSLATIONS[lang];

    return (
      <div ref={ref} className="w-full max-w-2xl px-6 py-6 mx-auto flex flex-col items-center">
        {/* Header Section */}
        <div className="text-center mb-6 flex flex-col items-center">
          <h1 className="text-3xl font-extrabold tracking-tight bg-linear-to-r from-primary via-indigo-600 to-indigo-500 bg-clip-text text-transparent">
            {t.title}
          </h1>
          <p className="text-muted-foreground mt-2 text-sm max-w-md mx-auto">
            {t.subtitle}
          </p>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 w-full mb-6">
          {/* Card 1 */}
          <div className="flex flex-col items-center md:items-start p-3.5 rounded-xl border border-border bg-card text-center md:text-left transition-all hover:shadow-sm">
            <div className="p-2 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 rounded-lg mb-2">
              <GraduationCap className="size-4.5" />
            </div>
            <h3 className="font-semibold text-foreground text-xs">{t.flTitle}</h3>
            <p className="text-[11px] leading-relaxed text-muted-foreground mt-1">
              {t.flDesc}
            </p>
          </div>

          {/* Card 2 */}
          <div className="flex flex-col items-center md:items-start p-3.5 rounded-xl border border-border bg-card text-center md:text-left transition-all hover:shadow-sm">
            <div className="p-2 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 rounded-lg mb-2">
              <ShieldCheck className="size-4.5" />
            </div>
            <h3 className="font-semibold text-foreground text-xs">{t.gsTitle}</h3>
            <p className="text-[11px] leading-relaxed text-muted-foreground mt-1">
              {t.gsDesc}
            </p>
          </div>

          {/* Card 3 */}
          <div className="flex flex-col items-center md:items-start p-3.5 rounded-xl border border-border bg-card text-center md:text-left transition-all hover:shadow-sm">
            <div className="p-2 bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 rounded-lg mb-2">
              <AlertTriangle className="size-4.5" />
            </div>
            <h3 className="font-semibold text-foreground text-xs">{t.saTitle}</h3>
            <p className="text-[11px] leading-relaxed text-muted-foreground mt-1">
              {t.saDesc}
            </p>
          </div>
        </div>

        {/* Dynamic Government Schemes & Hyperlinks */}
        <div className="w-full border border-border/80 rounded-xl p-4 bg-muted/20 mb-6 text-left">
          <h2 className="text-sm font-bold text-foreground mb-1 flex items-center gap-1.5">
            <ExternalLink className="size-4 text-primary" />
            {t.schemesTitle}
          </h2>
          <p className="text-xs text-muted-foreground mb-3">{t.schemesSubtitle}</p>
          <div className="space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 rounded-lg border border-border bg-card">
              <div>
                <h4 className="text-xs font-bold text-foreground">{t.pmjdyTitle}</h4>
                <p className="text-[10px] text-muted-foreground mt-0.5">{t.pmjdyDesc}</p>
              </div>
              <a
                href="https://www.pmjdy.gov.in/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[10px] font-bold text-primary hover:underline shrink-0 flex items-center gap-1"
              >
                {t.learnMore}
              </a>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 rounded-lg border border-border bg-card">
              <div>
                <h4 className="text-xs font-bold text-foreground">{t.apyTitle}</h4>
                <p className="text-[10px] text-muted-foreground mt-0.5">{t.apyDesc}</p>
              </div>
              <a
                href="https://www.npscra.nsdl.co.in/scheme-atal-pension-yojana.php"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[10px] font-bold text-primary hover:underline shrink-0 flex items-center gap-1"
              >
                {t.learnMore}
              </a>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 rounded-lg border border-border bg-card">
              <div>
                <h4 className="text-xs font-bold text-foreground">{t.pmsbyTitle}</h4>
                <p className="text-[10px] text-muted-foreground mt-0.5">{t.pmsbyDesc}</p>
              </div>
              <a
                href="https://www.jansuraksha.gov.in/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[10px] font-bold text-primary hover:underline shrink-0 flex items-center gap-1"
              >
                {t.learnMore}
              </a>
            </div>
          </div>
        </div>

        {/* Security Warning Notice */}
        <div className="w-full bg-amber-50 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-900/40 rounded-xl p-3.5 mb-6 flex gap-3 text-left">
          <div className="text-amber-600 dark:text-amber-400 shrink-0">
            <ShieldCheck className="size-4.5" />
          </div>
          <div>
            <h4 className="text-xs font-semibold text-amber-800 dark:text-amber-300">{t.secNoticeTitle}</h4>
            <p className="text-[11px] text-amber-700/90 dark:text-amber-400/90 mt-0.5 leading-relaxed">
              {t.secNoticeBody}
            </p>
          </div>
        </div>

        {/* Call to Action Button */}
        <Button
          size="lg"
          onClick={onStartCall}
          className="w-full md:w-64 rounded-full font-mono text-xs font-bold tracking-wider uppercase bg-primary hover:bg-primary/95 text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:scale-[1.02]"
        >
          {t.startBtn}
        </Button>

        {/* Footer info link */}
        <div className="mt-6 text-center">
          <p className="text-muted-foreground text-[10px]">
            {t.footerText}
          </p>
        </div>
      </div>
    );
  }
);

WelcomeView.displayName = 'WelcomeView';
