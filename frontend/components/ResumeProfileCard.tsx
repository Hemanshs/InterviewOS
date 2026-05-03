"use client";

import type { ResumeProfile } from "@/types/interview";

interface ResumeProfileCardProps {
  profile: ResumeProfile;
  fileName: string;
  onRemove: () => void;
}

function uniqueSkills(profile: ResumeProfile) {
  const combined = [
    ...profile.skills.languages,
    ...profile.skills.frameworks,
    ...profile.skills.databases,
    ...profile.skills.cloud_devops,
    ...profile.skills.testing_tools,
    ...profile.skills.other,
  ];

  return Array.from(new Set(combined)).slice(0, 8);
}

export function ResumeProfileCard({
  profile,
  fileName,
  onRemove,
}: ResumeProfileCardProps) {
  const skills = uniqueSkills(profile);
  const experienceLabel =
    profile.total_experience_years !== null
      ? `${profile.total_experience_years} years`
      : null;
  const firstProject = profile.projects[0];

  return (
    <section className="rounded-sm border border-white/10 border-l-4 border-l-emerald-500 bg-[#1a1a1a] p-6">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="font-mono text-xs uppercase tracking-[0.22em] text-emerald-300">
            Resume loaded
          </div>
          <div className="text-sm text-[#9a9a9a]">{fileName}</div>
        </div>
        <button
          onClick={onRemove}
          className="text-xs uppercase tracking-[0.16em] text-[#a7a7a7] transition-colors hover:text-[#f0f0f0]"
        >
          Remove
        </button>
      </div>

      <div className="mt-5 space-y-2">
        <h2 className="text-2xl text-[#f5f5f5]">
          {profile.candidate_name || "Resume candidate"}
        </h2>
        <div className="text-base text-[#cccccc]">
          {profile.current_or_latest_role || "Role not extracted"}
        </div>
        {(experienceLabel || profile.current_or_latest_role) && (
          <div className="text-sm text-[#8f8f8f]">
            {[experienceLabel, profile.current_or_latest_role]
              .filter(Boolean)
              .join(" · ")}
          </div>
        )}
      </div>

      {profile.summary ? (
        <p className="mt-5 text-sm leading-6 text-[#d3d3d3]">{profile.summary}</p>
      ) : null}

      {skills.length > 0 ? (
        <div className="mt-6 flex flex-wrap gap-2">
          {skills.map((skill) => (
            <span
              key={skill}
              className="rounded-full border border-white/15 px-3 py-1 text-xs text-[#cfcfcf]"
            >
              {skill}
            </span>
          ))}
        </div>
      ) : null}

      {profile.strength_areas.length > 0 ? (
        <div className="mt-6 flex flex-wrap gap-2">
          {profile.strength_areas.slice(0, 3).map((area) => (
            <span
              key={area}
              className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300"
            >
              {area}
            </span>
          ))}
        </div>
      ) : null}

      {profile.recommended_interview_topics.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {profile.recommended_interview_topics.slice(0, 3).map((topic) => (
            <span
              key={topic}
              className="rounded-full border border-sky-500/25 px-3 py-1 text-xs text-sky-300"
            >
              {topic}
            </span>
          ))}
        </div>
      ) : null}

      {firstProject ? (
        <div className="mt-6 rounded-sm border border-white/8 bg-[#151515] p-4">
          <div className="font-mono text-xs uppercase tracking-[0.18em] text-[#8d8d8d]">
            Project highlight
          </div>
          <div className="mt-2 text-sm text-[#f0f0f0]">
            {firstProject.name || "Untitled project"}
          </div>
          {firstProject.technologies.length > 0 ? (
            <div className="mt-2 text-xs text-[#9a9a9a]">
              {firstProject.technologies.join(" · ")}
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
