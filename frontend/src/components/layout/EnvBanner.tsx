interface EnvBannerProps {
  message: string;
}

export function EnvBanner({ message }: EnvBannerProps): JSX.Element {
  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-10">
      <section className="bg-card text-card-foreground w-full max-w-2xl rounded-[2rem] border p-8 shadow-shell">
        <p className="text-sm uppercase tracking-[0.32em] text-slate-500">Environment error</p>
        <h1 className="mt-3 text-3xl font-semibold">Frontend configuration is incomplete.</h1>
        <p className="mt-4 text-base leading-7 text-slate-600 dark:text-slate-300">{message}</p>
      </section>
    </main>
  );
}
