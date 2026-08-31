"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { CheckIcon } from "@/components/Icons";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api/client";
import { screening as t } from "@/messages/ru";
import type { Screening } from "@/lib/api/types";

interface Finding {
  check: string;
  severity: string;
  title: string;
  detail: string;
  path: string;
  line: number;
}

/**
 * Итог автоматической проверки репозитория.
 *
 * Находки ничего не запрещают: у сканеров секретов бывают ложные
 * срабатывания, поэтому решение остаётся за проверяющим.
 */
export function ScreeningPanel({
  submissionId,
  screening,
}: {
  submissionId: number;
  screening: Screening | null;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function recheck() {
    setBusy(true);
    try {
      await api.post(`/api/admin/submissions/${submissionId}/screen/`);
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  const findings = (screening?.findings ?? []) as unknown as Finding[];
  const meta = (screening?.repo_meta ?? {}) as Record<string, unknown>;

  return (
    <section className="mb-7 rounded-card border border-line bg-surface p-5">
      <div className="mb-3.5 flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-[13px] font-bold tracking-wide text-muted-2 uppercase">{t.title}</h3>
        <Button variant="ghost" size="sm" onClick={recheck} disabled={busy}>
          {busy ? t.checking : t.recheck}
        </Button>
      </div>

      {!screening || screening.status === "pending" ? (
        <p className="text-[13.5px] text-muted-2">{t.notRun}</p>
      ) : screening.status === "failed" ? (
        <p className="text-[13.5px] text-amber">
          {t.failed}
          {screening.error ? `: ${screening.error}` : ""}
        </p>
      ) : (
        <>
          {findings.length === 0 ? (
            <p className="flex items-center gap-2 text-[13.5px] text-green-light">
              <CheckIcon size={16} />
              {t.clean}
            </p>
          ) : (
            <ul className="flex list-none flex-col gap-2 p-0">
              {findings.map((finding, index) => (
                <li
                  key={`${finding.check}-${index}`}
                  className={`rounded-lg border px-3.5 py-2.5 ${
                    finding.severity === "high"
                      ? "border-red/25 bg-red/8"
                      : "border-amber/25 bg-amber/8"
                  }`}
                >
                  <div className="flex flex-wrap items-baseline gap-2">
                    <span
                      className={`text-[13.5px] font-semibold ${
                        finding.severity === "high" ? "text-red" : "text-amber"
                      }`}
                    >
                      {finding.title}
                    </span>
                    {finding.path && (
                      <code className="font-mono text-[12px] text-muted-2">
                        {finding.path}
                        {finding.line > 0 ? `:${finding.line}` : ""}
                      </code>
                    )}
                  </div>
                  {finding.detail && (
                    <p className="mt-0.5 font-mono text-[12px] break-all text-muted-2">
                      {finding.detail}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          )}

          <div className="mt-3.5 flex flex-wrap gap-x-4 gap-y-1 border-t border-line pt-3 font-mono text-[12px] text-muted-2">
            <span>
              {screening.files_scanned} {t.filesScanned}
            </span>
            {typeof meta.stars === "number" && (
              <span>
                {meta.stars} {t.stars}
              </span>
            )}
            {typeof meta.size_kb === "number" && (
              <span>
                {meta.size_kb} {t.sizeKb}
              </span>
            )}
            <LiveStatus status={screening.live_status ?? null} />
          </div>

          {findings.length > 0 && (
            <p className="mt-2 text-[12px] text-muted-3">{t.hint}</p>
          )}
        </>
      )}
    </section>
  );
}

function LiveStatus({ status }: { status: number | null }) {
  if (status === null) return <span className="text-amber">{t.liveDead}</span>;
  if (status < 400) return <span className="text-green-light">{`${t.liveOk} (${status})`}</span>;
  return <span className="text-amber">{`${t.liveBad} (${status})`}</span>;
}
