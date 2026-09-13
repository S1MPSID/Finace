/** Custom hero stat illustrations — richer than generic line icons. */

export function IconRegulationsIndexed({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" className={className} aria-hidden>
      <defs>
        <linearGradient id="regGrad" x1="8" y1="6" x2="40" y2="42" gradientUnits="userSpaceOnUse">
          <stop stopColor="#4ade80" />
          <stop offset="1" stopColor="#2dd4a8" />
        </linearGradient>
      </defs>
      {/* Document stack */}
      <rect x="12" y="10" width="22" height="28" rx="3" fill="url(#regGrad)" opacity="0.18" stroke="url(#regGrad)" strokeWidth="1.5" />
      <rect x="15" y="7" width="22" height="28" rx="3" fill="#0c1412" stroke="url(#regGrad)" strokeWidth="1.5" />
      <path d="M20 15h12M20 20h12M20 25h8" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round" opacity="0.85" />
      {/* Seal / badge */}
      <circle cx="33" cy="32" r="7" fill="#0c1412" stroke="url(#regGrad)" strokeWidth="1.5" />
      <path d="M30.5 32.2l1.6 1.6 3.4-3.6" stroke="#4ade80" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconClausesEmbedded({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" className={className} aria-hidden>
      <defs>
        <linearGradient id="embGrad" x1="6" y1="8" x2="42" y2="40" gradientUnits="userSpaceOnUse">
          <stop stopColor="#a7f3e0" />
          <stop offset="1" stopColor="#34d399" />
        </linearGradient>
      </defs>
      {/* Vector / embedding constellation */}
      <circle cx="24" cy="24" r="5.5" fill="url(#embGrad)" opacity="0.9" />
      <circle cx="24" cy="24" r="10" stroke="url(#embGrad)" strokeWidth="1.2" opacity="0.45" />
      <circle cx="11" cy="16" r="3" fill="#4ade80" opacity="0.85" />
      <circle cx="37" cy="14" r="2.5" fill="#4ade80" opacity="0.7" />
      <circle cx="38" cy="32" r="3.2" fill="#4ade80" opacity="0.85" />
      <circle cx="12" cy="34" r="2.8" fill="#4ade80" opacity="0.75" />
      <path
        d="M14 17.5L19.5 21.5M29 21.5L35 16M28.5 26.5L36 31M19 27L14.5 32"
        stroke="#4ade80"
        strokeWidth="1.3"
        strokeLinecap="round"
        opacity="0.65"
      />
      {/* Spark marks */}
      <path d="M24 9v3M24 36v3M9 24h3M36 24h3" stroke="#4ade80" strokeWidth="1.4" strokeLinecap="round" opacity="0.5" />
    </svg>
  );
}

export function IconProofsAnchored({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" className={className} aria-hidden>
      <defs>
        <linearGradient id="chainGrad" x1="8" y1="10" x2="40" y2="38" gradientUnits="userSpaceOnUse">
          <stop stopColor="#4ade80" />
          <stop offset="1" stopColor="#14b8a6" />
        </linearGradient>
      </defs>
      {/* Hex / block */}
      <path
        d="M24 8l12 7v14l-12 7-12-7V15l12-7z"
        fill="url(#chainGrad)"
        opacity="0.15"
        stroke="url(#chainGrad)"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      {/* Inner lock */}
      <rect x="19" y="22" width="10" height="8" rx="2" stroke="#4ade80" strokeWidth="1.5" />
      <path d="M21.5 22v-2.5a2.5 2.5 0 015 0V22" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="24" cy="26" r="1.2" fill="#4ade80" />
      {/* Link accents */}
      <path d="M14 18c-2.5 1-4 3.2-4 6s1.5 5 4 6" stroke="#4ade80" strokeWidth="1.4" strokeLinecap="round" opacity="0.55" />
      <path d="M34 18c2.5 1 4 3.2 4 6s-1.5 5-4 6" stroke="#4ade80" strokeWidth="1.4" strokeLinecap="round" opacity="0.55" />
    </svg>
  );
}
