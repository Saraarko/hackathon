import { useState } from 'react';
import { Routes, Route, useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { ShieldPlus } from 'lucide-react';
import UploadForm from './components/UploadForm';
import PipelineStatus from './components/PipelineStatus';
import ResultsDashboard from './components/ResultsDashboard';
import LandingPage from './components/LandingPage';
import ThemeToggle from './components/ThemeToggle';

function VerifyPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const role = searchParams.get('role') || 'doctor';
  const [appState, setAppState] = useState('IDLE');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pipelineStep, setPipelineStep] = useState(-1);
  const [verificationResult, setVerificationResult] = useState(null);
  const [pipelineError, setPipelineError] = useState(false);
  const [formKey, setFormKey] = useState(0);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleVerificationSubmit = async (formData) => {
    setIsSubmitting(true);
    setAppState('PIPELINE');
    setPipelineStep(0);
    setPipelineError(false);
    setVerificationResult(null);

    // Prepare FormData for API
    const data = new FormData();
    data.append('doctorName', formData.entityName || formData.doctorName);
    data.append('licenseNumber', formData.licenseNumber);
    data.append('specialty', formData.specialty);
    data.append('country', formData.country);
    data.append('entityType', formData.entityType || role);
    for (const file of formData.files) {
      data.append('files', file);
    }

    // Start API call
    let apiResult = null;
    let hasError = false;

    // Start animation and API call
    const animatePipeline = async () => {
      const steps = 3;
      for (let i = 0; i < steps; i++) {
        setPipelineStep(i);
        // Only progress if we haven't received the result yet
        if (i < steps - 1) {
          await new Promise(resolve => setTimeout(resolve, 2500));
        }
      }
    };

    // Run animation (don't await it, let it run in background)
    animatePipeline();

    try {
      const response = await axios.post(`${API_URL}/api/verify`, data, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      });
      apiResult = response.data;
    } catch (error) {
      console.error('API Error:', error);
      hasError = true;
    }

    setIsSubmitting(false);

    if (hasError) {
      setPipelineError(true);
    } else if (apiResult) {
      setPipelineStep(3);
      setVerificationResult(apiResult);
      setAppState('RESULT');
    }
  };

  const handleReset = () => {
    setAppState('IDLE');
    setPipelineStep(-1);
    setVerificationResult(null);
    setPipelineError(false);
    setFormKey(k => k + 1);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-[#0d0f1a] transition-colors duration-300">
      {/* Header */}
      <header className="bg-white/80 dark:bg-[#0d0f1a]/80 backdrop-blur-md border-b border-slate-200 dark:border-white/6 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div
            className="flex items-center space-x-3 cursor-pointer"
            onClick={() => navigate('/')}
          >
            <div className="bg-brand-600 p-2 rounded-xl text-white shadow-sm shadow-brand-500/20">
              <ShieldPlus className="w-6 h-6" />
            </div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight flex items-center">
              DocTome <span className="mx-2 text-slate-300 dark:text-white/20">|</span>
              <span className="text-slate-500 dark:text-slate-400 font-medium text-base mt-0.5">
                {{ doctor: 'Doctor Verification', clinic: 'Clinic Verification', lab: 'Laboratory Verification' }[role] || 'AI Verification Pipeline'}
              </span>
            </h1>
          </div>
          <ThemeToggle />
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">
        {appState === 'RESULT' && verificationResult ? (
          <ResultsDashboard result={verificationResult} onReset={handleReset} />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12">
            {/* Left Panel: Upload Form */}
            <div className="lg:col-span-5 xl:col-span-5 flex flex-col items-center lg:items-start">
              <UploadForm key={formKey} role={role} onSubmit={handleVerificationSubmit} isSubmitting={isSubmitting} />
            </div>

            {/* Right Panel: Pipeline Status */}
            <div className="lg:col-span-7 xl:col-span-7 flex flex-col items-center lg:items-center justify-start pt-4 lg:pt-0">
              {appState === 'IDLE' && (
                <div className="h-full flex flex-col items-center justify-center text-slate-400 p-12 text-center border-2 border-dashed border-slate-200 rounded-2xl w-full max-w-xl bg-white/30 backdrop-blur-sm">
                  <ShieldPlus className="w-16 h-16 text-slate-300 mb-4" />
                  <h3 className="text-lg font-medium text-slate-600 mb-2">Ready to Verify</h3>
                  <p className="text-sm">Submit practitioner details and credential documents to start the AI verification pipeline.</p>
                </div>
              )}

              {appState === 'PIPELINE' && (
                <PipelineStatus
                  currentStepIndex={pipelineStep}
                  isError={pipelineError}
                  isFinished={pipelineStep >= 3}
                />
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/verify" element={<VerifyPage />} />
    </Routes>
  );
}
