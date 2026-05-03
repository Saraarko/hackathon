import { motion } from 'framer-motion';
import { ShieldAlert, ShieldCheck, ShieldX, RefreshCw, AlertTriangle, Info, ArrowRight } from 'lucide-react';

export default function ResultCard({ result, onReset }) {
  if (!result) return null;

  const {
    status,
    confidenceScore,
    extractedData,
    anomalyRisk,
    issues,
    reasoning,
    nextSteps
  } = result;

  const getStatusConfig = () => {
    switch (status) {
      case 'APPROVED': return { color: 'bg-green-500', bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200', icon: ShieldCheck };
      case 'REJECTED': return { color: 'bg-red-500', bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', icon: ShieldX };
      case 'FLAGGED': return { color: 'bg-yellow-500', bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200', icon: AlertTriangle };
      case 'FLAGGED_FOR_HUMAN': return { color: 'bg-orange-500', bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200', icon: ShieldAlert };
      default: return { color: 'bg-slate-500', bg: 'bg-slate-50', text: 'text-slate-700', border: 'border-slate-200', icon: Info };
    }
  };

  const getRiskConfig = () => {
    switch (anomalyRisk) {
      case 'LOW': return 'bg-green-100 text-green-700 border-green-200';
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'HIGH': return 'bg-red-100 text-red-700 border-red-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const config = getStatusConfig();
  const StatusIcon = config.icon;
  
  // Circular progress calculation
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (confidenceScore / 100) * circumference;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      className="glass-card w-full max-w-xl overflow-hidden flex flex-col"
    >
      {/* Header Status Bar */}
      <div className={`px-6 py-4 border-b flex items-center justify-between ${config.bg} ${config.border}`}>
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg bg-white shadow-sm text-white ${config.text}`}>
            <StatusIcon className="w-6 h-6" />
          </div>
          <div>
            <h3 className={`text-lg font-bold tracking-wide ${config.text}`}>
              {status.replace(/_/g, ' ')}
            </h3>
            <p className={`text-xs font-medium opacity-80 ${config.text}`}>Verification Result</p>
          </div>
        </div>
        
        {/* Confidence Score Circle */}
        <div className="flex items-center space-x-3">
          <div className="text-right">
            <div className="text-2xl font-bold text-slate-900">{confidenceScore}%</div>
            <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Confidence</div>
          </div>
          <div className="relative w-16 h-16">
            <svg className="w-full h-full transform -rotate-90">
              <circle cx="32" cy="32" r={radius} stroke="currentColor" strokeWidth="6" fill="transparent" className="text-slate-200" />
              <circle
                cx="32"
                cy="32"
                r={radius}
                stroke="currentColor"
                strokeWidth="6"
                fill="transparent"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                className={`transition-all duration-1000 ease-out ${config.text}`}
                strokeLinecap="round"
              />
            </svg>
          </div>
        </div>
      </div>

      <div className="p-6 md:p-8 space-y-6 flex-1 overflow-y-auto">
        
        {/* Extracted Data Summary */}
        <div>
          <h4 className="text-sm font-semibold text-slate-900 mb-3 uppercase tracking-wider">Extracted Details</h4>
          <div className="grid grid-cols-2 gap-4 bg-slate-50/50 p-4 rounded-xl border border-slate-100">
            <div>
              <p className="text-xs text-slate-500">Practitioner Name</p>
              <p className="font-medium text-slate-900">{extractedData?.name || 'N/A'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">License Number</p>
              <p className="font-medium text-slate-900">{extractedData?.license || 'N/A'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Specialty</p>
              <p className="font-medium text-slate-900">{extractedData?.specialty || 'N/A'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Expiry Date</p>
              <p className="font-medium text-slate-900">{extractedData?.expiry || 'N/A'}</p>
            </div>
          </div>
        </div>

        {/* Risk & Issues */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">Anomaly Risk</h4>
            <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${getRiskConfig()}`}>
              {anomalyRisk} RISK
            </span>
          </div>
          
          {issues && issues.length > 0 && (
            <ul className="space-y-2">
              {issues.map((issue, idx) => (
                <li key={idx} className="flex items-start text-sm text-slate-700 bg-red-50/50 p-2.5 rounded-lg border border-red-100">
                  <AlertTriangle className="w-4 h-4 text-red-500 mr-2 mt-0.5 flex-shrink-0" />
                  <span>{issue}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* AI Reasoning */}
        <div>
          <h4 className="text-sm font-semibold text-slate-900 mb-2 uppercase tracking-wider">AI Reasoning</h4>
          <p className="text-sm text-slate-600 bg-slate-50 p-4 rounded-xl border border-slate-200 leading-relaxed italic">
            "{reasoning}"
          </p>
        </div>

        {/* Next Steps */}
        {nextSteps && nextSteps.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-slate-900 mb-2 uppercase tracking-wider">Recommended Next Steps</h4>
            <ul className="space-y-2">
              {nextSteps.map((step, idx) => (
                <li key={idx} className="flex items-center text-sm text-slate-700">
                  <ArrowRight className="w-4 h-4 text-brand-500 mr-2 flex-shrink-0" />
                  {step}
                </li>
              ))}
            </ul>
          </div>
        )}

      </div>

      <div className="p-6 border-t border-slate-100 bg-slate-50/30">
        <button
          onClick={onReset}
          className="w-full flex items-center justify-center space-x-2 bg-white border border-slate-300 text-slate-700 font-medium py-2.5 rounded-xl hover:bg-slate-50 transition-colors shadow-sm"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Verify Another Practitioner</span>
        </button>
      </div>
    </motion.div>
  );
}
