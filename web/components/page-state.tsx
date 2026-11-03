"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";

export function PageLoading({ label }: { label: string }) {
  const [slow, setSlow] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setSlow(true), 5000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div role="status" aria-live="polite" className="mt-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <div aria-hidden="true" className="mt-3 space-y-2">
        <div className="h-3 w-2/3 animate-pulse rounded bg-muted motion-reduce:animate-none" />
        <div className="h-3 w-1/2 animate-pulse rounded bg-muted motion-reduce:animate-none" />
        <div className="h-3 w-3/5 animate-pulse rounded bg-muted motion-reduce:animate-none" />
      </div>
      {slow ? (
        <p className="mt-3 text-sm text-muted-foreground">
          The demo API sleeps when idle; the first load can take up to a minute.
        </p>
      ) : null}
    </div>
  );
}

export function PageError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div role="alert" className="mt-4">
      <h2 className="text-lg font-medium">Couldn&apos;t load this page</h2>
      <p className="mt-2 text-sm">{message}</p>
      <Button variant="outline" onClick={onRetry} className="mt-4">
        Try again
      </Button>
    </div>
  );
}
