import { useEffect, useState } from "react";
import {
  Search,
  Image as ImageIcon,
  FileVideo,
  FileText,
  Database,
  SlidersHorizontal,
  Loader2,
  X,
  HardDrive,
  Play,
} from "lucide-react";

const API_BASE_URL = "http://127.0.0.1:8000";

const FILTERS = [
  {
    value: "all",
    label: "All assets",
    icon: Database,
  },
  {
    value: "image",
    label: "Images",
    icon: ImageIcon,
  },
  {
    value: "video",
    label: "Videos",
    icon: FileVideo,
  },
  {
    value: "pdf",
    label: "PDFs",
    icon: FileText,
  },
];

function formatBytes(bytes) {
  if (!bytes || bytes <= 0) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB"];

  const index = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1
  );

  return `${(
    bytes / Math.pow(1024, index)
  ).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatDuration(seconds) {
  if (!seconds || seconds <= 0) {
    return null;
  }

  const totalSeconds = Math.round(seconds);
  const minutes = Math.floor(totalSeconds / 60);
  const remainingSeconds = totalSeconds % 60;

  return `${minutes}:${String(
    remainingSeconds
  ).padStart(2, "0")}`;
}

function getFilterLabel(filter) {
  const selected = FILTERS.find(
    (item) => item.value === filter
  );

  return selected?.label || "All assets";
}

function App() {
  const [query, setQuery] = useState("");

  const [activeFilter, setActiveFilter] =
    useState("all");

  const [results, setResults] = useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [searched, setSearched] =
    useState(false);

  const [selectedAsset, setSelectedAsset] =
    useState(null);

  // =========================================================
  // INDEXING STATE
  // =========================================================

  const [indexing, setIndexing] = useState({
    running: false,
    total: 0,
    processed: 0,
    completed: 0,
    skipped: 0,
    duplicate: 0,
    failed: 0,
    current_file: null,
    current_type: null,
    progress: 0,
  });

  // =========================================================
  // INDEXING STATUS
  // =========================================================

  async function fetchIndexingStatus() {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/indexing/status`
      );

      if (!response.ok) {
        throw new Error(
          "Failed to get indexing status."
        );
      }

      const data = await response.json();

      setIndexing(data);

      return data;
    } catch (err) {
      console.error(
        "Indexing status error:",
        err
      );

      return null;
    }
  }

 async function startIndexing() {
  try {
    setError("");

    const response = await fetch(
      `${API_BASE_URL}/api/indexing/start`,
      {
        method: "POST",
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data?.detail ||
          "Failed to start indexing."
      );
    }

    // Immediately get the initial status
    let status = await fetchIndexingStatus();

    // Keep polling while indexing is running
    while (status?.running) {
      await new Promise((resolve) =>
        setTimeout(resolve, 1000)
      );

      status = await fetchIndexingStatus();
    }

    // Refresh asset library when finished
    await loadAssets(activeFilter);

  } catch (err) {
    console.error(err);

    setError(
      err.message ||
        "Unable to start indexing."
    );
  }
}

  // =========================================================
  // LOAD ASSET LIBRARY
  // =========================================================

  async function loadAssets(
    filter = "all"
  ) {
    try {
      setLoading(true);
      setError("");

      const params =
        new URLSearchParams();

      // Load enough assets for the current
      // assignment dataset.
      params.set("limit", "500");

      if (filter !== "all") {
        params.set(
          "file_type",
          filter
        );
      }

      const response = await fetch(
        `${API_BASE_URL}/api/assets?${params.toString()}`
      );

      if (!response.ok) {
        const body =
          await response
            .json()
            .catch(() => null);

        throw new Error(
          body?.detail ||
            "Failed to load assets."
        );
      }

      const data =
        await response.json();

      const assets = (
        data.results || []
      ).map((asset) => ({
        ...asset,
        score: null,
      }));

      setResults(assets);

      setSearched(false);
    } catch (err) {
      console.error(err);

      setResults([]);

      setError(
        err.message ||
          "Unable to load assets."
      );
    } finally {
      setLoading(false);
    }
  }

  // =========================================================
  // SEMANTIC SEARCH
  // =========================================================

  async function performSearch(
    selectedFilter = activeFilter
  ) {
    const trimmedQuery =
      query.trim();

    if (!trimmedQuery) {
      await loadAssets(
        selectedFilter
      );

      return;
    }

    try {
      setLoading(true);
      setError("");
      setSearched(true);

      const params =
        new URLSearchParams();

      params.set(
        "q",
        trimmedQuery
      );

      params.set(
        "top_k",
        "20"
      );

      if (
        selectedFilter !== "all"
      ) {
        params.set(
          "file_type",
          selectedFilter
        );
      }

      const response = await fetch(
        `${API_BASE_URL}/api/search?${params.toString()}`
      );

      if (!response.ok) {
        const body =
          await response
            .json()
            .catch(() => null);

        throw new Error(
          body?.detail ||
            `Search failed (${response.status})`
        );
      }

      const data =
        await response.json();

      setResults(
        data.results || []
      );
    } catch (err) {
      console.error(err);

      setResults([]);

      setError(
        err.message ||
          "Unable to search the DAM."
      );
    } finally {
      setLoading(false);
    }
  }

  // =========================================================
  // INITIAL LOAD
  // =========================================================

  useEffect(() => {
    loadAssets("all");
    fetchIndexingStatus();
  }, []);

  // =========================================================
  // SEARCH SUBMIT
  // =========================================================

  function handleSearchSubmit(
    event
  ) {
    event.preventDefault();

    performSearch(
      activeFilter
    );
  }

  // =========================================================
  // FILTER CHANGE
  // =========================================================

  function handleFilterChange(
    filter
  ) {
    setActiveFilter(filter);

    if (query.trim()) {
      performSearch(filter);
    } else {
      loadAssets(filter);
    }
  }

  // =========================================================
  // CLEAR SEARCH
  // =========================================================

  function clearSearch() {
    setQuery("");
    setSearched(false);
    setError("");

    loadAssets(activeFilter);
  }

  // =========================================================
  // RENDER
  // =========================================================

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">

      {/* ===================================================
          HEADER
      =================================================== */}

      <header className="border-b border-zinc-800/80 bg-zinc-950/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">

          <div className="flex items-center gap-3">

            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500/15 text-blue-400">
              <Database size={19} />
            </div>

            <div>
              <h1 className="text-sm font-semibold tracking-wide">
                AI DAM
              </h1>

              <p className="text-xs text-zinc-500">
                Digital Asset Manager
              </p>
            </div>

          </div>

          <div className="hidden items-center gap-2 rounded-full border border-zinc-800 bg-zinc-900/70 px-3 py-1.5 text-xs text-zinc-400 sm:flex">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            AI search online
          </div>

        </div>
      </header>

      {/* ===================================================
          MAIN
      =================================================== */}

      <main className="mx-auto max-w-7xl px-6 py-12">

        {/* =================================================
            HERO
        ================================================= */}

        <section className="mx-auto max-w-4xl text-center">

          <div className="mb-3 text-xs font-medium uppercase tracking-[0.25em] text-blue-400">
            Multimodal search
          </div>

          <h2 className="text-4xl font-semibold tracking-tight text-white sm:text-5xl">
            Find anything in your
            <span className="text-blue-400">
              {" "}digital library.
            </span>
          </h2>

          <p className="mx-auto mt-4 max-w-2xl text-sm leading-6 text-zinc-500 sm:text-base">
            Search images, videos and documents
            using natural language. AI understands
            the content of your assets, not just
            their filenames.
          </p>

          {/* =================================================
              SEARCH BAR
          ================================================= */}

          <form
            onSubmit={
              handleSearchSubmit
            }
            className="mt-8"
          >
            <div className="group flex items-center rounded-2xl border border-zinc-800 bg-zinc-900/80 p-2 shadow-2xl shadow-black/20 transition focus-within:border-blue-500/50 focus-within:ring-4 focus-within:ring-blue-500/5">

              <Search
                size={20}
                className="ml-3 shrink-0 text-zinc-500 transition group-focus-within:text-blue-400"
              />

              <input
                value={query}
                onChange={(event) =>
                  setQuery(
                    event.target.value
                  )
                }
                placeholder="Try “modern living room with a grey sofa”"
                className="min-w-0 flex-1 bg-transparent px-4 py-3 text-sm text-white outline-none placeholder:text-zinc-600"
              />

              {query && (
                <button
                  type="button"
                  onClick={
                    clearSearch
                  }
                  className="mr-2 rounded-lg p-2 text-zinc-500 transition hover:bg-zinc-800 hover:text-zinc-300"
                  aria-label="Clear search"
                >
                  <X size={17} />
                </button>
              )}

              <button
                type="submit"
                disabled={
                  loading ||
                  !query.trim()
                }
                className="flex items-center gap-2 rounded-xl bg-blue-500 px-5 py-3 text-sm font-medium text-white transition hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {loading &&
                searched ? (
                  <Loader2
                    size={17}
                    className="animate-spin"
                  />
                ) : (
                  <Search size={17} />
                )}

                Search
              </button>

            </div>
          </form>

        </section>

        {/* =================================================
            INDEXING STATUS
        ================================================= */}

        <section className="mx-auto mt-8 max-w-4xl rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5">

          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

            <div>

              <div className="flex items-center gap-2">

                {indexing.running ? (
                  <Loader2
                    size={16}
                    className="animate-spin text-blue-400"
                  />
                ) : (
                  <Database
                    size={16}
                    className="text-emerald-400"
                  />
                )}

                <h3 className="text-sm font-semibold text-zinc-200">

                  {indexing.running
                    ? "Indexing assets..."
                    : indexing.processed > 0
                    ? "Indexing complete"
                    : "Asset indexing"}

                </h3>

              </div>

              <p className="mt-1 text-xs text-zinc-600">

                {indexing.running
                  ? `${indexing.processed} / ${indexing.total} assets processed`
                  : indexing.processed > 0
                  ? `${indexing.processed} assets processed`
                  : "Keep your library up to date"}

              </p>

            </div>

            {!indexing.running && (
              <button
                type="button"
                onClick={
                  startIndexing
                }
                className="flex items-center justify-center gap-2 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-xs font-medium text-zinc-300 transition hover:bg-zinc-700 hover:text-white"
              >
                <Play size={14} />

                {indexing.processed > 0
                  ? "Run indexing again"
                  : "Run indexing"}
              </button>
            )}

          </div>

          {/* =================================================
              PROGRESS BAR
          ================================================= */}

          <div className="mt-5">

            <div className="mb-2 flex items-center justify-between text-[11px]">

              <span className="text-zinc-600">
                Progress
              </span>

              <span className="font-medium text-zinc-400">
                {indexing.progress}%
              </span>

            </div>

            <div className="h-2 overflow-hidden rounded-full bg-zinc-800">

              <div
                className="h-full rounded-full bg-blue-500 transition-all duration-500"
                style={{
                  width: `${indexing.progress}%`,
                }}
              />

            </div>

          </div>

          {/* =================================================
              CURRENT FILE
          ================================================= */}

          {indexing.running &&
            indexing.current_file && (
              <div className="mt-4 truncate text-xs text-zinc-600">

                Processing:{" "}

                <span className="text-zinc-400">
                  {indexing.current_file}
                </span>

              </div>
            )}

          {/* =================================================
              INDEXING STATS
          ================================================= */}

          <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">

            <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-3">

              <p className="text-[10px] uppercase tracking-wider text-zinc-600">
                Completed
              </p>

              <p className="mt-1 text-lg font-semibold text-zinc-200">
                {indexing.completed}
              </p>

            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-3">

              <p className="text-[10px] uppercase tracking-wider text-zinc-600">
                Skipped
              </p>

              <p className="mt-1 text-lg font-semibold text-zinc-200">
                {indexing.skipped}
              </p>

            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-3">

              <p className="text-[10px] uppercase tracking-wider text-zinc-600">
                Duplicates
              </p>

              <p className="mt-1 text-lg font-semibold text-zinc-200">
                {indexing.duplicate}
              </p>

            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-3">

              <p className="text-[10px] uppercase tracking-wider text-zinc-600">
                Failed
              </p>

              <p className="mt-1 text-lg font-semibold text-zinc-200">
                {indexing.failed}
              </p>

            </div>

          </div>

        </section>

        {/* =================================================
            FILTER BAR
        ================================================= */}

        <section className="mt-12 flex flex-col gap-4 border-b border-zinc-800/80 pb-5 sm:flex-row sm:items-center sm:justify-between">

          <div className="flex items-center gap-2 overflow-x-auto">

            <SlidersHorizontal
              size={16}
              className="mr-1 shrink-0 text-zinc-600"
            />

            {FILTERS.map(
              ({
                value,
                label,
                icon: Icon,
              }) => {

                const active =
                  activeFilter ===
                  value;

                return (
                  <button
                    key={value}
                    type="button"
                    onClick={() =>
                      handleFilterChange(
                        value
                      )
                    }
                    className={`flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium transition ${
                      active
                        ? "bg-zinc-100 text-zinc-950"
                        : "text-zinc-500 hover:bg-zinc-900 hover:text-zinc-300"
                    }`}
                  >

                    <Icon size={15} />

                    {label}

                  </button>
                );
              }
            )}

          </div>

          {!loading && (
            <div className="text-xs text-zinc-600">

              {results.length}{" "}

              {results.length === 1
                ? "asset"
                : "assets"}

            </div>
          )}

        </section>

        {/* =================================================
            ERROR
        ================================================= */}

        {error && (
          <div className="mt-6 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* =================================================
            LOADING
        ================================================= */}

        {loading && (
          <div className="flex min-h-64 items-center justify-center">

            <div className="flex items-center gap-3 text-sm text-zinc-500">

              <Loader2
                size={20}
                className="animate-spin text-blue-400"
              />

              {searched
                ? "Searching your assets..."
                : "Loading your asset library..."}

            </div>

          </div>
        )}

        {/* =================================================
            EMPTY STATE
        ================================================= */}

        {!loading &&
          !searched &&
          results.length === 0 &&
          !error && (
            <div className="flex min-h-80 items-center justify-center">

              <div className="text-center">

                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-zinc-800 bg-zinc-900 text-zinc-600">

                  <Database size={24} />

                </div>

                <h3 className="text-sm font-medium text-zinc-300">
                  No assets found
                </h3>

                <p className="mt-2 text-xs text-zinc-600">

                  There are no{" "}

                  {getFilterLabel(
                    activeFilter
                  ).toLowerCase()}{" "}

                  in the indexed library.

                </p>

              </div>

            </div>
          )}

        {/* =================================================
            NO SEARCH RESULTS
        ================================================= */}

        {!loading &&
          searched &&
          results.length === 0 &&
          !error && (
            <div className="flex min-h-80 items-center justify-center">

              <div className="text-center">

                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-zinc-800 bg-zinc-900 text-zinc-600">

                  <Search size={24} />

                </div>

                <h3 className="text-sm font-medium text-zinc-300">
                  No matching assets
                </h3>

                <p className="mt-2 text-xs text-zinc-600">
                  Try a broader search or
                  another asset type.
                </p>

              </div>

            </div>
          )}

        {/* =================================================
            RESULTS / LIBRARY
        ================================================= */}

        {!loading &&
          results.length > 0 && (
            <section className="mt-8">

              <div className="mb-5 flex items-center justify-between">

                <div>

                  <h3 className="text-sm font-semibold text-zinc-200">

                    {searched
                      ? "Search results"
                      : getFilterLabel(
                          activeFilter
                        )}

                  </h3>

                  <p className="mt-1 text-xs text-zinc-600">

                    {searched
                      ? "Ranked by semantic similarity"
                      : "Browse your indexed assets"}

                  </p>

                </div>

                <div className="hidden items-center gap-2 text-xs text-zinc-600 sm:flex">

                  <HardDrive size={14} />

                  {results.length} displayed

                </div>

              </div>

              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">

                {results.map(
                  (asset) => (
                    <AssetCard
                      key={asset.id}
                      asset={asset}
                      onClick={() =>
                        setSelectedAsset(
                          asset
                        )
                      }
                    />
                  )
                )}

              </div>

            </section>
          )}

      </main>

      {/* ===================================================
          PREVIEW MODAL
      =================================================== */}

      {selectedAsset && (
        <PreviewModal
          asset={selectedAsset}
          onClose={() =>
            setSelectedAsset(null)
          }
        />
      )}

    </div>
  );
}

// ===========================================================
// ASSET CARD
// ===========================================================

function AssetCard({
  asset,
  onClick,
}) {
  const previewUrl =
    `${API_BASE_URL}/api/assets/${asset.id}/preview`;

  const isImage =
    asset.file_type === "image";

  const isVideo =
    asset.file_type === "video";

  const isPdf =
    asset.file_type === "pdf";

  return (
    <button
      type="button"
      onClick={onClick}
      className="group overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/60 text-left transition hover:-translate-y-0.5 hover:border-zinc-700 hover:bg-zinc-900"
    >

      {/* PREVIEW */}

      <div className="relative aspect-[4/3] overflow-hidden bg-zinc-950">

        {/* IMAGE */}

        {isImage && (
          <img
            src={previewUrl}
            alt={asset.filename}
            className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
            loading="lazy"
          />
        )}

        {/* VIDEO */}

        {isVideo && (
          <video
            src={previewUrl}
            muted
            preload="metadata"
            className="h-full w-full object-cover"
          />
        )}

        {/* PDF */}

        {isPdf && (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-zinc-600">

            <FileText size={42} />

            <span className="text-xs uppercase tracking-wider">
              PDF document
            </span>

          </div>
        )}

        {/* SEMANTIC SCORE */}

        {asset.score !== null &&
          asset.score !== undefined && (
            <div className="absolute right-3 top-3 rounded-lg border border-white/10 bg-black/60 px-2 py-1 text-[11px] font-medium text-white backdrop-blur">

              {(asset.score * 100).toFixed(
                1
              )}
              %

            </div>
          )}

        {/* FILE TYPE */}

        <div className="absolute bottom-3 left-3 rounded-lg border border-white/10 bg-black/60 px-2 py-1 text-[10px] font-medium uppercase tracking-wider text-zinc-300 backdrop-blur">

          {asset.file_type}

        </div>

      </div>

      {/* ASSET INFO */}

      <div className="p-4">

        <h4
          className="truncate text-sm font-medium text-zinc-200"
          title={asset.filename}
        >
          {asset.filename}
        </h4>

        <div className="mt-2 flex items-center justify-between gap-2 text-[11px] text-zinc-600">

          <span>
            {formatBytes(
              asset.file_size
            )}
          </span>

          {asset.width &&
            asset.height && (
              <span>
                {asset.width} ×{" "}
                {asset.height}
              </span>
            )}

          {asset.duration && (
            <span>
              {formatDuration(
                asset.duration
              )}
            </span>
          )}

        </div>

      </div>

    </button>
  );
}

// ===========================================================
// PREVIEW MODAL
// ===========================================================

function PreviewModal({
  asset,
  onClose,
}) {
  const previewUrl =
    `${API_BASE_URL}/api/assets/${asset.id}/preview`;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm"
      onClick={onClose}
    >

      <div
        className="relative max-h-[92vh] w-full max-w-5xl overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950 shadow-2xl"
        onClick={(event) =>
          event.stopPropagation()
        }
      >

        {/* CLOSE */}

        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 z-10 flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-black/60 text-zinc-300 backdrop-blur transition hover:bg-black/80"
          aria-label="Close preview"
        >
          <X size={18} />
        </button>

        {/* PREVIEW AREA */}

        <div className="flex max-h-[75vh] min-h-80 items-center justify-center bg-black">

          {/* IMAGE */}

          {asset.file_type ===
            "image" && (
            <img
              src={previewUrl}
              alt={asset.filename}
              className="max-h-[75vh] max-w-full object-contain"
            />
          )}

          {/* VIDEO */}

          {asset.file_type ===
            "video" && (
            <video
              src={previewUrl}
              controls
              autoPlay
              className="max-h-[75vh] max-w-full"
            />
          )}

          {/* PDF */}

          {asset.file_type ===
            "pdf" && (
            <iframe
              src={previewUrl}
              title={asset.filename}
              className="h-[75vh] w-full border-0"
            />
          )}

        </div>

        {/* DETAILS */}

        <div className="border-t border-zinc-800 p-5">

          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">

            <div className="min-w-0">

              <h3 className="truncate text-sm font-semibold text-white">
                {asset.filename}
              </h3>

              <p className="mt-1 text-xs text-zinc-600">

                {asset.file_type.toUpperCase()}
                {" · "}
                {formatBytes(
                  asset.file_size
                )}

              </p>

            </div>

            {/* SEMANTIC SCORE */}

            {asset.score !== null &&
              asset.score !== undefined && (
                <div className="shrink-0 rounded-lg border border-blue-500/20 bg-blue-500/5 px-3 py-2 text-xs text-blue-400">

                  Semantic match:{" "}

                  {(asset.score * 100).toFixed(
                    1
                  )}
                  %

                </div>
              )}

          </div>

          {/* DIMENSIONS */}

          {asset.width &&
            asset.height && (
              <div className="mt-4 text-xs text-zinc-600">

                Resolution:{" "}

                {asset.width} ×{" "}
                {asset.height}

              </div>
            )}

          {/* VIDEO DURATION */}

          {asset.duration && (
            <div className="mt-1 text-xs text-zinc-600">

              Duration:{" "}

              {formatDuration(
                asset.duration
              )}

            </div>
          )}

          {/* EXTRACTED PDF TEXT */}

          {asset.extracted_text && (
            <div className="mt-5">

              <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-600">
                Extracted text
              </p>

              <p className="max-h-32 overflow-y-auto text-xs leading-5 text-zinc-500">
                {asset.extracted_text}
              </p>

            </div>
          )}

          {/* DESCRIPTION */}

          {asset.description && (
            <div className="mt-5">

              <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-600">
                Description
              </p>

              <p className="text-xs leading-5 text-zinc-500">
                {asset.description}
              </p>

            </div>
          )}

        </div>

      </div>

    </div>
  );
}

export default App;