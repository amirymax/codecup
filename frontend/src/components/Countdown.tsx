"use client";

import { useEffect, useState } from "react";

import { contest as t } from "@/messages/ru";
import { pad, splitDuration } from "@/lib/format";

/**
 * Обратный отсчёт до дедлайна.
 *
 * Стартовое значение приходит с сервера в секундах, а не как дата: иначе
 * отсчёт зависел бы от часов на устройстве пользователя, которые могут врать.
 * Дальше уменьшаем локально — расхождение за время сессии несущественно.
 */
export function useCountdown(initialSeconds: number): number {
  const [seconds, setSeconds] = useState(initialSeconds);

  useEffect(() => {
    setSeconds(initialSeconds);
    if (initialSeconds <= 0) return;

    const timer = setInterval(() => {
      setSeconds((current) => (current <= 1 ? 0 : current - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [initialSeconds]);

  return seconds;
}

/** Четыре ячейки отсчёта на странице контеста. */
export function Countdown({ secondsLeft }: { secondsLeft: number }) {
  const seconds = useCountdown(secondsLeft);
  const parts = splitDuration(seconds);

  const cells = [
    { value: pad(parts.days), label: t.days },
    { value: pad(parts.hours), label: t.hours },
    { value: pad(parts.minutes), label: t.minutes },
    { value: pad(parts.seconds), label: t.seconds },
  ];

  return (
    <div className="flex gap-2">
      {cells.map((cell) => (
        <div
          key={cell.label}
          className="flex-1 rounded-lg border border-line-2 bg-surface-3 px-1 py-2 text-center"
        >
          <div className="font-mono text-[17px] font-bold text-text">{cell.value}</div>
          <div className="mt-0.5 text-[10px] text-muted-2">{cell.label}</div>
        </div>
      ))}
    </div>
  );
}

/** Компактная строка «4д 12ч» — для плиток на главной. */
export function CompactCountdown({ secondsLeft }: { secondsLeft: number }) {
  const seconds = useCountdown(secondsLeft);
  const { days, hours, minutes } = splitDuration(seconds);

  if (seconds <= 0) return <>—</>;
  if (days > 0) return <>{`${days}д ${hours}ч`}</>;
  if (hours > 0) return <>{`${hours}ч ${minutes}м`}</>;
  return <>{`${minutes}м`}</>;
}

/** Строка «Осталось: 04д 12ч 33м» в карточке контеста недели. */
export function InlineCountdown({ secondsLeft }: { secondsLeft: number }) {
  const seconds = useCountdown(secondsLeft);
  const { days, hours, minutes } = splitDuration(seconds);

  return <>{`${pad(days)}д ${pad(hours)}ч ${pad(minutes)}м`}</>;
}
