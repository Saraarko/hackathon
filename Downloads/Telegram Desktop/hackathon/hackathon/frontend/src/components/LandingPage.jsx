import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Stethoscope, Building2, Microscope, ShieldCheck,
  ArrowRight, Clock, Heart, BadgeCheck, ShieldPlus,
} from 'lucide-react';
import ThemeToggle from './ThemeToggle';

const roles = [
  {
    id: 'doctor',
    title: 'Individual Doctor',
    icon: Stethoscope,
    description: 'For licensed practitioners who need fast, reliable credential verification and professional identity management.',
    lightGradient: 'from-blue-50 to-indigo-50',
    darkGradient: 'dark:from-blue-950/40 dark:to-indigo-950/40',
    iconBg: 'bg-blue-100 dark:bg-blue-900/50',
    iconColor: 'text-blue-600 dark:text-blue-400',
    border: 'border-blue-100/60 dark:border-blue-800/30',
    buttonBg: 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600',
    glow: 'hover:shadow-blue-500/20',
  },
  {
    id: 'clinic',
    title: 'Medical Clinic',
    icon: Building2,
    description: 'For clinics and outpatient facilities managing staff credentials, facility licenses, and compliance records.',
    lightGradient: 'from-sky-50 to-blue-50',
    darkGradient: 'dark:from-sky-950/40 dark:to-blue-950/40',
    iconBg: 'bg-sky-100 dark:bg-sky-900/50',
    iconColor: 'text-sky-600 dark:text-sky-400',
    border: 'border-sky-100/60 dark:border-sky-800/30',
    buttonBg: 'bg-sky-600 hover:bg-sky-700 dark:bg-sky-500 dark:hover:bg-sky-600',
    glow: 'hover:shadow-sky-500/20',
  },
  {
    id: 'lab',
    title: 'Diagnostic Lab',
    icon: Microscope,
    description: 'For laboratories and diagnostic centers requiring certification, equipment validation, and technician credentialing.',
    lightGradient: 'from-indigo-50 to-violet-50',
    darkGradient: 'dark:from-indigo-950/40 dark:to-violet-950/40',
    iconBg: 'bg-indigo-100 dark:bg-indigo-900/50',
    iconColor: 'text-indigo-600 dark:text-indigo-400',
    border: 'border-indigo-100/60 dark:border-indigo-800/30',
    buttonBg: 'bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600',
    glow: 'hover:shadow-indigo-500/20',
  },
];

const features = [
  { icon: Clock, title: 'Fast & Reliable', description: 'Quick turnaround with accurate verification.' },
  { icon: Heart, title: 'Trusted by Healthcare', description: 'Secure and trusted by healthcare professionals.' },
  { icon: BadgeCheck, title: 'Built for Compliance', description: 'Designed to meet industry standards and regulations.' },
];

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.15 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } },
};

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-[#0d0f1a] transition-colors duration-300">
      {/* Header */}
      <header className="bg-white/80 dark:bg-[#0d0f1a]/80 backdrop-blur-md border-b border-slate-200 dark:border-white/6 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-brand-600 p-2 rounded-xl text-white shadow-sm shadow-brand-500/20">
              <ShieldPlus className="w-6 h-6" />
            </div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">DocTome</h1>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="flex-1">
        {/* Hero */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-8 text-center">
          <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <div className="inline-flex items-center gap-2 bg-brand-50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400 px-4 py-1.5 rounded-full text-sm font-medium mb-6 border border-brand-100 dark:border-brand-500/20">
              <ShieldCheck className="w-4 h-4" />
              Trusted Verification Platform
            </div>
            <h2 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-slate-900 dark:text-white leading-tight tracking-tight mb-6">
              Verify Medical<br />
              <span className="bg-linear-to-r from-brand-600 to-indigo-600 dark:from-brand-400 dark:to-indigo-400 bg-clip-text text-transparent">
                Credentials with AI
              </span>
            </h2>
            <p className="text-lg text-slate-500 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
              Select your clinical role to begin the AI-powered verification pipeline.
              DocTome uses a multi-agent LangGraph system to extract, verify, and certify medical credentials automatically.
            </p>
          </motion.div>
        </section>

        {/* Role Cards */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {roles.map((role) => {
              const Icon = role.icon;
              return (
                <motion.div
                  key={role.id}
                  variants={itemVariants}
                  whileHover={{ y: -6, transition: { duration: 0.25 } }}
                  className={`group relative bg-linear-to-br ${role.lightGradient} ${role.darkGradient}
                              rounded-2xl border ${role.border}
                              shadow-lg ${role.glow} hover:shadow-xl
                              dark:shadow-black/20 dark:hover:shadow-black/40
                              overflow-hidden cursor-pointer transition-all duration-300`}
                  onClick={() => navigate(`/verify?role=${role.id}`)}
                >
                  <div className="p-8 pb-6 text-center">
                    <div className={`inline-flex items-center justify-center w-20 h-20 rounded-2xl ${role.iconBg} mb-6 transition-transform duration-300 group-hover:scale-110`}>
                      <Icon className={`w-10 h-10 ${role.iconColor}`} strokeWidth={1.5} />
                    </div>
                    <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">{role.title}</h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed mb-6">{role.description}</p>
                    <button
                      className={`inline-flex items-center gap-2 ${role.buttonBg} text-white px-6 py-3 rounded-full text-sm font-semibold shadow-lg transition-all duration-300 group-hover:gap-3`}
                      onClick={(e) => { e.stopPropagation(); navigate(`/verify?role=${role.id}`); }}
                    >
                      Get Verified
                      <ArrowRight className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-0.5" />
                    </button>
                  </div>
                  <div className="h-1.5 w-full bg-linear-to-r from-transparent via-brand-500/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                </motion.div>
              );
            })}
          </motion.div>
        </section>

        {/* Features Bar */}
        <section className="border-t border-slate-200 dark:border-white/6 bg-white/60 dark:bg-white/2 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
            <motion.div
              className="grid grid-cols-1 md:grid-cols-3 gap-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.5 }}
            >
              {features.map((feat) => {
                const FIcon = feat.icon;
                return (
                  <div key={feat.title} className="flex items-center gap-4">
                    <div className="shrink-0 w-12 h-12 rounded-xl bg-brand-50 dark:bg-brand-500/10 flex items-center justify-center border border-brand-100 dark:border-brand-500/20">
                      <FIcon className="w-6 h-6 text-brand-600 dark:text-brand-400" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-900 dark:text-white">{feat.title}</h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{feat.description}</p>
                    </div>
                  </div>
                );
              })}
            </motion.div>
          </div>
        </section>
      </main>
    </div>
  );
}
