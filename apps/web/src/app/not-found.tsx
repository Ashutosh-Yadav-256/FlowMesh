import Link from "next/link";
import { Search, Home, ArrowLeft, LifeBuoy } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-[75vh] flex flex-col items-center justify-center text-center px-4 py-12">
      <div className="relative mb-6">
        <div className="w-20 h-20 bg-[#FAF8F5] border border-[#D5CABE] rounded-3xl flex items-center justify-center text-[#874436] shadow-sm">
          <Search className="w-10 h-10" />
        </div>
        <span className="absolute -bottom-1 -right-1 px-2 py-0.5 rounded-full bg-[#874436] text-white text-[10px] font-mono font-bold shadow">
          404
        </span>
      </div>

      <span className="text-xs font-semibold tracking-widest text-[#968676] uppercase mb-2">
        HTTP 404 · Page or Resource Missing
      </span>
      <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-[#1B1B1B] mb-3">
        Resource Not Found
      </h1>
      <p className="text-sm text-[#5C5C5C] max-w-md mb-8 leading-relaxed">
        The workflow DAG, connection endpoint, execution run, or page you are attempting to access does not exist or has been archived.
      </p>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-white bg-[#874436] hover:bg-[#6E3529] rounded-xl transition-all shadow-sm active:scale-[0.98]"
        >
          <Home className="w-4 h-4" />
          <span>Back to Overview</span>
        </Link>
        <Link
          href="/help"
          className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold text-[#1B1B1B] bg-[#F0EBE4] hover:bg-[#E5DDD4] rounded-xl border border-[#D5CABE] transition-all"
        >
          <LifeBuoy className="w-4 h-4 text-[#874436]" />
          <span>Help Center</span>
        </Link>
        <a
          href="mailto:ashutosh4tech@gmail.com?subject=FlowMesh%20404%20Broken%20Link"
          className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-medium text-[#5C5C5C] hover:text-[#1B1B1B] transition-colors"
        >
          Report to ashutosh4tech@gmail.com
        </a>
      </div>
    </div>
  );
}
