import { Helmet } from 'react-helmet-async';

interface SEOProps {
  title?: string;
  description?: string;
}

const DEFAULT_DESCRIPTION = 'Upload your resume and instantly see matching jobs from thousands of companies. RepoRadar combines job boards, ATS feeds, and GitHub analysis to surface roles that match your skills.';

export default function SEO({ title, description = DEFAULT_DESCRIPTION }: SEOProps) {
  const fullTitle = title ? `${title} | RepoRadar` : 'RepoRadar — Find Jobs at Companies That Use Your Tech Stack';

  return (
    <Helmet>
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description} />
    </Helmet>
  );
}
