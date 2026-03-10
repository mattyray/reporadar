/**
 * Shared chip component with category-based colors.
 *
 * Categories:
 * - stack (indigo): backend, frontend, database, ai_ml — the tech stack
 * - ai_tool (purple): AI coding tools like Claude Code, Cursor, etc.
 * - infra (gray): Docker, CI/CD, Tests, Deployed
 */

const CATEGORY_STYLES: Record<string, string> = {
  // Stack categories all use indigo
  backend: 'bg-indigo-100 text-indigo-700',
  frontend: 'bg-indigo-100 text-indigo-700',
  database: 'bg-indigo-100 text-indigo-700',
  ai_ml: 'bg-indigo-100 text-indigo-700',
  // AI tools use purple
  ai_tool: 'bg-purple-100 text-purple-700',
  // Infrastructure uses gray
  infrastructure: 'bg-gray-100 text-gray-700',
  infra: 'bg-gray-100 text-gray-700',
};

interface TechChipProps {
  name: string;
  category?: string;
  size?: 'sm' | 'md';
}

export default function TechChip({ name, category = 'backend', size = 'sm' }: TechChipProps) {
  const colorClass = CATEGORY_STYLES[category] || CATEGORY_STYLES.backend;
  const sizeClass = size === 'md'
    ? 'px-2.5 py-1 rounded-full text-xs font-medium'
    : 'px-2 py-0.5 rounded text-xs';

  return (
    <span className={`${colorClass} ${sizeClass}`}>
      {name}
    </span>
  );
}


/**
 * Helper to group StackDetection items by display category.
 */
export interface GroupedTechs {
  stack: string[];
  aiTools: string[];
  infra: string[];
}

export function groupByCategory(
  detections: Array<{ technology_name: string; category: string }>,
): GroupedTechs {
  const stack: string[] = [];
  const aiTools: string[] = [];
  const infra: string[] = [];

  const seen = new Set<string>();
  for (const d of detections) {
    if (seen.has(d.technology_name)) continue;
    seen.add(d.technology_name);

    if (d.category === 'ai_tool') {
      aiTools.push(d.technology_name);
    } else if (d.category === 'infrastructure') {
      infra.push(d.technology_name);
    } else {
      stack.push(d.technology_name);
    }
  }
  return { stack, aiTools, infra };
}
