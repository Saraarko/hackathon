import { useState, useRef } from 'react';
import { UploadCloud, File, X, CheckCircle2, Plus, Stethoscope, Building2, Microscope } from 'lucide-react';

const COUNTRIES = ['Algeria', 'Tunisia', 'Morocco', 'France', 'United States', 'United Kingdom', 'Canada', 'Germany'];

// ── Role configurations ──────────────────────────────────
const ROLES = {
  doctor: {
    icon: Stethoscope,
    label: 'Individual Doctor',
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-50 dark:bg-blue-500/10',
    border: 'border-blue-200 dark:border-blue-500/30',
    accent: 'bg-blue-600',
    entityLabel: 'Full Name',
    entityPlaceholder: 'e.g. Dr. Ahmed Ben Ali',
    licenseLabel: 'License / Registration Number',
    licensePlaceholder: 'e.g. OM-2019-81976',
    extraFields: [
      { name: 'specialty', label: 'Medical Specialty', type: 'select', options: [
        'General Practice', 'Cardiology', 'Pediatrics', 'Surgery', 'Radiology',
        'Dermatology', 'Neurology', 'Orthopedics', 'Psychiatry', 'Other',
      ]},
    ],
    docTypes: 'Medical License, Diploma, National ID',
    docHint: 'Upload your license + diploma for best results (score improves significantly)',
  },
  clinic: {
    icon: Building2,
    label: 'Medical Clinic',
    color: 'text-sky-600 dark:text-sky-400',
    bg: 'bg-sky-50 dark:bg-sky-500/10',
    border: 'border-sky-200 dark:border-sky-500/30',
    accent: 'bg-sky-600',
    entityLabel: 'Clinic / Hospital Name',
    entityPlaceholder: 'e.g. Clinique El Hayat',
    licenseLabel: 'MOH Registration Number',
    licensePlaceholder: 'e.g. MOH-ALG-2021-004',
    extraFields: [
      { name: 'directorName', label: 'Medical Director Name', type: 'text', placeholder: 'e.g. Dr. Sara Mansouri' },
      { name: 'address', label: 'Clinic Address', type: 'text', placeholder: 'e.g. 12 Rue Didouche, Alger' },
      { name: 'specialty', label: 'Facility Type', type: 'select', options: [
        'General Clinic', 'Polyclinic', 'Hospital', 'Maternity Clinic',
        'Surgical Center', 'Rehabilitation Center', 'Dental Clinic', 'Other',
      ]},
    ],
    docTypes: 'Operating License, MOH Certificate, Director Credentials',
    docHint: 'Upload the official operating license issued by the Ministry of Health',
  },
  lab: {
    icon: Microscope,
    label: 'Diagnostic Laboratory',
    color: 'text-indigo-600 dark:text-indigo-400',
    bg: 'bg-indigo-50 dark:bg-indigo-500/10',
    border: 'border-indigo-200 dark:border-indigo-500/30',
    accent: 'bg-indigo-600',
    entityLabel: 'Laboratory Name',
    entityPlaceholder: 'e.g. Laboratoire BioAnalyse',
    licenseLabel: 'ISO / Accreditation Number',
    licensePlaceholder: 'e.g. ISO-9001-2024-LAB-042',
    extraFields: [
      { name: 'directorName', label: 'Laboratory Director', type: 'text', placeholder: 'e.g. Dr. Karim Boudiaf' },
      { name: 'specialty', label: 'Laboratory Type', type: 'select', options: [
        'Clinical Biology', 'Microbiology', 'Pathology', 'Radiology',
        'Genetics', 'Toxicology', 'Immunology', 'Multi-discipline', 'Other',
      ]},
      { name: 'equipmentType', label: 'Primary Equipment / Analyses', type: 'text', placeholder: 'e.g. PCR, Hematology, Biochemistry' },
    ],
    docTypes: 'ISO Certificate, Accreditation Letter, Equipment Certificates',
    docHint: 'Upload your ISO accreditation certificate for the highest trust score',
  },
};

export default function UploadForm({ role = 'doctor', onSubmit, isSubmitting }) {
  const cfg = ROLES[role] || ROLES.doctor;
  const RoleIcon = cfg.icon;

  const [formData, setFormData] = useState({
    entityName: '', licenseNumber: '', country: '', specialty: '',
    directorName: '', address: '', equipmentType: '',
    entityType: role, files: [],
  });
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  const dragCounter = useRef(0);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleDragEnter = (e) => { e.preventDefault(); e.stopPropagation(); dragCounter.current += 1; setIsDragging(true); };
  const handleDragLeave = (e) => { e.preventDefault(); e.stopPropagation(); dragCounter.current -= 1; if (dragCounter.current <= 0) { dragCounter.current = 0; setIsDragging(false); } };
  const handleDragOver  = (e) => { e.preventDefault(); e.stopPropagation(); e.dataTransfer.dropEffect = 'copy'; };
  const handleDrop = (e) => {
    e.preventDefault(); e.stopPropagation();
    dragCounter.current = 0; setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) setFormData(prev => ({ ...prev, files: [...prev.files, ...files] }));
  };
  const handleFileSelect = (e) => {
    if (e.target.files?.length > 0) setFormData(prev => ({ ...prev, files: [...prev.files, ...Array.from(e.target.files)] }));
    if (fileInputRef.current) fileInputRef.current.value = '';
  };
  const removeFile = (i) => setFormData(prev => ({ ...prev, files: prev.files.filter((_, idx) => idx !== i) }));

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ ...formData, doctorName: formData.entityName });
  };

  return (
    <div className="glass-card p-6 md:p-8 w-full max-w-xl">
      {/* Role badge */}
      <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold mb-5 border ${cfg.bg} ${cfg.color} ${cfg.border}`}>
        <RoleIcon className="w-3.5 h-3.5" />
        {cfg.label}
      </div>

      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">Verification Details</h2>
        <p className="text-slate-500 dark:text-slate-400 mt-1 text-sm">Fill in the information and upload supporting documents.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">

        {/* Entity name + license */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">{cfg.entityLabel}</label>
          <input required type="text" name="entityName" value={formData.entityName}
            onChange={handleChange} placeholder={cfg.entityPlaceholder} className="premium-input" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">{cfg.licenseLabel}</label>
            <input required type="text" name="licenseNumber" value={formData.licenseNumber}
              onChange={handleChange} placeholder={cfg.licensePlaceholder} className="premium-input" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Country</label>
            <select required name="country" value={formData.country} onChange={handleChange} className="premium-input appearance-none">
              <option value="" disabled>Select country</option>
              {COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        </div>

        {/* Role-specific extra fields */}
        {cfg.extraFields.map(field => (
          <div key={field.name}>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">{field.label}</label>
            {field.type === 'select' ? (
              <select required name={field.name} value={formData[field.name]} onChange={handleChange} className="premium-input appearance-none">
                <option value="" disabled>Select...</option>
                {field.options.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            ) : (
              <input required type="text" name={field.name} value={formData[field.name]}
                onChange={handleChange} placeholder={field.placeholder} className="premium-input" />
            )}
          </div>
        ))}

        {/* File upload */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
            Documents <span className="text-slate-400 font-normal">({formData.files.length} selected)</span>
          </label>

          {formData.files.length > 0 && (
            <div className="space-y-2 mb-3">
              {formData.files.map((file, idx) => (
                <div key={`${file.name}-${idx}`} className="glass-panel p-3 flex items-center justify-between">
                  <div className="flex items-center space-x-3 overflow-hidden">
                    <div className={`p-1.5 rounded-lg shrink-0 ${cfg.bg} ${cfg.color}`}><File className="w-4 h-4" /></div>
                    <div className="truncate">
                      <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">{file.name}</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                  </div>
                  <button type="button" onClick={() => removeFile(idx)}
                    className="p-1 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-colors shrink-0">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Drop zone */}
          <div
            onDragEnter={handleDragEnter} onDragLeave={handleDragLeave}
            onDragOver={handleDragOver} onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            role="button" tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
            className={`relative border-2 border-dashed rounded-xl p-7 text-center cursor-pointer transition-all duration-200 outline-none
              ${isDragging
                ? `border-blue-500 scale-[1.01] shadow-lg ${cfg.bg}`
                : 'border-slate-300 dark:border-white/10 hover:border-blue-400 dark:hover:border-blue-500/40 hover:bg-slate-50 dark:hover:bg-white/3'
              }`}
          >
            {isDragging && <div className="absolute inset-0 rounded-xl z-10" />}
            <div className="flex flex-col items-center justify-center space-y-2">
              <div className={`p-3 rounded-full transition-colors ${isDragging ? cfg.bg : 'bg-white dark:bg-white/6 shadow-sm'}`}>
                {isDragging ? <UploadCloud className={`w-6 h-6 ${cfg.color}`} /> : formData.files.length > 0 ? <Plus className={`w-6 h-6 ${cfg.color}`} /> : <UploadCloud className={`w-6 h-6 ${cfg.color}`} />}
              </div>
              <div>
                <p className={`text-sm font-semibold ${cfg.color}`}>
                  {isDragging ? 'Release to upload' : formData.files.length > 0 ? 'Add more documents' : 'Click to upload or drag & drop'}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{cfg.docTypes}</p>
              </div>
            </div>
          </div>

          {/* Hint */}
          <p className={`text-xs mt-2 ${cfg.color} opacity-80`}>💡 {cfg.docHint}</p>

          <input ref={fileInputRef} type="file" onChange={handleFileSelect} className="hidden" accept=".pdf,.jpg,.jpeg,.png" multiple />
        </div>

        <button type="submit" disabled={isSubmitting || formData.files.length === 0} className="premium-button w-full relative overflow-hidden group">
          {isSubmitting ? (
            <span className="flex items-center space-x-2">
              <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span>Running Verification Pipeline...</span>
            </span>
          ) : (
            <span className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>Start Verification ({formData.files.length} doc{formData.files.length !== 1 ? 's' : ''})</span>
            </span>
          )}
          <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
        </button>
      </form>
    </div>
  );
}
