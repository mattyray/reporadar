export interface UserProfile {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  github_connected: boolean;
  has_hunter_key: boolean;
  has_apollo_key: boolean;
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
  organization_name: string;
  organization_login: string;
  organization_avatar: string;
  repo_name: string;
  created_at: string;
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
  has_docker: boolean;
  has_ci_cd: boolean;
  has_tests: boolean;
  has_deployment_config: boolean;
  last_pushed_at: string | null;
  stack_detections: StackDetection[];
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

export interface Contact {
  id: number;
  provider: string;
  first_name: string;
  last_name: string;
  email: string;
  email_confidence: number;
  position: string;
  department: string;
  seniority: string;
  linkedin_url: string;
  is_engineering_lead: boolean;
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

export interface OutreachMessage {
  id: string;
  organization_name: string;
  message_type: string;
  subject: string;
  body: string;
  created_at: string;
}
