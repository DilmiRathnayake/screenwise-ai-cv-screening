import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Loader2, RefreshCw, Search as SearchIcon, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';
import { searchApi } from '../../api/endpoints';
import { getErrorMessage } from '../../api/client';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card } from '../../components/ui/card';
import { EmptyState, PageHeader } from '../../components/ui/misc';
import { UserAvatar } from '../../components/ui/avatar';
import { ScoreRing } from '../../components/ui/progress';

export default function SearchPage() {
  const [query, setQuery] = useState('Python React engineer with MySQL');
  const [results, setResults] = useState([]);

  const searchMutation = useMutation({
    mutationFn: () => searchApi.search(query, 12),
    onSuccess: (res) => {
      const hits = res.data?.results || res.data?.hits || res.data || [];
      setResults(Array.isArray(hits) ? hits : []);
      toast.success(`${Array.isArray(hits) ? hits.length : 0} matches`);
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const syncMutation = useMutation({
    mutationFn: searchApi.sync,
    onSuccess: () => toast.success('Vector index synced'),
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  return (
    <div>
      <PageHeader
        title="Semantic search"
        subtitle="Find talent by intent — powered by embeddings and your candidate index."
        actions={
          <Button
            variant="secondary"
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
          >
            {syncMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Sync index
          </Button>
        }
      />

      <Card className="overflow-hidden !p-0">
        <div className="bg-gradient-to-r from-accent/15 via-transparent to-sky-500/10 p-6">
          <div className="flex flex-col gap-3 md:flex-row">
            <div className="relative flex-1">
              <SearchIcon className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && searchMutation.mutate()}
                placeholder="Describe the talent you need…"
                className="h-14 w-full rounded-2xl border border-border bg-background/70 pl-12 pr-4 text-base shadow-inner"
              />
            </div>
            <Button
              size="lg"
              className="h-14 px-8"
              onClick={() => searchMutation.mutate()}
              disabled={searchMutation.isPending || !query.trim()}
            >
              {searchMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              Search
            </Button>
          </div>
        </div>
      </Card>

      <div className="mt-6">
        {!results.length && !searchMutation.isSuccess ? (
          <EmptyState
            icon={Sparkles}
            title="Ask in natural language"
            description='Try “senior healthcare analyst with SQL” or “React engineer who led teams”.'
          />
        ) : !results.length ? (
          <EmptyState title="No matches" description="Sync the index or broaden your query." />
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {results.map((r, i) => {
              const score = Number(r.score ?? r.similarity ?? 0);
              const pct = score <= 1 ? score * 100 : score;
              return (
                <motion.div
                  key={r.candidate_id || r.id || i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                >
                  <Card hover>
                    <div className="flex items-start gap-4">
                      <UserAvatar name={r.full_name || r.name || 'C'} size="lg" />
                      <div className="min-w-0 flex-1">
                        <p className="font-display text-lg font-semibold">
                          {r.full_name || r.name || 'Candidate'}
                        </p>
                        <p className="text-xs text-muted-foreground">{r.email || r.metadata?.email}</p>
                        <div className="mt-2 flex flex-wrap gap-1">
                          {(r.skills || r.metadata?.skills || []).slice(0, 5).map((s) => (
                            <Badge key={s} variant="secondary">
                              {s}
                            </Badge>
                          ))}
                        </div>
                        {r.snippet || r.text ? (
                          <p className="mt-3 line-clamp-3 text-sm text-muted-foreground">
                            {r.snippet || r.text}
                          </p>
                        ) : null}
                      </div>
                      <ScoreRing score={pct} label="Match" size={76} />
                    </div>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
