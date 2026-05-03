import { motion } from 'framer-motion';
import { FileSearch, ShieldCheck, Scale, Check, Lock, Loader2, XCircle } from 'lucide-react';

const stepsConfig = [
  {
    id: 'extraction',
    name: 'Agent 1 — Document Extraction',
    description: 'OCR scanning, text extraction & structured data parsing',
    icon: FileSearch,
  },
  {
    id: 'verification',
    name: 'Agent 2 — Credential Verification',
    description: 'Cross-referencing registries, scoring & anomaly detection',
    icon: ShieldCheck,
  },
  {
    id: 'report',
    name: 'Agent 3 — Decision & Report',
    description: 'AI-powered decision making with Groq LLM analysis',
    icon: Scale,
  },
];

export default function PipelineStatus({ currentStepIndex, isError, isFinished }) {
  const getStepStatus = (index) => {
    if (index < currentStepIndex || isFinished) return 'done';
    if (index === currentStepIndex && isError) return 'error';
    if (index === currentStepIndex) return 'processing';
    return 'pending';
  };

  return (
    <div className="glass-card p-6 md:p-8 w-full max-w-xl">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">AI Verification Pipeline</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">LangGraph multi-agent system analyzing credentials in real-time.</p>
      </div>

      <div className="space-y-4">
        {stepsConfig.map((step, index) => {
          const status = getStepStatus(index);
          const Icon = step.icon;

          let containerClass = 'border-slate-200 dark:border-white/7 bg-white/40 dark:bg-white/3';
          let iconContainerClass = 'bg-slate-100 dark:bg-white/6 text-slate-400 dark:text-slate-500';
          let StatusIcon = Lock;
          let statusIconClass = 'text-slate-300 dark:text-slate-600';
          let nameClass = 'text-slate-900 dark:text-slate-200';
          let descClass = 'text-slate-500 dark:text-slate-500';

          if (status === 'done') {
            containerClass = 'border-green-200 dark:border-green-800/40 bg-green-50/30 dark:bg-green-500/[0.07]';
            iconContainerClass = 'bg-green-100 dark:bg-green-500/20 text-green-600 dark:text-green-400';
            StatusIcon = Check;
            statusIconClass = 'text-green-500 dark:text-green-400';
          } else if (status === 'processing') {
            containerClass = 'border-brand-300 dark:border-brand-500/40 bg-brand-50/50 dark:bg-brand-500/[0.08] shadow-sm ring-1 ring-brand-500/10 dark:ring-brand-500/20';
            iconContainerClass = 'bg-brand-100 dark:bg-brand-500/20 text-brand-600 dark:text-brand-400';
            StatusIcon = Loader2;
            statusIconClass = 'text-brand-500 dark:text-brand-400 animate-spin';
            nameClass = 'text-brand-700 dark:text-brand-300';
          } else if (status === 'error') {
            containerClass = 'border-red-300 dark:border-red-800/40 bg-red-50/50 dark:bg-red-500/[0.07]';
            iconContainerClass = 'bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400';
            StatusIcon = XCircle;
            statusIconClass = 'text-red-500 dark:text-red-400';
          }

          return (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`relative flex items-center p-4 rounded-xl border transition-all duration-300 ${containerClass}`}
            >
              <div className={`p-2.5 rounded-lg mr-4 shrink-0 transition-colors ${iconContainerClass}`}>
                <Icon className="w-5 h-5" />
              </div>

              <div className="flex-1 min-w-0">
                <h4 className={`text-sm font-semibold truncate ${nameClass}`}>{step.name}</h4>
                <p className={`text-xs truncate ${descClass}`}>{step.description}</p>
              </div>

              <div className="ml-4 shrink-0">
                <StatusIcon className={`w-5 h-5 ${statusIconClass}`} />
              </div>

              {index < stepsConfig.length - 1 && (
                <div className={`absolute left-9 top-13 w-px h-6 -ml-px ${status === 'done' ? 'bg-green-300 dark:bg-green-700' : 'bg-slate-200 dark:bg-white/10'}`} />
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
