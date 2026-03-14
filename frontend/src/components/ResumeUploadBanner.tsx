import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

interface ResumeUploadBannerProps {
  onParsed?: (techStack: string[]) => void;
  hasExisting?: boolean;
}

export default function ResumeUploadBanner({ onParsed, hasExisting }: ResumeUploadBannerProps) {
  const queryClient = useQueryClient();

  const upload = useMutation({
    mutationFn: (file: File) => api.uploadResume(file),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['resumeProfile'] });
      if (data?.tech_stack?.length && onParsed) {
        onParsed(data.tech_stack.map((t: string) => t.toLowerCase()));
      }
    },
  });

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) upload.mutate(file);
  };

  return (
    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <p className="text-sm font-semibold text-indigo-900">
            {hasExisting ? 'Update your resume' : 'Want to skip the clicking? Upload your resume.'}
          </p>
          <p className="text-xs text-indigo-700 mt-1">
            {hasExisting
              ? 'Re-upload to refresh your tech stack and job matches.'
              : "We'll read your tech stack and auto-select the right technologies for you."}
          </p>
        </div>
        <label className="flex-shrink-0 inline-flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 cursor-pointer">
          <span>{upload.isPending ? 'Parsing...' : hasExisting ? 'Re-upload Resume' : 'Upload Resume'}</span>
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={handleFile}
            className="hidden"
            disabled={upload.isPending}
          />
        </label>
      </div>
      {upload.isSuccess && (
        <p className="text-xs text-green-600 mt-2">Resume parsed! Tech stack updated.</p>
      )}
      {upload.isError && (
        <p className="text-xs text-red-600 mt-2">{upload.error.message}</p>
      )}
    </div>
  );
}
