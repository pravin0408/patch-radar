"use client";

interface Props {
  total: number;
  limit: number;
  offset: number;
  onPageChange: (newOffset: number) => void;
}

export default function Pagination({ total, limit, offset, onPageChange }: Props) {
  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  if (totalPages <= 1) return null;

  const pages: (number | "...")[] = [];
  for (let i = 1; i <= totalPages; i++) {
    if (
      i === 1 ||
      i === totalPages ||
      (i >= currentPage - 2 && i <= currentPage + 2)
    ) {
      pages.push(i);
    } else if (pages[pages.length - 1] !== "...") {
      pages.push("...");
    }
  }

  return (
    <div className="mt-4 flex items-center justify-between text-sm">
      <span className="text-gray-500">
        Showing {Math.min(offset + 1, total)}–{Math.min(offset + limit, total)} of{" "}
        {total} results
      </span>

      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(Math.max(0, offset - limit))}
          disabled={currentPage === 1}
          className="rounded border border-gray-700 bg-gray-900 px-3 py-1.5 text-sm hover:bg-gray-800 disabled:opacity-30"
        >
          Previous
        </button>

        {pages.map((page, idx) =>
          page === "..." ? (
            <span key={`ellipsis-${idx}`} className="px-2 text-gray-500">
              ...
            </span>
          ) : (
            <button
              key={page}
              onClick={() => onPageChange((page - 1) * limit)}
              className={`rounded border px-3 py-1.5 text-sm ${
                page === currentPage
                  ? "border-blue-500 bg-blue-900/40 text-blue-300"
                  : "border-gray-700 bg-gray-900 hover:bg-gray-800"
              }`}
            >
              {page}
            </button>
          )
        )}

        <button
          onClick={() => onPageChange(offset + limit)}
          disabled={currentPage === totalPages}
          className="rounded border border-gray-700 bg-gray-900 px-3 py-1.5 text-sm hover:bg-gray-800 disabled:opacity-30"
        >
          Next
        </button>
      </div>
    </div>
  );
}
