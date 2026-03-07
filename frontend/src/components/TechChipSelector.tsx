import { useState } from 'react';

const POPULAR_TECHS = [
  // Languages & Frameworks
  'python', 'django', 'flask', 'fastapi',
  'javascript', 'typescript', 'react', 'next.js', 'vue', 'angular', 'svelte',
  'node.js', 'express', 'ruby', 'rails', 'go', 'rust',
  'java', 'spring', 'kotlin', 'swift',
  // Data & Infrastructure
  'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
  'docker', 'kubernetes', 'aws', 'gcp', 'terraform',
  // AI & ML
  'langchain', 'openai', 'pytorch', 'tensorflow',
  // Other
  'graphql', 'celery', 'kafka', 'rabbitmq',
];

interface TechChipSelectorProps {
  selected: string[];
  onChange: (techs: string[]) => void;
  label?: string;
  hint?: string;
}

export default function TechChipSelector({ selected, onChange, label, hint }: TechChipSelectorProps) {
  const [customInput, setCustomInput] = useState('');

  const toggle = (tech: string) => {
    if (selected.includes(tech)) {
      onChange(selected.filter((t) => t !== tech));
    } else {
      onChange([...selected, tech]);
    }
  };

  const addCustom = () => {
    const tech = customInput.trim().toLowerCase();
    if (tech && !selected.includes(tech)) {
      onChange([...selected, tech]);
    }
    setCustomInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addCustom();
    }
  };

  // Show selected-but-not-popular chips at the top
  const customSelected = selected.filter((t) => !POPULAR_TECHS.includes(t));

  return (
    <div>
      {label && <p className="text-sm font-medium text-gray-700 mb-2">{label}</p>}
      {hint && <p className="text-xs text-gray-500 mb-3">{hint}</p>}

      <div className="flex flex-wrap gap-2 mb-3">
        {/* Custom selected chips first */}
        {customSelected.map((tech) => (
          <button
            key={tech}
            type="button"
            onClick={() => toggle(tech)}
            className="px-3 py-1.5 rounded-full text-sm font-medium bg-indigo-600 text-white cursor-pointer"
          >
            {tech} x
          </button>
        ))}
        {/* Popular chips */}
        {POPULAR_TECHS.map((tech) => (
          <button
            key={tech}
            type="button"
            onClick={() => toggle(tech)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors cursor-pointer ${
              selected.includes(tech)
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {tech}
          </button>
        ))}
      </div>

      {/* Add custom tech */}
      <div className="flex gap-2">
        <input
          type="text"
          value={customInput}
          onChange={(e) => setCustomInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Add a technology..."
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm flex-1"
        />
        <button
          type="button"
          onClick={addCustom}
          disabled={!customInput.trim()}
          className="px-3 py-1.5 bg-gray-200 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-300 disabled:opacity-50 cursor-pointer"
        >
          Add
        </button>
      </div>
    </div>
  );
}
