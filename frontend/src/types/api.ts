export interface UserProfile {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  github_connected: boolean;
}

export interface SearchConfig {
  name?: string;
  stack_requirements: {
    must_have: string[];
    nice_to_have?: string[];
    ai_tool_signals?: string[];
  };
  filters?: {
    org_only?: boolean;
    min_stars?: number;
    min_contributors?: number;
    updated_within_days?: number;
  };
  max_results?: number;
}

export interface SearchQuery {
  id: string;
  name: string;
  config: SearchConfig;
  status: 'pending' | 'running' | 'completed' | 'failed';
  total_repos_found: number;
  total_orgs_found: number;
  error_message: string;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface SearchResult {
  id: number;
  organization_id: number;
  match_score: number;
  matched_stack: string[];
  matched_ai_tools: string[];
  matched_infra: string[];
  organization_name: string;
  organization_login: string;
  organization_avatar: string;
  repo_name: string;
  created_at: string;
  is_hiring: boolean;
}

export interface Organization {
  id: number;
  github_login: string;
  name: string;
  description: string;
  website: string;
  email: string;
  location: string;
  avatar_url: string;
  public_repos_count: number;
  github_url: string;
  repos: Repo[];
  top_contributors: Contributor[];
}

export interface Repo {
  id: number;
  name: string;
  full_name: string;
  description: string;
  url: string;
  stars: number;
  forks: number;
  has_claude_md: boolean;
  has_cursor_config: boolean;
  has_copilot_config: boolean;
  has_windsurf_config: boolean;
  has_aider_config: boolean;
  has_codeium_config: boolean;
  has_continue_config: boolean;
  has_bolt_config: boolean;
  has_v0_config: boolean;
  has_lovable_config: boolean;
  has_idx_config: boolean;
  has_amazonq_config: boolean;
  has_cline_config: boolean;
  has_roo_config: boolean;
  has_codex_config: boolean;
  has_docker: boolean;
  has_ci_cd: boolean;
  has_tests: boolean;
  has_deployment_config: boolean;
  last_pushed_at: string | null;
  stack_detections: StackDetection[];
  ai_analysis_status: 'none' | 'pending' | 'analyzing' | 'completed' | 'failed';
  ai_analysis: RepoAnalysis | null;
  ai_analyzed_at: string | null;
}

export interface RepoAnalysis {
  summary: string;
  tech_stack: {
    languages: string[];
    frameworks: string[];
    databases: string[];
    infrastructure: string[];
    notable_libraries: string[];
    ai_tools: string[];
  };
  architecture: {
    pattern: string;
    description: string;
    key_directories: Array<{ path: string; purpose: string }>;
  };
  code_quality: {
    has_tests: boolean;
    has_ci_cd: boolean;
    has_linting: boolean;
    has_type_checking: boolean;
    has_documentation: boolean;
    quality_notes: string;
  };
  maturity: {
    stage: string;
    signals: string[];
    team_size_estimate: string;
    activity_assessment: string;
  };
  what_they_are_building: string;
  notable_patterns: string[];
  interesting_for_job_seekers: {
    why_work_here: string;
    tech_culture_signals: string[];
    potential_roles: string[];
  };
}

export interface StackDetection {
  technology_name: string;
  category: string;
  source_file: string;
}

export interface Contributor {
  github_username: string;
  name: string;
  email: string;
  company: string;
  bio: string;
  location: string;
  avatar_url: string;
  contributions: number;
  profile_url: string;
}

export interface ResumeProfile {
  id: number;
  file_type: string;
  parsed_data: Record<string, unknown>;
  summary: string;
  key_projects: string[];
  tech_stack: string[];
  years_experience: number | null;
  story_hook: string;
  parsed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobListing {
  id: number;
  external_id: string;
  title: string;
  department: string;
  location: string;
  employment_type: string;
  salary: string;
  detected_techs: string[];
  apply_url: string;
  is_active: boolean;
  posted_at: string | null;
  last_seen_at: string;
  source: 'ats' | 'remoteok' | 'remotive' | 'wwr' | 'hn';
  source_url: string;
  company_name: string;
  ats_platform: string;
  organization_id: number | null;
  avatar_url: string;
}

export interface JobCheckResponse {
  status: 'cached' | 'probing';
  detail?: string;
  jobs?: JobListing[];
}

export interface CompanyLookupResult {
  login: string;
  github_id: number;
  avatar_url: string;
  type: 'Organization' | 'User';
  url: string;
}

export interface CompanyScanResponse {
  status: 'completed' | 'scanning';
  organization?: Organization;
}
