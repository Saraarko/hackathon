import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldCheck, ShieldX, ShieldAlert, RefreshCw, AlertTriangle,
  ArrowRight, FileSearch, Scale, ChevronDown, ChevronUp,
  User, MapPin, Stethoscope, Hash, FileText, Sparkles
} from 'lucide-react';

const getDecisionConfig = (decision) => {
  switch (decision) {
    case 'APPROVED':
      return { gradient: 'from-emerald-500 to-green-600', bg: 'bg-emerald-50 dark:bg-emerald-500/10', text: 'text-emerald-700 dark:text-emerald-400', border: 'border-emerald-200 dark:border-emerald-500/30', icon: ShieldCheck, label: 'APPROVED' };
    case 'REJECTED':
      return { gradient: 'from-red-500 to-rose-600', bg: 'bg-red-50 dark:bg-red-500/10', text: 'text-red-700 dark:text-red-400', border: 'border-red-200 dark:border-red-500/30', icon: ShieldX, label: 'REJECTED' };
    default:
      return { gradient: 'from-amber-500 to-orange-500', bg: 'bg-amber-50 dark:bg-amber-500/10', text: 'text-amber-700 dark:text-amber-400', border: 'border-amber-200 dark:border-amber-500/30', icon: ShieldAlert, label: 'PENDING REVIEW' };
  }
};

const getPriorityBadge = (priority) => {
  switch (priority) {
    case 'HIGH': return 'bg-red-100 dark:bg-red-500/15 text-red-700 dark:text-red-400 border-red-200 dark:border-red-500/30';
    case 'MEDIUM': return 'bg-amber-100 dark:bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-500/30';
    case 'LOW': return 'bg-green-100 dark:bg-green-500/15 text-green-700 dark:text-green-400 border-green-200 dark:border-green-500/30';
    default: return 'bg-slate-100 dark:bg-white/6 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-white/10';
  }
};

function QualityBar({ value, max = 1, label }) {
  const pct = Math.min((value / max) * 100, 100);
  const barColor = pct > 70 ? 'bg-emerald-500' : pct > 40 ? 'bg-amber-500' : 'bg-red-500';

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-600 dark:text-slate-400 font-medium">{label}</span>
        <span className="text-slate-900 dark:text-white font-bold">
          {typeof value === 'number' ? (max === 1 ? `${(value * 100).toFixed(0)}%` : `${value.toFixed(1)}/${max}`) : value}
        </span>
      </div>
      <div className="h-2 bg-slate-100 dark:bg-white/8 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
          className={`h-full rounded-full ${barColor}`}
        />
      </div>
    </div>
  );
}

function DocumentCard({ doc, index }) {
  const [expanded, setExpanded] = useState(false);
  const results = doc?.results || {};
  const structured = results?.structured_data || {};
  const docInfo = doc?.document || {};

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="border border-slate-200 dark:border-white/7 rounded-xl overflow-hidden bg-white/60 dark:bg-white/3"
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-slate-50/50 dark:hover:bg-white/3 transition-colors text-left"
      >
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-50 dark:bg-blue-500/15 rounded-lg">
            <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              {docInfo.file_path?.split('/').pop() || `Document ${index + 1}`}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Type: {docInfo.document_type || docInfo.entity_type || 'N/A'} • Quality: {((results.document_quality || 0) * 100).toFixed(0)}%
            </p>
          </div>
        </div>
        {expanded
          ? <ChevronUp className="w-4 h-4 text-slate-400" />
          : <ChevronDown className="w-4 h-4 text-slate-400" />
        }
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-slate-100 dark:border-white/6"
          >
            <div className="p-4 space-y-3">
              {Object.keys(structured).length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Extracted Fields</p>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(structured).map(([key, value]) => (
                      <div key={key} className="bg-slate-50 dark:bg-white/4 p-2 rounded-lg">
                        <p className="text-[10px] text-slate-400 dark:text-slate-500 uppercase">{key.replace(/_/g, ' ')}</p>
                        <p className="text-xs text-slate-800 dark:text-slate-200 font-medium truncate">{String(value)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {results.doc_anomalies?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Anomalies Detected</p>
                  <ul className="space-y-1">
                    {results.doc_anomalies.map((a, i) => (
                      <li key={i} className="flex items-center text-xs text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-500/10 p-2 rounded-lg">
                        <AlertTriangle className="w-3 h-3 mr-2 shrink-0" />{a}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function ResultsDashboard({ result, onReset }) {
  if (!result) return null;
  const { practitioner, pipeline, errors } = result;
  const { extraction, verification, report } = pipeline;
  const config = getDecisionConfig(report.decision);
  const DecisionIcon = config.icon;
  const trustScore = verification.trustScore || 0;
  const trustPct = Math.min(trustScore, 100);
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (trustPct / 100) * circumference;

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-5xl mx-auto space-y-6">

      {/* Decision Header */}
      <div className="rounded-2xl overflow-hidden shadow-lg dark:shadow-black/30">
        <div className={`bg-linear-to-r ${config.gradient} p-6 md:p-8`}>
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-white/20 backdrop-blur-sm rounded-xl">
                <DecisionIcon className="w-8 h-8 text-white" />
              </div>
              <div className="text-white">
                <h2 className="text-2xl md:text-3xl font-bold tracking-tight">{config.label}</h2>
                <p className="text-white/80 text-sm mt-1">
                  {report.requiresHumanReview ? 'Requires human review' : 'Automated decision'}
                  {report.priority && (
                    <span className="ml-2 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-white/20">
                      {report.priority} Priority
                    </span>
                  )}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right text-white">
                <div className="text-3xl font-bold">{trustScore.toFixed(1)}</div>
                <div className="text-[10px] uppercase font-bold tracking-widest text-white/70">Trust Score</div>
              </div>
              <div className="relative w-24 h-24">
                <svg className="w-full h-full -rotate-90">
                  <circle cx="48" cy="48" r={radius} stroke="rgba(255,255,255,0.2)" strokeWidth="7" fill="transparent" />
                  <motion.circle
                    cx="48" cy="48" r={radius} stroke="white" strokeWidth="7" fill="transparent"
                    strokeDasharray={circumference}
                    initial={{ strokeDashoffset: circumference }}
                    animate={{ strokeDashoffset }}
                    transition={{ duration: 1.5, ease: 'easeOut' }}
                    strokeLinecap="round"
                  />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* Practitioner Info Bar */}
        <div className="bg-white dark:bg-[#161926] border-b border-slate-100 dark:border-white/6 px-6 py-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { icon: User, label: 'Name', value: practitioner.name },
              { icon: Hash, label: 'License', value: practitioner.registrationNumber },
              { icon: Stethoscope, label: 'Specialty', value: practitioner.specialty },
              { icon: MapPin, label: 'Country', value: practitioner.country },
            ].map(({ icon: Icon, label, value }) => (
              <div key={label} className="flex items-center space-x-2">
                <Icon className="w-4 h-4 text-slate-400 dark:text-slate-500 shrink-0" />
                <div>
                  <p className="text-[10px] text-slate-400 dark:text-slate-500 uppercase">{label}</p>
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">{value}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Agent Results Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Agent 1: Extraction */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 dark:border-white/6 flex items-center space-x-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-500/15 rounded-lg">
              <FileSearch className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 dark:text-white">Agent 1 — Extraction</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Document parsing & data extraction</p>
            </div>
          </div>
          <div className="p-6 space-y-4">
            <div className="grid grid-cols-3 gap-3">
              {[
                { value: extraction.totalDocuments, label: 'Documents', colorVal: 'text-blue-700 dark:text-blue-300', colorBg: 'bg-blue-50/50 dark:bg-blue-500/10', border: 'border-blue-100 dark:border-blue-500/20', labelColor: 'text-blue-500 dark:text-blue-400' },
                { value: `${(extraction.averageQuality * 100).toFixed(0)}%`, label: 'Avg Quality', colorVal: 'text-blue-700 dark:text-blue-300', colorBg: 'bg-blue-50/50 dark:bg-blue-500/10', border: 'border-blue-100 dark:border-blue-500/20', labelColor: 'text-blue-500 dark:text-blue-400' },
                { value: extraction.totalAnomalies, label: 'Anomalies', colorVal: 'text-amber-600 dark:text-amber-400', colorBg: 'bg-amber-50/50 dark:bg-amber-500/10', border: 'border-amber-100 dark:border-amber-500/20', labelColor: 'text-amber-500 dark:text-amber-400' },
              ].map(({ value, label, colorVal, colorBg, border, labelColor }) => (
                <div key={label} className={`${colorBg} p-3 rounded-xl text-center border ${border}`}>
                  <p className={`text-2xl font-bold ${colorVal}`}>{value}</p>
                  <p className={`text-[10px] uppercase font-semibold ${labelColor}`}>{label}</p>
                </div>
              ))}
            </div>
            <QualityBar value={extraction.averageQuality} max={1} label="Average Document Quality" />
            {extraction.documents?.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Document Details</p>
                {extraction.documents.map((doc, i) => <DocumentCard key={i} doc={doc} index={i} />)}
              </div>
            )}
          </div>
        </motion.div>

        {/* Agent 2: Verification */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 dark:border-white/6 flex items-center space-x-3">
            <div className="p-2 bg-violet-100 dark:bg-violet-500/15 rounded-lg">
              <ShieldCheck className="w-5 h-5 text-violet-600 dark:text-violet-400" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 dark:text-white">Agent 2 — Verification</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Credential scoring & anomaly detection</p>
            </div>
          </div>
          <div className="p-6 space-y-4">
            <QualityBar value={trustScore} max={100} label="Trust Score" />
            {verification.categoryBreakdown && Object.keys(verification.categoryBreakdown).length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Category Scores</p>
                <div className="space-y-2">
                  {Object.entries(verification.categoryBreakdown).map(([category, data]) => (
                    <div key={category} className="bg-violet-50/50 dark:bg-violet-500/[0.07] p-3 rounded-xl border border-violet-100 dark:border-violet-500/20">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-slate-700 dark:text-slate-300 capitalize">{category}</span>
                        <span className="text-sm font-bold text-violet-700 dark:text-violet-400">{data.average_score?.toFixed(1) || 'N/A'}/100</span>
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{data.count} document(s) verified</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {verification.issues?.length > 0 ? (
              <div>
                <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Issues Found ({verification.totalIssues})</p>
                <ul className="space-y-2">
                  {verification.issues.map((issue, idx) => (
                    <li key={idx} className="flex items-start text-sm text-red-700 dark:text-red-400 bg-red-50/50 dark:bg-red-500/[0.07] p-3 rounded-xl border border-red-100 dark:border-red-500/20">
                      <AlertTriangle className="w-4 h-4 text-red-500 dark:text-red-400 mr-2 mt-0.5 shrink-0" />
                      <span>{issue}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="flex items-center space-x-2 text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-500/10 p-3 rounded-xl border border-green-100 dark:border-green-500/20">
                <ShieldCheck className="w-4 h-4" />
                <span className="text-sm font-medium">No issues detected</span>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Agent 3: AI Decision */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="glass-card overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 dark:border-white/6 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-amber-100 dark:bg-amber-500/15 rounded-lg">
              <Sparkles className="w-5 h-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 dark:text-white">Agent 3 — AI Decision Engine</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Groq LLM analysis & final decision</p>
            </div>
          </div>
          {report.priority && (
            <span className={`text-xs font-bold px-3 py-1 rounded-full border ${getPriorityBadge(report.priority)}`}>
              {report.priority} PRIORITY
            </span>
          )}
        </div>

        <div className="p-6 space-y-5">
          {report.reasoning && (
            <div>
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">AI Reasoning</p>
              <div className="bg-linear-to-br from-slate-50 to-blue-50/30 dark:from-white/3 dark:to-blue-500/[0.05] p-5 rounded-xl border border-slate-200 dark:border-white/7">
                <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed italic">"{report.reasoning}"</p>
              </div>
            </div>
          )}

          {report.nextSteps?.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Recommended Next Steps</p>
              <ul className="space-y-2">
                {report.nextSteps.map((step, idx) => (
                  <li key={idx} className="flex items-center text-sm text-slate-700 dark:text-slate-300">
                    <ArrowRight className="w-4 h-4 text-brand-500 dark:text-brand-400 mr-2 shrink-0" />{step}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {report.documentReports?.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Per-Document Decisions</p>
              <div className="space-y-2">
                {report.documentReports.map((docReport, idx) => {
                  const docDecision = docReport.decision || {};
                  const docConfig = getDecisionConfig(docDecision.status);
                  const DocIcon = docConfig.icon;
                  return (
                    <div key={idx} className={`flex items-center justify-between p-3 rounded-xl border ${docConfig.border} ${docConfig.bg}`}>
                      <div className="flex items-center space-x-3">
                        <DocIcon className={`w-4 h-4 ${docConfig.text}`} />
                        <div>
                          <p className="text-sm font-medium text-slate-900 dark:text-white">{docReport.document?.name || `Document ${idx + 1}`}</p>
                          <p className="text-xs text-slate-500 dark:text-slate-400">{docReport.document?.entity_type}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`text-xs font-bold ${docConfig.text}`}>{docDecision.status}</p>
                        <p className="text-[10px] text-slate-500 dark:text-slate-400">Score: {docReport.scoring?.document_trust_score?.toFixed(1) || 'N/A'}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </motion.div>

      {/* Errors */}
      {errors?.length > 0 && (
        <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 rounded-xl p-4">
          <p className="text-sm font-semibold text-red-700 dark:text-red-400 mb-2">Pipeline Errors</p>
          <ul className="space-y-1">
            {errors.map((err, i) => <li key={i} className="text-xs text-red-600 dark:text-red-400">• {err}</li>)}
          </ul>
        </div>
      )}

      {/* Reset */}
      <div className="flex justify-center pt-2 pb-8">
        <button
          onClick={onReset}
          className="flex items-center space-x-2 bg-white dark:bg-white/5 border border-slate-300 dark:border-white/10 text-slate-700 dark:text-slate-300 font-medium px-8 py-3 rounded-xl hover:bg-slate-50 dark:hover:bg-white/8 transition-all shadow-sm hover:shadow-md dark:shadow-black/20"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Verify Another Practitioner</span>
        </button>
      </div>
    </motion.div>
  );
}
