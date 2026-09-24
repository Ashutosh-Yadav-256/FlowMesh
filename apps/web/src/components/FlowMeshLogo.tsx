import React from "react";

export function FlowMeshSymbol({
  className = "w-5 h-5",
  color = "currentColor",
}: {
  className?: string;
  color?: string;
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="FlowMesh Symbol"
    >

      <path
        d="M6 18.5V7C6 6.17 6.67 5.5 7.5 5.5H17.5"
        stroke={color}
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <path
        d="M6 12H12.5C13.5 12 14.2 12.5 14.8 13.5L17.5 18.5"
        stroke={color}
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <path
        d="M12 18.5H17.5"
        stroke={color}
        strokeWidth="2.4"
        strokeLinecap="round"
      />

      <circle cx="17.5" cy="5.5" r="1.8" fill={color} />

      <circle cx="12.5" cy="12" r="1.6" fill={color} />

      <circle cx="17.5" cy="18.5" r="1.8" fill={color} />

      <circle cx="6" cy="18.5" r="1.8" fill={color} />
    </svg>
  );
}

export function FlowMeshLogoIcon({
  size = 32,
  className = "",
}: {
  size?: number;
  className?: string;
}) {
  return (
    <div
      style={{ width: size, height: size }}
      className={`rounded-xl bg-[#874436] flex items-center justify-center text-white shadow-sm shrink-0 relative overflow-hidden transition-all duration-200 group-hover:shadow-md group-hover:scale-[1.02] border border-[#A05748]/30 ${className}`}
    >

      <div className="absolute inset-0 bg-gradient-to-br from-white/15 via-transparent to-black/10 pointer-events-none" />
      <FlowMeshSymbol className="w-[21px] h-[21px] text-white relative z-10" />
    </div>
  );
}

export function FlowMeshBrand({
  tagline = "Enterprise Platform",
  version = "v0.1",
}: {
  tagline?: string;
  version?: string;
}) {
  return (
    <div className="flex items-center gap-2.5 group select-none">
      <FlowMeshLogoIcon size={32} />
      <div>
        <span className="font-bold text-base tracking-tight text-[#1B1B1B] flex items-center gap-1.5">
          FlowMesh
          {version && (
            <span className="text-[10px] uppercase font-semibold tracking-wider px-1.5 py-0.5 rounded bg-[#F8EBE8] text-[#874436] border border-[#EED1CB]">
              {version}
            </span>
          )}
        </span>
        {tagline && (
          <span className="text-[11px] text-[#4F4F4F] block -mt-0.5">
            {tagline}
          </span>
        )}
      </div>
    </div>
  );
}
