"use client";

import { useEffect } from "react";
import { AlertOctagon, RotateCcw, Home } from "lucide-react";
import Link from "next/link";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Global application error:", error);
  }, [error]);

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-4">
      <div className="w-16 h-16 bg-rose-50 border border-rose-200 rounded-2xl flex items-center justify-center text-rose-600 mb-6 shadow-sm">
        <AlertOctagon className="w-8 h-8" />
      </div>
      <h1 className="text-2xl font-bold tracking-tight text-zinc-900 mb-2">
        Something went wrong
      </h1>
      <p className="text-sm text-zinc-600 max-w-md mb-6 leading-relaxed">
        An unhandled runtime error occurred in the FlowMesh dashboard.
        {error.message && (
          <span className="block mt-2 font-mono text-xs text-rose-700 bg-rose-50 px-3 py-1.5 rounded border border-rose-100">
            {error.message}
          </span>
        )}
      </p>
      <div className="flex items-center gap-3">
        <button
          onClick={() => reset()}
          className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-semibold text-white bg-zinc-900 hover:bg-zinc-800 rounded-xl transition-all shadow-sm active:scale-[0.98]"
        >
          <RotateCcw className="w-4 h-4" />
          Try Again
        </button>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-semibold text-zinc-700 bg-zinc-100 hover:bg-zinc-200 rounded-xl transition-all"
        >
          <Home className="w-4 h-4" />
          Dashboard
        </Link>
      </div>
    </div>
  );
}
